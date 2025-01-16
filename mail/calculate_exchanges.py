from mailboxreader import MboxReader
from collections import defaultdict
from bs4 import BeautifulSoup
from textblob import TextBlob
from datetime import datetime
from threading import Thread
import json
import time
import re

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

def parse_sender(message):
    return message['From'].split(' <')[1][:-1] if '<' in message['From'] else message['From']

def process_inbox(message):
    sender = parse_sender(message)
    # reciever = message['To'].split(' <')[1][:-1] if message['To'] and '<' in message['To'] else message['To']

    # only count interactions that the target has responded to
    # TODO make it so it weighs interactions from seperate threads differently than from interactions from the same thread
    if message['In-Reply-To'] and sender != TARGET_EMAIL:
        email_exchanges[sender] += 1
        timestamp = datetime.strptime(message['Date'], "%a, %d %b %Y %H:%M:%S %z").timestamp()
        exchange_timestamps[sender].append(timestamp)

        body = extract_body(message)
        if body:
            soup = BeautifulSoup(body, 'lxml')
            content = soup.get_text()
            content = re.sub(r'\s+', ' ', content).strip()
        else:
            content = ''

        blob = TextBlob(content)
        polarity = blob.polarity
        subjectivity = blob.subjectivity
        if sender in exchange_sentiment:
            exchange_sentiment[sender]['polarity'].append(polarity)
            exchange_sentiment[sender]['subjectivity'].append(subjectivity) # highlights a more informal relationship?
        else:
            exchange_sentiment[sender] = {
                'polarity': [polarity],
                'subjectivity': [subjectivity]
            }


TARGET_EMAIL = 'thomas@thomasatamian.com'
email_exchanges = defaultdict(int)
exchange_timestamps = defaultdict(list)
exchange_averages = {}
exchange_sentiment = {}
exchange_data = defaultdict(dict)
i = 0

threads = []
queue = []
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        queue.append(message)
        if (i := i+1) == 10000: break

# use dict for o(1) search
viable_senders = {sender: None for message in queue if message['In-Reply-To'] and (sender := parse_sender(message)) != TARGET_EMAIL}

# go through queue to pick out emails that were sent from an account that the target has responded to before
for message in queue:
    if parse_sender(message) in viable_senders:
        thread = Thread(target=lambda: process_inbox(message))
        thread.start()
        threads.append(thread)

for thread in threads:
    thread.join()

# post processing stuff
# calculate averages
for key in exchange_timestamps:
    exchange_timestamps[key].sort()
    differences = [exchange_timestamps[key][i+1] - exchange_timestamps[key][i] for i in range(len(exchange_timestamps[key]) - 1)]
    exchange_averages[key] = sum(differences) / len(differences) if differences else None

for key in email_exchanges:
    exchange_data[key]['frequency'] = email_exchanges[key]
for key in exchange_averages:
    exchange_data[key]['averages'] = exchange_averages[key]
for key in exchange_sentiment:
    polarity_nonzero = [i for i in exchange_sentiment[key]['polarity'] if i]
    subjectvitiy_nonzero = [i for i in exchange_sentiment[key]['subjectivity'] if i]

    exchange_data[key]['sentiment'] = {
        'average_polarity': sum(polarity_nonzero)/len(polarity_nonzero) if polarity_nonzero else 0,
        'average_subjectivity': sum(subjectvitiy_nonzero)/len(subjectvitiy_nonzero) if polarity_nonzero else 0
    }


# save exchange data so that if I run it on a smaller group, it still uses the exchange data from the large group
with open('exchanges.json', 'w') as file:
    file.write(json.dumps(exchange_data, indent=2))