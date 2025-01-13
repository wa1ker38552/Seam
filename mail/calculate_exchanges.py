from mailboxreader import MboxReader
from collections import defaultdict
import json

TARGET_EMAIL = 'thomas@thomasatamian.com'
email_exchanges = defaultdict(int)

i = 0
with MboxReader('All mail Including Spam and Trash-001.mbox') as mbox:
    for message in mbox:
        sender = message['From'].split(' <')[1][:-1] if '<' in message['From'] else message['From']
        reciever = message['To'].split(' <')[1][:-1] if message['To'] and '<' in message['To'] else message['To']
        if sender == TARGET_EMAIL:
            email_exchanges[reciever] += 1
        if message['In-Reply-To'] and not sender == TARGET_EMAIL:
            email_exchanges[sender] += 1
    
        i += 1
        if i == 10000: break


# save exchange data so that if I run it on a smaller group, it still uses the exchange data from the large group
with open('exchanges.json', 'w') as file:
    file.write(json.dumps(email_exchanges, indent=2))