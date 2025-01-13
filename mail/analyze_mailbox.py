from transformers import AutoModelForSequenceClassification, AutoTokenizer
from deepinfra import prompt_deepinfra
from analyze_spam import predict_spam
from mailboxreader import MboxReader
from collections import defaultdict
from email.policy import default
from bs4 import BeautifulSoup
from threading import Thread
from groq import Groq
import math
import email
import time
import json
import re
import os


def parse_mail(message):
    return {
        "sender": message.get("From"),
        "receiver": message.get("To"),
        "subject": message.get("Subject"),
        "date": message.get("Date"),
        "body": extract_body(message)
    }

def extract_body(message):
    if message.is_multipart():
        for part in message.iter_parts():
            if part.get_content_type() == "text/plain":
                return part.get_content().strip()
            elif part.get_content_type() == "text/html":
                return part.get_content().strip()
    else:
        return message.get_content().strip()
    return None

def prompt_groq(client, instructions, query):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a bot designed to give short quick and concise information. Never add formatting to your responses and return a direct answer."
            },
            {
                "role": "system",
                "content": instructions
            },
            {
                "role": "user",
                "content": query,
            }
        ],
        model="llama3-8b-8192"
    )
    return chat_completion.choices[0].message.content

def run_iteration(message, client):
    if message['body']:
        soup = BeautifulSoup(message['body'], 'lxml')
        content = soup.get_text()
        content = re.sub(r'\s+', ' ', content).strip()
    else:
        content = ''
    used_subject = True if len(content) > 6000 else False
    content = message['subject'] if len(content) > 6000 else content

    if not content:
        used_subject = True
        content = message['subject']

    sender = message['sender'].split(' <')[1][:-1] if '<' in message['sender'] else message['sender']

    spam_score = -5 if predict_spam(content, model, tokenizer) == 'spam' else 0
    exchange_score = math.log10((email_exchanges[sender] if sender in email_exchanges else 0/AVERAGE_EXCHANGES)+1)*5
    sender_score = -20 if ('no' in message['sender'].lower() and 'reply' in message['sender'].lower()) or 'update' in message['sender'].lower() or 'info' in message['sender'].lower() or 'notification' in message['sender'].lower() or 'support' in message['sender'].lower() else 0
    subject_score = int(prompt_deepinfra('Given the subject line of an email, return whether or not the content of this email are important. Give it less score if it seems like the email was a automated response. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', message['subject']))
    timing_score = int(prompt_deepinfra('Given the contents of an email, determine whether or not it is urgent. For example a 0 would be not urgent and requiring attention immediately. However, a 10 would be something that is extremely important and must be immediately attended to. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
    content_score = int(prompt_deepinfra('Given the contents of an email, evaluate how relevant and important this email is to the person at hand. 0 means not important at all, something like a notification message or spam message and 10 means very important, something that might be personal or requiring the reciever to do something. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
    personalization_score = int(prompt_deepinfra('Given the contents of an email, rate how personal it is. A personal email will be addressing the recipient by name and would NOT be automated or mass sent. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
    action_score = int(prompt_deepinfra('Given the contents of an email, rate whether or not it requires the recipient to do something. For example, a 0 would be a informative email while a 5 would be asking the user to do EXPLICITLY something. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', content))
    followup_score = int(prompt_deepinfra('Given the contents of an email, rate how likely it is that this email requires a followup or response from the recipient. For example, a 0 would be something the recipient can ignore and not respond to but a 5 would be something that the recipient should definitely acknowledge and respond to. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', content))
    trustworthy_score = int(prompt_deepinfra('Given a name rate how trustworthy the name sounds. For example, companies or things that do not sound like real names should have less score. Names that sound like its from a real person should be given a higher score. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', message['sender'].split('<')[0].strip()))
    domain_score = int(prompt_deepinfra('Given a domain, rate how trustworthy it is. For exmaple, gmail should be a 10 while abc.123.com should be given a lower score. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', message['sender'].split('@')[1].split('>')[0]))

    score = (exchange_score+spam_score+sender_score+subject_score+timing_score+content_score+personalization_score+action_score+followup_score+trustworthy_score+domain_score-(5 if used_subject else 0))/MAX_SCORE
    data.append({
        'sender': message['sender'],
        'used_subject': used_subject,
        'subject': message['subject'],
        'score': score,
        'scores': [spam_score, exchange_score, sender_score, subject_score, timing_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score]
    })
    print(used_subject, message['sender'], message['subject'], score, spam_score, exchange_score, sender_score, subject_score, timing_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score)
    save_data()

def worker(chunk, key):
    client = Groq(api_key=key)
    for i, item in enumerate(chunk):
        print(f'{i}/{len(chunk)}')
        run_iteration(item, client)
    
def save_data():
    with open('dump.json', 'w') as file:
        file.write(json.dumps(data, indent=2))

def data_saver():
    while True:
        time.sleep(10) # save every 10 seconds
        save_data()
        print('Backed up data')

def calculate_average_exchanges():
    with open('exchanges.json', 'r') as file:
        data = json.loads(file.read())
    exchange_counts = [data[key] for key in data]
    average = sum(exchange_counts)/len(data)
    return average, math.log10((max(exchange_counts)/average)+1)


TARGET_EMAIL = 'thomas@thomasatamian.com'
AVERAGE_EXCHANGES, MAX_EXCHANGE_SCORE = calculate_average_exchanges()
EXCHANGE_WEIGHT = 5
MAX_SCORE = 0+0+10+10+10+10+5+5+5+5+MAX_EXCHANGE_SCORE*5 # sum of scores for each type of score

# spam stuff
model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"
model = AutoModelForSequenceClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

i = 0
offset = 0
data = json.loads(open('dump.json', 'r').read())
current_set = 0

email_exchanges = json.loads(open('exchanges.json', 'r').read())
queue = []
start = time.time()
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        sender = message['From'].split(' <')[1][:-1] if '<' in message['From'] else message['From']
        if message['In-Reply-To'] and not sender == TARGET_EMAIL:
            queue.append(parse_mail(message))

        if i < offset:
            i += 1
            continue

        i += 1

        if i == 1000:
            break

print(f'Collecting queue took {round(time.time()-start, 2)} seconds')


THREADS = 1 # one for each api key
thread_list = []
chunks = [queue[i * len(queue) // THREADS:(i + 1) * len(queue) // THREADS] for i in range(THREADS)]
api_keys = open('groqkeys.txt', 'r').read().split('\n')
for i, chunk in enumerate(chunks):
    t = Thread(target=lambda: worker(chunk, api_keys[i]))
    t.start()
    thread_list.append(t)
# Thread(target=data_saver).start()

for t in thread_list:
    t.join()