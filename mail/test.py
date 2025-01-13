from mailboxreader import MboxReader
from email.policy import default
import json
import email


with open('dump.json', 'r') as file:
    print(len(json.loads(file.read())))

'''with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        print(message.get('To'))
        break'''