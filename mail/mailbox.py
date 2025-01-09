from email.policy import default
from bs4 import BeautifulSoup
from threading import Thread
from groq import Groq
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

def prompt(client, instructions, query):
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

    sender_score = -5 if ('no' in message['sender'].lower() and 'reply' in message['sender'].lower()) or 'update' in message['sender'].lower() or 'info' in message['sender'] else 5
    subject_score = int(prompt(client, 'Given the subject line of an email, return whether or not the content of this email are important. Give it less score if it seems like the email was a automated response, return ONLY A NUMBER from 0-10', message['subject']))
    timing_score = int(prompt(client, 'Given the contents of an email, determine whether or not it is urgent. For example a 0 would be not urgent and requiring attention immediately. However, a 10 would be something that is extremely important and must be immediately attended to. Return ONLY A NUMBER from 0-10. If email is empty return 0', content))
    content_score = int(prompt(client, 'Given the contents of an email, evaluate how relevant and important this email is to the person at hand. 0 means not important at all, something like a notification message or spam message and 10 means very important, something that might be personal or requiring the reciever to do something. Return ONLY A NUMBER from 0-10. If email is empty return 0', content))
    personalization_score = int(prompt(client, 'Given the contents of an email, rate how personal it is. A personal email will be addressing the recipient by name and would NOT be automated or mass sent. Return ONLY A NUMBER from 0-10. If email is empty return 0', content))
    action_score = int(prompt(client, 'Given the contents of an email, rate whether or not it requires the recipient to do something. For example, a 0 would be a informative email while a 5 would be asking the user to do EXPLICITLY something, return ONLY A NUMBER from 0-5. If email is empty return 0', content))
    followup_score = int(prompt(client, 'Given the contents of an email, rate how likely it is that this email requires a followup or response from the recipient. For example, a 0 would be something the recipient can ignore and not respond to but a 5 would be something that the recipient should definitely acknowledge and respond to. Return ONLY A NUMBER from 0-5. If email is empty return 0', content))
    trustworthy_score = int(prompt(client, 'Given a name rate how trustworthy the name sounds. For example, companies or things that do not sound like real names should have less score. Names that sound like its from a real person should be given a higher score. Return ONLY A NUMBER from 0-5', message['sender'].split('<')[0].strip()))
    domain_score = int(prompt(client, 'Given a domain, rate how trustworthy it is. For exmaple, gmail should be a 10 while abc.123.com should be given a lower score. Return ONLY A NUMBER from 0-5', message['sender'].split('@')[1].split('>')[0]))

    score = (sender_score+subject_score+timing_score+content_score+personalization_score+action_score+followup_score+trustworthy_score+domain_score)/MAX_SCORE
    data.append({
        'sender': message['sender'],
        'used_subject': used_subject,
        'subject': message['subject'],
        'score': score,
        'scores': [sender_score, subject_score, timing_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score]
    })
    print(used_subject, message['sender'], message['subject'], score, sender_score, subject_score, timing_score, content_score, personalization_score, action_score, followup_score, trustworthy_score, domain_score)
    

def worker(chunk, key):
    client = Groq(api_key=key)
    for item in chunk:
        run_iteration(item, client)
    
def data_saver():
    while True:
        time.sleep(10) # save every 10 seconds
        with open('dump.json', 'w') as file:
            file.write(json.dumps(data, indent=2))
        print('Backed up data')

# https://stackoverflow.com/questions/59681461/read-a-big-mbox-file-with-python
# faster way to read using email lib since the file is very big
class MboxReader:
    def __init__(self, filename):
        self.handle = open(filename, 'rb')
        assert self.handle.readline().startswith(b'From ')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.handle.close()

    def __iter__(self):
        return iter(self.__next__())

    def __next__(self):
        lines = []
        while True:
            line = self.handle.readline()
            if line == b'' or line.startswith(b'From '):
                yield email.message_from_bytes(b''.join(lines), policy=default)
                if line == b'':
                    break
                lines = []
                continue
            lines.append(line)


MAX_SCORE = 5+10+10+10+10+5+5+5+5 # sum of scores for each type of score

i = 0
offset = 1000
data = json.loads(open('dump.json', 'r').read())
current_set = 0

queue = []
start = time.time()
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        if i < offset:
            i += 1
            continue

        # run_iteration(message)
        queue.append(parse_mail(message))
        i += 1

        if i == 1500:
            break

print(f'Collecting queue took {round(time.time()-start, 2)} seconds')

THREADS = 1 # one for each api key
thread_list = []
chunks = [queue[i * len(queue) // THREADS:(i + 1) * len(queue) // THREADS] for i in range(THREADS)]
api_keys = []
for i, chunk in enumerate(chunks):
    t = Thread(target=lambda: worker(chunk, api_keys[i]))
    t.start()
    thread_list.append(t)
Thread(target=data_saver).start()

for t in thread_list:
    t.join()