from parse_json_mailbox import parse_mailbox
from deepinfra import prompt_deepinfra
from analyze_spam import predict_spam
from mailboxreader import MboxReader
from multiprocessing import Process
from bs4 import BeautifulSoup
from threading import Thread
import threading
import math
import time
import json
import re
import os

# for reference
# sender -> From
# reciever -> To
# subject -> Subject
# date -> Date
# body -> extract_body(message)


def parse_sender(message):
    return message['sender'].split(' <')[1][:-1] if '<' in message['sender'] else message['sender']

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

def run_iteration(message):
    '''
    if body := extract_body(message):
        soup = BeautifulSoup(body, 'lxml')
        content = soup.get_text()
        content = re.sub(r'\s+', ' ', content).strip()
    else:
        content = ''
    '''
    content = message['content']

    # TODO find a way to analyze the entire content even if it exceeds a max length
    used_subject = True if len(content) > 6000 else False
    content = message['subject'] if len(content) > 6000 else content

    if not content:
        used_subject = True
        content = message['subject']

    sender = parse_sender(message)

    spam_score = -5 if predict_spam(content) == 'spam' else 0
    # TODO make it so exchange factors in frequency of communication
    exchange_score = math.log10((email_exchanges[sender] if sender in email_exchanges else 0/AVERAGE_EXCHANGES)+1)*5
    polarity_score = exchange_data[sender]['sentiment']['average_polarity']*POLARITY_WEIGHT
    subjectivity_score = exchange_data[sender]['sentiment']['average_subjectivity']*SUBJECTIVITY_WEIGHT
    sender_score = -20 if ('no' in message['sender'].lower() and 'reply' in message['sender'].lower()) or 'update' in message['sender'].lower() or 'info' in message['sender'].lower() or 'notification' in message['sender'].lower() or 'support' in message['sender'].lower() else 0
    
    # non-exchange score factors
    # TODO improve prompt/failsafe so that if llama returns non-number it doesn't fail
    try:
        subject_score = int(prompt_deepinfra('Given the subject line of an email, return whether or not the content of this email are important. Give it less score if it seems like the email was a automated response. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', message['subject']))
        urgency_score = int(prompt_deepinfra('Given the contents of an email, determine whether or not it is urgent. For example a 0 would be not urgent and requiring attention immediately. However, a 10 would be something that is extremely important and must be immediately attended to. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
        content_score = int(prompt_deepinfra('Given the contents of an email, evaluate how relevant and important this email is to the person at hand. 0 means not important at all, something like a notification message or spam message and 10 means very important, something that might be personal or requiring the reciever to do something. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
        personalization_score = int(prompt_deepinfra('Given the contents of an email, rate how personal it is. A personal email will be addressing the recipient by name and would NOT be automated or mass sent. Return ONLY A NUMBER from 0-10 without ANY ADDITIONAL NOTES', content))
        action_score = int(prompt_deepinfra('Given the contents of an email, rate whether or not it requires the recipient to do something. For example, a 0 would be a informative email while a 5 would be asking the user to do EXPLICITLY something. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', content))
        followup_score = int(prompt_deepinfra('Given the contents of an email, rate how likely it is that this email requires a followup or response from the recipient. For example, a 0 would be something the recipient can ignore and not respond to but a 5 would be something that the recipient should definitely acknowledge and respond to. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', content))
        trustworthy_score = int(prompt_deepinfra('Given a name rate how trustworthy the name sounds. For example, companies or things that do not sound like real names should have less score. Names that sound like its from a real person should be given a higher score. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', message['sender'].split('<')[0].strip()))
        domain_score = int(prompt_deepinfra('Given a domain, rate how trustworthy it is. For exmaple, gmail should be a 10 while abc.123.com should be given a lower score. Return ONLY A NUMBER from 0-5 without ANY ADDITIONAL NOTES', message['sender'].split('@')[1].split('>')[0]))

        score = (exchange_score+polarity_score+subjectivity_score+spam_score+sender_score+subject_score+urgency_score+content_score+personalization_score+action_score+followup_score+trustworthy_score+domain_score-(5 if used_subject else 0))/MAX_SCORE
        data.append({
            'sender': sender,
            'used_subject': used_subject,
            'subject': message['subject'],
            'score': score,
            'scores': [spam_score, exchange_score, polarity_score, subjectivity_score, sender_score, subject_score, urgency_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score]
        })
        print(used_subject, sender, message['subject'], score, spam_score, exchange_score, polarity_score, subjectivity_score, sender_score, subject_score, urgency_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score)
        save_data()
    except Exception as e:
        print(f'Failed to prompt: {e}')

def worker(chunk):
    for i, item in enumerate(chunk):
        print(f'{threading.get_ident()}: {i}/{len(chunk)}')
        run_iteration(item)
    
def save_data():
    with open('dump.json', 'w') as file:
        # use locks to avoid corruption while writing from multiple threads
        lock.acquire()
        try:
            file.write(json.dumps(data, indent=2))
        finally:
            lock.release()

def calculate_average_exchanges():
    with open('exchanges.json', 'r') as file:
        data = json.loads(file.read())

    exchange_counts = [data[key]['frequency'] for key in data]
    average = sum(exchange_counts)/len(data)
    return average, math.log10((max(exchange_counts)/average)+1)


s = time.time()
TARGET_EMAIL = 'thomas@thomasatamian.com'
TARGET_DOMAIN = TARGET_EMAIL.split('@')[1]
AVERAGE_EXCHANGES, MAX_EXCHANGE_SCORE = calculate_average_exchanges()

# score weights
EXCHANGE_WEIGHT = 5
POLARITY_WEIGHT = 5 # values range from -1 to 1 so the max is the weight
SUBJECTIVITY_WEIGHT = -5 # values range from -1 to 1. Having a negative weight pioritizes objective exchanges rather than subjective ones
MAX_SCORE = 0+0+10+10+10+10+5+5+5+5+MAX_EXCHANGE_SCORE*5+POLARITY_WEIGHT+abs(SUBJECTIVITY_WEIGHT) # sum of scores for each type of score

i = 0
data = []
current_set = 0

lock = threading.Lock()
exchange_data = json.loads(open('exchanges.json', 'r').read())
email_exchanges = {key: exchange_data[key]['frequency'] for key in exchange_data}
queue = []
start = time.time()

inbox = parse_mailbox('mailbox')
for message in inbox:
    sender = parse_sender(message)
    if message['in-reply-to'] and sender != TARGET_EMAIL and sender.split('@')[1] != TARGET_DOMAIN:
        queue.append(message)

    # if i%100 == 0: print(i) # only print every 100 to make it faster
    if (i := i+1) == 5000:
        break

print(f'Collecting queue took {round(time.time()-start, 2)} seconds')


THREADS = 1
thread_list = []
chunks = [queue[i * len(queue) // THREADS:(i + 1) * len(queue) // THREADS] for i in range(THREADS)]

for i, chunk in enumerate(chunks):
    t = Thread(target=lambda: worker(chunk))
    t.start()
    thread_list.append(t)

for t in thread_list:
    t.join()

# sort data
data = json.loads(open('dump.json', 'r').read())
data = sorted(data, key=lambda x: x['score'])[::-1]
with open('dump.json', 'w') as file:
    file.write(json.dumps(data, indent=2))

print(time.time()-s)