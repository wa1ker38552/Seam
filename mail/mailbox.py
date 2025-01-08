from email.policy import default
from bs4 import BeautifulSoup
from groq import Groq
import email
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

def prompt(instructions, query):
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


client = Groq(api_key=os.environ['API_KEY'])
MAX_SCORE = 10+10+10+10+10+5+5 # sum of scores for each type of score

with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        message = parse_mail(message)
        soup = BeautifulSoup(message['body'], 'lxml')
        content = soup.get_text()
        content = re.sub(r'\s+', ' ', content).strip()
        used_subject = True if len(content) > 6000 else False
        content = message['subject'] if len(content) > 6000 else content

        sender_score = 0 if ('no' in message['sender'].lower() and 'reply' in message['sender'].lower()) or 'update' in message['sender'].lower() else 10
        subject_score = int(prompt('Given the subject line of an email, return whether or not the content of this email are important. Give it less score if it seems like the email was a automated response, return only a number from 0-10', message['subject']))
        timing_score = int(prompt('Given the contents of an email, determine whether or not it is urgent. For example a 0 would be not urgent and requiring attention immediately. However, a 10 would be something that is extremely important and must be immediately attended to. Return only a number from 0-10', content))
        content_score = int(prompt('Given the contents of an email, evaluate how relevant and important this email is to the person at hand. 0 means not important at all, something like a notification message or spam message and 10 means very important, something that might be personal or requiring the reciever to do something. Return only a number from 0-10', content))
        personalization_score = int(prompt('Given the contents of an email, rate how personal it is. A personal email will be addressing the recipient by name and would NOT be automated or mass sent. Return only a number from 0-10', content))
        action_score = int(prompt('Given the contents of an email, rate whether or not it requires the recipient to do something. For example, a 0 would be a informative email while a 5 would be asking the user to do EXPLICITLY something, return only a number from 0-5', content))
        followup_score = int(prompt('Given the contents of an email, rate how likely it is that this email requires a followup or response from the recipient. For example, a 0 would be something the recipient can ignore and not respond to but a 5 would be something that the recipient should definitely acknowledge and respond to. Return only a number from 0-5', content))

        score = (sender_score+subject_score+timing_score+content_score+personalization_score+action_score+followup_score)/MAX_SCORE
        print(used_subject, message['sender'], message['subject'], score, sender_score, subject_score, timing_score, content_score, personalization_score, action_score, followup_score)