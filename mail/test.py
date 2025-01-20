from mailboxreader import MboxReader
from email.policy import default
import email
import json
import time
import re
import os

'''with open('dump.json', 'r') as file:
    print(len(json.loads(file.read())))'''

def parse_replies(message):
    try:
        body = message.get_payload(decode=True).decode(message.get_content_charset(), 'ignore')
        body_cleaned = re.sub(r'\r\n', '\n', body)  # replace CRLF with LF
        body_cleaned = re.sub(r'\xef\xbf\xbc', '', body_cleaned)  # remove invalid characters
        body_cleaned = re.sub(r'\xe2\x80\x99', "'", body_cleaned)  # replace single quotes
        body_cleaned = re.sub(r'\xe2\x80\xaf', ' ', body_cleaned)  # replace narrow no-break space

        message_split_pattern = re.compile(r'(On .*? wrote:|On .*? at .*?:)')
        messages = message_split_pattern.split(body_cleaned)

        parsed_messages = []
        current_message = ""
        for part in messages:
            if re.match(message_split_pattern, part): 
                if current_message.strip():
                    parsed_messages.append(current_message.strip())
                current_message = part
            else:
                current_message += part 

        if current_message.strip():
            parsed_messages.append(current_message.strip())

        cleaned_messages = [re.sub(r'^>+', '', msg, flags=re.MULTILINE).strip() for msg in parsed_messages]
        for i, message in enumerate(cleaned_messages):
            cleaned_messages[i] = '\n'.join([line.strip() for line in message.split('\n')]).replace('￼', '') # remove whitespaces in each line

        cleaned_messages = [re.sub(r'\n+$', '', msg) for msg in cleaned_messages]
        return cleaned_messages
    except:
        return []

i = 0
data = []
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        if message['In-Reply-To']:
            s = time.time()
            parts = []
            if message.is_multipart():
                for part in message.get_payload():
                    if part.get_content_type() == 'text/plain':
                        parts.append(parse_replies(part))
            else:
                parts.append(parse_replies(message))
            data.append({
                'sender': message['From'],
                'receiver': message['To'],
                'reference': message['References'],
                'content': parts,
                'date': message['Date'],
                'subject': message['Subject'],
                'in-reply-to': message['In-Reply-To']
            })

        if (i := i + 1) % 5000 == 0:
            print(i)
            with open(f'mailbox_replied_to_only/{int(i/5000)}.json', 'w') as file:
                file.write(json.dumps(data))
            data = []