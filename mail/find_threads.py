from mailboxreader import MboxReader
from threading import Thread
import json

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

def process_message(message):
    if message['References'].strip() == references.strip():
        print(message['Subject'])

largest_thread = {
    'amount': 0,
    'data': ''
}

threads = []
processes = []
references = open('references.txt', 'r').read()
i = 0
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        t = Thread(target=lambda: process_references(message))
        t.start()
        threads.append(t)
        
        if (i := i+1) % 1000 == 0: print(i)


for t in threads:
    t.join()