from mailboxreader import MboxReader
from bs4 import BeautifulSoup
from threading import Thread
import json
import time
import re

def process_references(message):
    global largest_thread
    if references := message['References']:
        references = len(references.split())
        if references > largest_thread['amount']:
            if references == 145:
                with open('references.txt', 'w') as file:
                    file.write(message['References'])
            largest_thread = {
                'amount': references,
                'data': message['References']
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

def process(message):
    if body := extract_body(message):
        soup = BeautifulSoup(body, 'lxml')
        content = soup.get_text()
        content = re.sub(r'\s+', ' ', content).strip()
    else:
        content = ''

    chunk.append({
        'sender': message['From'],
        'receiver': message['To'],
        'reference': message['References'],
        'content': content,
        'date': message['Date'],
        'subject': message['Subject'],
        'in-reply-to': message['In-Reply-To']
    })

largest_thread = {
    'amount': 0,
    'data': ''
}

chunk = []
i = 0
c = 0
s = time.time()
threads = []
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        thread = Thread(target=lambda: process(message))
        thread.start()
        threads.append(thread)

        if (i := i+1) % 5000 == 0: 
            print('here')
            print(i, end=' ')
            for thread in threads:
                thread.join()
            threads = []
            with open(f'mailbox/{c}.json', 'w') as file:
                file.write(json.dumps(chunk))
            chunk = []
            c += 1


with open(f'mailbox/{c}.json', 'w') as file:
    file.write(json.dumps(chunk))
print(time.time()-s)