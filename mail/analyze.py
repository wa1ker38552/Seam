import os
import re
import pytz
import spacy
import torch
import mailbox
import pandas as pd
from datetime import datetime, timedelta
from textblob import TextBlob
import torch.nn.functional as F
from openai import OpenAI
from collections import defaultdict, Counter
from flask import request, jsonify, Blueprint
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from language_tool_python import LanguageTool



analyze = Blueprint('analyze', __name__)


openapi = OpenAI(
    base_url="https://api.deepinfra.com/v1/openai",
    api_key="duKc1nUpnQSqS1UrOlBwi6gYUSy3ZMba",
)

UPLOAD_FOLDER = '../uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BLOCKED_CONTACTS = ['reply', 'support', 'notification', 'human resources', 'rewards', 'orders', 'alerts', 'talent', 'recruit', 'info', 'email', 'customer', 'account', 'admission', 'store', 'club', 'subscription', 'news', 'newsletter', 'product', 'updates', 'help', 'assistance', 'jury', 'careers', 'sale', 'response', 'guest', 'user', 'robot', 'confirm', 'automate', 'website', 'notice']

INVITATION_KEYWORDS = {
    'invite', 'invites', 'invited', 'inviting', 'invitation', 'introduce', 'introduction', 'RSVP', 'like to meet', 'attend', 'event', 'participate', 'join', 'meeting', 'conference', 'webinar', 'seminar', 'workshop', 'presentation', 'talk', 'session', 'panel', 'roundtable', 'summit', 'forum', 'gathering', 'get together', 'network', 'networking', 'connect', 'connection', 'meetup', 'meet-up', 'meet up', 'hangout', 'social'
}
STOP_WORDS = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
    'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
    'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up',
    'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should',
    'now', 'hello', 'dear', 'hi', 'hey', 'regards', 'thanks', 'thank', 'best', 'kind', 'warm', 'sincerely', 'yours', 'tomorrow',
    'cheers', 'everything', 'next', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'need', 'please',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'am', 'pm', 'it', 'its', 'it\'s', 'they', 'them', 'their', 'theirs', 'yes',
    'ipad', 'iphone', 'would', 'just', 'i\'m', 'i\'d' , 'i\'ve', 'you\'re', 'i\'ll'
}

def parse_date(date_string):
    date_string = re.sub(r'\s\([A-Z]{2,}\)$', '', date_string)

    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a %d %b %Y %H:%M:%S %z',
        '%d %b %Y %H:%M:%S %z'
    ]
    
    for format_string in formats:
        try:
            return datetime.strptime(date_string, format_string).replace(tzinfo=pytz.UTC)
        except ValueError:
            continue
        
    # If no timezone info, assume UTC
    for format_string in formats:
        try:
            naive_dt = datetime.strptime(date_string, format_string.replace(' %z', ''))
            return naive_dt.replace(tzinfo=pytz.UTC)
        except ValueError:
            continue

    return None

def is_invitation(subject, body):
    try:
        subject = subject.lower()
        body = body.lower()
        return any(keyword in subject or keyword in body for keyword in INVITATION_KEYWORDS)
    except Exception as e:
        print(f"Error in is_invitation: {e}")

def sentiment_analysis(sentiment_scores, relationship_summaries, address, emails):
    sentiment_scores_list = []

    try:
        for email in emails:
            blob = TextBlob(email['Body'])
            polarity = blob.sentiment.polarity
            sentiment_scores_list.append(polarity)
        if sentiment_scores_list:
            sentiment_score = sum(sentiment_scores_list) / len(sentiment_scores_list)
            sentiment_summary = 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'
            sentiment_scores[address] = (sentiment_score)
            relationship_summaries[address] = sentiment_summary

    except Exception as e:
        print(f"Error in sentiment_analysis: {e}")

def organize_by_thread(threads, address, emails):
    try:
        for email in emails:
            subject = email['Subject']
            if 'Re: ' in subject or 'RE: ' in subject:
                threads[address][subject].append(email)
    except Exception as e:
        print(f"Error in organize_by_thread: {e}")

def calculate_user_response_times(threads, user_response_times_by_contact, user_email):
    try:
        for contact, threadz in threads.items():
            for emails in threadz.values():
                for i in range(1, len(emails)):
                    current_email = emails[i]
                    previous_email = emails[i - 1]
                    
                    if user_email in current_email['From'] and user_email not in previous_email['From']:
                        current_date = parse_date(current_email['Date'])
                        previous_date = parse_date(previous_email['Date'])
                        if current_date and previous_date:
                            response_time = (current_date - previous_date).seconds
                            response_time /= 3600
                            user_response_times_by_contact[contact].append(response_time)

        for contact, times in user_response_times_by_contact.items():
            if times:
                user_response_times_by_contact[contact] = sum(times) / len(times)

    except Exception as e:
        print(f"Error in calculating response times: {e}")

def calculate_contact_response_times(threads, contact_response_times, user_email):
    try:
        for contact, threadz in threads.items():
            for emails in threadz.values():
                for i in range(1, len(emails)):
                    current_email = emails[i]
                    previous_email = emails[i - 1]
                    
                    if user_email in previous_email['From'] and user_email not in current_email['From']:
                        current_date = parse_date(current_email['Date'])
                        previous_date = parse_date(previous_email['Date'])
                        if current_date and previous_date:
                            response_time = (current_date - previous_date).seconds
                            response_time /= 3600
                            contact_response_times[contact].append(response_time)

        for contact, times in contact_response_times.items():
            if times:
                contact_response_times[contact] = sum(times) / len(times)

    except Exception as e:
        print(f"Error in calculating response times: {e}")

def calculate_thread_length(threads, thread_lengths):
    try:
        for contact, threadz in threads.items():
            for emails in threadz.values():
                thread_lengths[contact] += 1 + len(emails)
            thread_lengths[contact] /= len(threadz)
    except Exception as e:
        print(f"Error in calculating thread length: {e}")

def calculate_follow_up_rate(follow_up, address, emails, user_email):
    try:
        emails_from_contact_count = sum(1 for email in emails if address in email['From'])
        follow_up_count = 0

        for i in range(1, len(emails)):
            current_email = emails[i]
            previous_email = emails[i - 1]

            if user_email in current_email['From'] and user_email not in previous_email['From']:
                follow_up_count += 1

        follow_up[address] = (follow_up_count / emails_from_contact_count * 100) if emails_from_contact_count > 0 else 0
        
    except Exception as e:
        print(f"Error in calculating follow up rate: {e}")

def calculate_interaction_frequency(monthly_interactions, interactions_each_month, address, emails):
    try:
        for email in emails:
            date_str = email["Date"]
            try:
                date = parse_date(date_str)
                if date:
                    month = date.strftime('%m')
                    month = int(month.lstrip('0'))
                    interactions_each_month[address][month] += 1
            except ValueError as e:
                print(f"Error parsing date in interaction_frequency: {e}")

        for email_address, months in interactions_each_month.items():
            total_sum = 0
            non_zero_months = 0
            for month in months:
                total_sum += month
                if month > 0:
                    non_zero_months += 1
            monthly_interactions[email_address] = total_sum / non_zero_months if non_zero_months > 0 else 0

    except Exception as e:
        print(f"Error in calculating interaction frequency: {e}")

def user_initiated(user_initiation, address, emails, user_email):
    if not emails:
        return
    try:
        user_initiation[address] = user_email in emails[0]['From']
    except Exception as e:
        print(f"Error in determining user initiation: {e}")

def calculate_personalization_score(nlp, personalization_scores, address, emails, user_email):
    try:
        for email in emails:
            if user_email in email['From']:
                doc = nlp(email['Body'])
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        personalization_scores[address] += 1
    except Exception as e:
        print(f"Error in calculating personalization score: {e}")
        
def calculate_emails_per_day(emails_per_day, average_emails_per_day, email_meta, user_email):
    try:
        today = datetime.now(pytz.UTC).date()
        start_date = today - timedelta(days=105)
        emails_per_day.clear()  # Clear the dictionary instead of slicing

        # Fill in missing days with 0 emails
        for i in range(106):
            day = start_date + timedelta(days=i)
            emails_per_day[day] = 0  # Use the day as a key
        
        for emails in email_meta.values():
            for email in emails:
                if user_email in email['From']:
                    email_date = parse_date(email['Date']).date()
                    if start_date <= email_date <= today:
                        index = (email_date - start_date).days
                        emails_per_day[start_date + timedelta(days=index)] += 1  # Increment the count for that day

        # Prepare the output for emails_per_day as a string of counts
        emails_per_day[0] = ', '.join(str(count) for count in emails_per_day.values())  # Ensure this is a string
        
        total_emails = sum(emails_per_day.values())  # Ensure all values are integers
        average_emails_per_day[0] = total_emails / 105 if total_emails > 0 else 0

    except Exception as e:
        print(f"Error in calculating emails per day: {e}")
        
def identify_no_reply_contacts(threads, user_email, no_reply_contacts):
    for contact, threadz in threads.items():
        for subject, emails in threadz.items():
            last_email = emails[-1]
            last_email_date = parse_date(last_email['Date'])
            if user_email in last_email['From']:
                if last_email_date and (datetime.now(pytz.UTC) - last_email_date).days > 7:
                    no_reply_contacts[contact] = (datetime.now(pytz.UTC) - last_email_date).days

def identify_forgot_to_reply_contacts(threads, user_email, forgot_to_reply_contacts):
    for contact, threadz in threads.items():
        for subject, emails in threadz.items():
            last_email = emails[-1]
            last_email_date = parse_date(last_email['Date'])
            if user_email not in last_email['From']:
                if last_email_date and (datetime.now(pytz.UTC) - last_email_date).days > 1:
                    forgot_to_reply_contacts[contact] = (datetime.now(pytz.UTC) - last_email_date).days

def identify_promised_follow_ups(emails, user_email, promised_follow_ups):
    commitment_phrases = ["i'll get back to you", "let me check", "i'll update you", "i will follow up"]
    for email in emails:
        if user_email in email['From']:
            body = email['Body'].lower()
            if any(phrase in body for phrase in commitment_phrases):
                contact = extract_contact(email)
                promised_follow_ups.add(contact)

def identify_suggested_meetings(emails, user_email, suggested_meetings):
    meeting_phrases = ["let's discuss", "we should meet", "schedule a call", "arrange a meeting", "call me", "meet up"]
    for email in emails:
        if user_email in email['From']:
            body = email['Body'].lower()
            if any(phrase in body for phrase in meeting_phrases):
                contact = extract_contact(email)
                suggested_meetings.add(contact)

def extract_contact(email):
    to_addresses = email['To']
    addresses = re.findall(r'[\w\.-]+@[\w\.-]+', to_addresses)
    for address in addresses:
        if address != user_email:
            return address
    return None

def calculate_priority_score(recency_score, engagement_score, potential_value_score, urgency_score):
    recency_weight = 0.3
    engagement_weight = 0.2
    potential_value_weight = 0.4
    urgency_weight = 0.1
    return (recency_weight * recency_score +
            engagement_weight * engagement_score +
            potential_value_weight * potential_value_score +
            urgency_weight * urgency_score)

def calculate_recency_score(last_contact_date):
    days_since_last_contact = (datetime.now(pytz.UTC) - last_contact_date).days
    return max(0, 1 - days_since_last_contact / 30)

def calculate_engagement_score(interaction_count):
    return min(1, interaction_count / 10)

def estimate_potential_value(contact):
    # Placeholder function - in real implementation, fetch data based on contact's email domain
    # For demonstration, assign a random value between 0.5 and 1
    return 0.75

def calculate_urgency_score(email_bodies):
    urgency_indicators = ["urgent", "asap", "important", "priority"]
    for body in email_bodies:
        if any(indicator in body.lower() for indicator in urgency_indicators):
            return 1
    return 0

def find_keywords(keywords, address, emails):
    try:
        all_messages = " ".join([email['Body'] for email in emails])
        all_messages = all_messages.lower()

        punctuation_marks = ['.', ',', '!', '?', ':', ';', '\n', '\t', '\r', '(', ')', '[', ']', '{', '}', '<', '>', '"', '—', '-', '_', '/', '\\', '|', '@', '#', '$', '%', '^', '&', '*', '+', '=', '~', '`']
        for marks in punctuation_marks:
            all_messages = all_messages.replace(marks, '')

        all_messages = all_messages.split()
        filtered_messages = [word for word in all_messages if word not in STOP_WORDS]
        word_counts = Counter(filtered_messages)
        most_common_words = word_counts.most_common(5)
        top_words = ', '.join([word for word, count in most_common_words])
        keywords[address] = top_words
        
    except Exception as e:
        print(f"Error in finding keywords: {e}")

def assign_tier(contact, last_email_dates, relationship_summaries):
    current_date = pd.Timestamp(datetime.now()).tz_localize('UTC')
    six_months_ago = current_date - pd.DateOffset(months=6)
    last_contact_str = last_email_dates.get(contact, None)
    sentiment = relationship_summaries.get(contact, 'N/A')
    
    if not last_contact_str or sentiment == 'N/A':
        return 0

    try:
        last_contact = pd.to_datetime(last_contact_str, utc=True)
    except Exception as e:
        print(f"Error parsing date for contact {contact}: {e}")
        return 0

    active = six_months_ago <= last_contact
    
    if active and sentiment == 'positive':
        return 1
    elif not active and sentiment == 'positive':
        return 2
    elif active and sentiment == 'neutral':
        return 3
    else:
        return 4
    
invitation_counts = [0] * 12
current_year = datetime.now().year
current_month = datetime.now().month

def calculate_yearly_invitations(email_meta, user_email):
    total_invitations = 0
    current_date = datetime.now(pytz.UTC)
    one_year_ago = current_date - timedelta(days=365)
    
    for emails in email_meta.values():
        for email in emails:
            if user_email not in email['From']:  # Count invitations received, not sent
                date = parse_date(email['Date'])
                if date and one_year_ago <= date <= current_date:
                    if is_invitation(email['Subject'], email['Body']):
                        total_invitations += 1
    
    return total_invitations

def calculate_recent_sentiment(email_meta, user_email):
    positive_count = 0
    total_count = 0
    current_date = datetime.now(pytz.UTC)
    one_month_ago = current_date - timedelta(days=30)
    
    for emails in email_meta.values():
        for email in emails:
            if user_email in email['From']:  # Only analyze sent emails
                date = parse_date(email['Date'])
                if date and one_month_ago <= date <= current_date:
                    blob = TextBlob(email['Body'])
                    sentiment = blob.sentiment.polarity
                    if sentiment > 0:
                        positive_count += 1
                    total_count += 1
    
    if total_count > 0:
        positive_percentage = (positive_count / total_count) * 100
    else:
        positive_percentage = 0
    
    return round(positive_percentage, 2)

def llama_classification(email, address, user_email, completions):
    if user_email not in email["From"]:
        try:
          response = openapi.chat.completions.create(
              model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
              max_tokens=4096,
              messages=[
                  {
                      "role": "system",
                      "content":
                      """
                      Analyze the following email sent by a contact to a user.
                      Determine if the email requires a follow-up response from the user.
                      If no response is needed, include 'NO' in all caps in your reply.
                      If a response is expected, provide a brief summary of the email's content.
                      When writing the summary, write as if you were an assistant directly reminding the user to respond.
                      """,
                  },
                  {"role": "user", "content": email["Body"]},
              ],
          )

          completions[address] = response.model_dump()['choices'][0]['message']['content']
 
        except Exception as e:
            print(f"Error in llama_classification: {e}")
    else:
        try:
          response = openapi.chat.completions.create(
              model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
              max_tokens=4096,
              messages=[
                  {
                      "role": "system",
                      "content":
                      """
                      Analyze the following email sent by a user to a contact.
                      Determine if the email requires a follow-up response from the contact.
                      If no response is needed, include 'NO' in all caps in your reply.
                      If a response is expected, provide a brief summary of the email's content.
                      When writing the summary, write as if you were an assistant directly reminding the user that the client hasn't responded to their email yet.
                      """
                  },
                  {"role": "user", "content": email["Body"]},
              ],
          )

          completions[address] = response.model_dump()['choices'][0]['message']['content']

        except Exception as e:
            print(f"Error in llama_classification: {e}")

def process_message(message, email_meta, email_content, contact_names, interaction_counts, invitation_counts, first_email_dates, last_email_dates, user_email):
    try:
        contacts = []

        if message['From']:
            from_address = message['From']
        else:
            from_address = ''

        if message['To']:
            to_addresses = message['To']
        else:
            to_addresses = ''

        if message['Date']:
            date_str = message['Date']
            date = parse_date(date_str)
        else:
            date_str = ''
            date = None

        if message['Subject']:
            subject = message['Subject']
        else:
            subject = ''

        if message['Body']:
            body = message['Body']
        else:
            body = ''

        if user_email not in from_address: # if the owner is not the sender, add the sender to the contact list
            split_address = from_address.split('<')
            if len(split_address) > 1: 
                name = split_address[0].strip()
                address = split_address[1].replace('>', '').strip()
                contacts.append(address)
                if address not in contact_names:
                    contact_names[address] = name
        elif user_email in from_address:
            split_to_addresses = to_addresses.split(',')
            if len(split_to_addresses) > 1: # multiple recipients
                for address in split_to_addresses:
                    if user_email not in address:
                        address = address.strip()
                        contacts.append(address)
            else:
                split_address = to_addresses.split('<')
                if len(split_address) > 1:
                    name = split_address[0].strip()
                    address = split_address[1].replace('>', '').strip()
                    if user_email not in address: # handle case where owner is the sender and recipient
                        contacts.append(address)
                        if address not in contact_names:
                            contact_names[address] = name
        # invitation_counts = [0] * 12  # Initialize invitation_counts for the current year
        for address in contacts:
            email_meta[address].append({
                'From': from_address,
                'To': to_addresses,
                'Subject': subject,
                'Date': date_str,
                'Body': body
            })

            body = body.replace('\r\n', ' ')
            body = body.replace('\n', ' ')
            email_content[address].append(body)

            interaction_counts[address] += 1

            if address in from_address and is_invitation(subject, body) and date and date.year == current_year:
                email_month = date.month - 1  # Get month (0-indexed)
                if email_month < current_month:
                    invitation_counts[email_month] += 1  # Increment the invitation count for the month

            if date:
                if first_email_dates[address] is None or date < first_email_dates[address]:
                    first_email_dates[address] = date
                if last_email_dates[address] is None or date > last_email_dates[address]:
                    last_email_dates[address] = date
        
    except Exception as e:
        print(f"Error processing message: {e}")
    # After processing all messages, print the invitation counts
    invitation_counts[0] = ', '.join(str(count) if i < current_month else '0' for i, count in enumerate(invitation_counts))
  
def generate_tabular_data(email_meta, email_content, contact_names, interaction_counts, invitation_counts, first_email_dates, last_email_dates, sentiment_scores, relationship_summaries, monthly_interactions, user_initiation, personalization_scores, follow_up_rates, keywords, contact_response_times, user_response_times_by_contact, user_email, thread_lengths, inbox_id, writing_level_data, emails_per_day, average_emails_per_day, quarterly_engagements, completions, last_email_date, last_email_subject, last_email_body):
    data = []
    
    for contact in email_content:
        # Ensure emails_per_day is a dictionary
        # if not isinstance(emails_per_day[contact], dict):
        #     print(f"Warning: emails_per_day for {contact} is not a dictionary. It is: {emails_per_day[contact]}")
        #     emails_per_day[contact] = {}  # Initialize as an empty dictionary if it's not

        data.append({
            'tier': assign_tier(contact, last_email_dates, relationship_summaries),
            "contact": contact_names[contact] if contact_names[contact] else 'N/A',
            "email_address": contact if contact else 'N/A',
            "emails_exchanged": interaction_counts[contact],
            # 'invitations_received': int(invitation_counts[contact]) if invitation_counts[contact] else 0,
            'months_known': round(((last_email_dates.get(contact) - first_email_dates.get(contact)).days) / 30, 2) if first_email_dates.get(contact) and last_email_dates.get(contact) else 0,
            "first_interaction_date": first_email_dates[contact].strftime('%Y-%m-%d') if first_email_dates[contact] else None,
            "last_interaction_date": last_email_dates[contact].strftime('%Y-%m-%d') if last_email_dates[contact] else None,
            "sentiment_score": sentiment_scores[contact],
            "relationship_summary": relationship_summaries[contact],
            "monthly_interactions": int(monthly_interactions[contact]),
            "user_initiated": user_initiation[contact],
            "personalization_score": int(personalization_scores[contact]),
            "follow_up_rate": int(follow_up_rates[contact]) if follow_up_rates[contact] else 0,
            "keywords": keywords[contact],
            "contact_avg_response_time_hours": round(contact_response_times.get(contact, 0), 2),
            "user_avg_response_time_hours": round(user_response_times_by_contact.get(contact, 0), 2),
            "thread_length": int(thread_lengths[contact]) if thread_lengths[contact] else 0, 
            # "emails_per_day": {date.strftime('%Y-%m-%d'): count for date, count in emails_per_day[contact].items()}, 
            "average_emails_per_day": int(average_emails_per_day[0]),  # Convert to int
            "inbox_id": inbox_id,
            "completions": completions[contact] if completions[contact] else 'N/A',
            "last_email_date": last_email_date[contact],
            "last_email_subject": last_email_subject[contact],
            "last_email_body": last_email_body[contact]
        })

    if not data:
        print("No data to insert into Supabase.")
        return


    # Calculate yearly invitations and recent sentiment
    yearly_invitations = calculate_yearly_invitations(email_meta, user_email)
    recent_sentiment_percentage = calculate_recent_sentiment(email_meta, user_email)

    # Insert or update the inbox_metrics table
    metrics_data = {
        "inbox_id": inbox_id,
        "Q1_engagements": quarterly_engagements['Q1_engagements'],
        "Q2_engagements": quarterly_engagements['Q2_engagements'],
        "Q3_engagements": quarterly_engagements['Q3_engagements'],
        "Q4_engagements": quarterly_engagements['Q4_engagements'],
        "writing_level": int(sum(writing_level_data.values()) / len(writing_level_data) if writing_level_data else 0),
        "emails_per_day": emails_per_day[0],
        "invitations_per_year": invitation_counts[0],
        "last_yearly_invitations_received": yearly_invitations,
        "recent_positive_sentiment_percentage": recent_sentiment_percentage
    }

        
def calculate_quarterly_engagements(email_meta, quarterly_engagements, user_email):
    try:
        for emails in email_meta.values():
            for email in emails:
                if user_email in email['From']:
                    date = parse_date(email['Date'])
                    if date:
                        month = date.month
                        if month in [1, 2, 3]:  # Q1
                            quarterly_engagements['Q1_engagements'] += 1
                        elif month in [4, 5, 6]:  # Q2
                            quarterly_engagements['Q2_engagements'] += 1
                        elif month in [7, 8, 9]:  # Q3
                            quarterly_engagements['Q3_engagements'] += 1
                        elif month in [10, 11, 12]:  # Q4
                            quarterly_engagements['Q4_engagements'] += 1
    except Exception as e:
        print(f"Error in calculating quarterly engagements: {e}")

def analyze_writing_level(email_content):
    try:
        # Initialize LanguageTool for grammar checking
        language_tool = LanguageTool('en-US')
        
        total_words = 0
        total_errors = 0
        percentages = []

        for content in email_content:
            # Remove email signatures and quoted text
            clean_content = re.sub(r'(\n--|^>).*', '', content, flags=re.MULTILINE | re.DOTALL)
            
            # Count words
            words = re.findall(r'\b\w+\b', clean_content.lower())
            total_words += len(words)

            # Check grammar
            grammar_errors = language_tool.check(clean_content)
            total_errors += len(grammar_errors)

            # Calculate grammatical correctness percentage for this email
            if total_words > 0:
                correctness_percentage = ((total_words - len(grammar_errors)) / total_words) * 100
                percentages.append(correctness_percentage)

        # Calculate average percentage
        if percentages:
            average_correctness = sum(percentages) / len(percentages)
            return int(average_correctness)  # Return as an integer
        else:
            return 0  # If no emails, return 0

    except Exception as e:
        print(f"Error in analyzing writing level: {e}")
        return 0  # Return 0 in case of an error

def main(data, user_email, nlp, inbox_id):
    try:
        keywords = defaultdict(list)
        email_meta = defaultdict(list)
        email_content = defaultdict(list)
        contact_names = defaultdict(str)
        sentiment_scores = defaultdict(str)   
        relationship_summaries = defaultdict(str)
        personalization_scores = defaultdict(int)
        user_response_times_by_contact = defaultdict(list)
        contact_response_times = defaultdict(list)
        monthly_interactions = defaultdict(int)
        interaction_counts = defaultdict(int)
        invitation_counts = defaultdict(int)
        follow_up_rates = defaultdict(int)
        thread_lengths = defaultdict(int)
        user_initiation = defaultdict(bool)
        last_email_dates = defaultdict(lambda: None)
        first_email_dates = defaultdict(lambda: None)
        threads = defaultdict(lambda: defaultdict(list))
        interactions_each_month = defaultdict(lambda: [0] * 13)
        writing_level_data = defaultdict(int)  # Change to store average correctness percentage
        emails_per_day = defaultdict(int)
        completions = defaultdict(str)
        last_email_date = defaultdict(str)
        last_email_subject = defaultdict(str)
        last_email_body = defaultdict(str)
        average_emails_per_day = [0]
        count = 0

        no_reply_contacts = {}
        forgot_to_reply_contacts = {}
        promised_follow_ups = set()
        suggested_meetings = set()
        all_emails = []
        
        quarterly_engagements = {
            'Q1_engagements': 0,
            'Q2_engagements': 0,
            'Q3_engagements': 0,
            'Q4_engagements': 0
        }

        # emails_replied = defaultdict(int)
        # emails_ignored = defaultdict(int)
        # emails_pending = defaultdict(int)
        all_emails = []
        for entry in data: 
            process_message(entry, email_meta, email_content, contact_names, interaction_counts, invitation_counts, first_email_dates, last_email_dates, user_email)

        for address, emails in email_meta.items():
            count += 1
            print(f'Processing contact {count} of {len(email_meta)}')
            sentiment_analysis(sentiment_scores, relationship_summaries, address, emails)
            calculate_interaction_frequency(monthly_interactions, interactions_each_month, address, emails)
            calculate_personalization_score(nlp, personalization_scores, address, emails, user_email)
            find_keywords(keywords, address, emails)

            valid_emails = [email for email in emails if parse_date(email['Date'])]
            sorted_emails = sorted(valid_emails, key=lambda x: parse_date(x['Date']))
            if sorted_emails:
              last_email = sorted_emails[-1]
            
            last_email_date[address] = last_email['Date']
            last_email_subject[address] = last_email['Subject']
            last_email_body[address] = last_email['Body']

            if not last_email['Body'] or 'Forwarded message' in last_email['Body']:
                continue

            llama_classification(last_email, address, user_email, completions)
            organize_by_thread(threads, address, sorted_emails)
            calculate_follow_up_rate(follow_up_rates, address, sorted_emails, user_email)
            user_initiated(user_initiation, address, sorted_emails, user_email)

            # Analyze writing level for user emails
            # user_emails = [email['Body'] for email in sorted_emails if user_email in email['From']]
            all_emails.extend(email['Body'] for email in sorted_emails if user_email in email['From'])
        
        user_emails_to_analyze = all_emails[-30:]
        writing_analysis = analyze_writing_level(user_emails_to_analyze)
        writing_level_data[address] = writing_analysis  # Store average correctness percentage
        
        calculate_user_response_times(threads, user_response_times_by_contact, user_email)
        calculate_contact_response_times(threads, contact_response_times, user_email)
        calculate_thread_length(threads, thread_lengths)
        calculate_emails_per_day(emails_per_day, average_emails_per_day, email_meta, user_email)
        calculate_quarterly_engagements(email_meta, quarterly_engagements, user_email)
        
        generate_tabular_data(
            email_meta, email_content, contact_names, interaction_counts, invitation_counts,
            first_email_dates, last_email_dates, sentiment_scores, relationship_summaries, monthly_interactions, user_initiation,
            personalization_scores, follow_up_rates, keywords, contact_response_times, user_response_times_by_contact, user_email, thread_lengths, inbox_id,
            writing_level_data, emails_per_day, average_emails_per_day, quarterly_engagements, completions, last_email_date, last_email_subject, last_email_body
        )

    except Exception as e:
        print(f'An error occurred in main(): {e}')

def clean_headers(msg):
    try:
        allowed_headers = ['To', 'From', 'Subject', 'Date']
        cleaned_msg = {key: str(msg.get(key)) for key in allowed_headers if msg.get(key)}
        return cleaned_msg
    except Exception as e:
        print(f'Error cleaning headers: {e}')

def predict_spam(text, model, tokenizer):
    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=-1)
    predicted_class = torch.argmax(probabilities, dim=-1).item()
    labels = ['not spam', 'spam']
    predicted_label = labels[predicted_class]
    
    return predicted_label

def clean_payload(payload, forwarded_message_pattern, on_wrote_pattern, from_pattern):
    try:
        if re.match(forwarded_message_pattern, payload, re.DOTALL):
            payload = payload
        elif re.match(on_wrote_pattern, payload, re.DOTALL):
            match = re.match(on_wrote_pattern, payload, re.DOTALL)
            if match:
                payload = match.group(1)
        
        elif re.match(from_pattern, payload, re.DOTALL):
            match = re.match(from_pattern, payload, re.DOTALL)
            if match:
                payload = match.group(1)
        
        return payload

    except Exception as e:
        print(f'Error cleaning payload: {e}')

def extract_mbox(input_mbox, model, tokenizer):

    on_wrote_pattern = r'^(.*?)(On .*? wrote:)'
    from_pattern = r'^(.*?)(?=From:.*<[^>]+>)'
    forwarded_message_pattern = r'^-{10,} Forwarded message -{10,}$'

    try:
        processed_messages = []
        in_mbox = mailbox.mbox(input_mbox)
        count = 0
        
        for message in in_mbox:
            if count == 100: 
                break
            count += 1
            print(f"Extracting message #{count} of {len(in_mbox)}")

            from_address = str(message.get('From'))
            if any(word in from_address.lower() for word in BLOCKED_CONTACTS):
                continue

            to_address = str(message.get('To'))
            if any(word in to_address.lower() for word in BLOCKED_CONTACTS):
                continue
            
            if message.is_multipart(): 
                
                for part in message.walk():
                    if part.get_content_type() != 'text/plain':
                        continue

                    payload = str(part.get_payload(decode=True).decode('utf-8', errors='replace'))
                    if not payload.strip():
                        continue
                
                    if 'unsubscribe' in payload.lower():
                        continue
                    
                    payload = clean_payload(payload, forwarded_message_pattern, on_wrote_pattern, from_pattern)
                    try:
                        result = predict_spam(payload, model, tokenizer)
                        if result == 'spam':
                            continue
                    except Exception as e:
                        continue
            
                    email_dict = {
                        'From': str(message.get('From')),
                        'To': str(message.get('To')),
                        'Subject': str(message.get('Subject')),
                        'Date': str(message.get('Date')),
                        'Body': payload
                    }
                    
                    processed_messages.append(email_dict)
                    break

            else:
                if message.get_content_type() != 'text/plain':
                    continue

                email_dict = clean_headers(message)
                payload = str(message.get_payload(decode=True).decode('utf-8', errors='replace'))
                if not payload.strip():
                    continue

                if 'unsubscribe' in payload.lower():
                    continue
                
                payload = clean_payload(payload, forwarded_message_pattern, on_wrote_pattern, from_pattern)

                try:
                    result = predict_spam(payload, model, tokenizer)
                    if result == 'spam':
                        continue
                except Exception as e:
                    continue
                
                email_dict['Body'] = payload
                processed_messages.append(email_dict)
            
        return processed_messages
    
    except Exception as e:
        print(f'Error extracting mbox: {e}')

inbox_id = ''
# nlp = spacy.load("en_core_web_sm")
model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
print('Checking if is spam')
is_spam = predict_spam('join for a chance to win $500', model, tokenizer)
print(is_spam)
# data = extract_mbox('All mail Including Spam and Trash-001.mbox', model, tokenizer)
# main(data, 'thomas@thomasatamian.co', nlp, inbox_id)
    