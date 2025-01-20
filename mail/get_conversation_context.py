
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from parse_json_mailbox import parse_mailbox
from collections import defaultdict
import json

def remove_duplicates(messages, threshold=0.99):
    vectorizer = TfidfVectorizer().fit_transform(messages)
    similarity_matrix = cosine_similarity(vectorizer)
    
    unique_messages = []
    seen_indices = set()
    
    for i, message in enumerate(messages):
        if i not in seen_indices:
            unique_messages.append(message)
            for j, sim in enumerate(similarity_matrix[i]):
                if sim >= threshold and i != j:
                    seen_indices.add(j)
    
    return unique_messages

def get_raw_conversations():
    for message in inbox:
        content = []
        for part in message['content']:
            for item in part:
                try:
                    content.append(item.split('wrote:')[1].strip() if item.startswith('On') else item)
                except IndexError:
                    # TODO find out what happens here
                    pass
                
        sender = message['sender'].split('<')[1][:-1] if message['sender'] and '<' in message['sender'] else message['sender']
        receiver = message['receiver'].split('<')[1][:-1] if message['receiver'] and '<' in message['receiver'] else message['receiver']
        if sender == TARGET:
            conversations[receiver].extend(content)
        else:
            conversations[sender].extend(content)

    with open('conversation_data.json', 'w') as file:
        file.write(json.dumps(conversations, indent=2))

def get_longest_conversation():
    with open('conversation_data.json', 'r') as file:
        data = json.loads(file.read())

        biggest = [0, None]
        for key in data:
            if key.split('@')[1] != TARGET.split('@')[1]:
                if (length := len(data[key])) > biggest[0]:
                    biggest = [length, key]
        
        print(biggest)
        filtered = remove_duplicates(data[biggest[1]])
        with open('longest_conversation_data.json', 'w') as file:
            file.write(json.dumps(filtered, indent=2))

TARGET = 'thomas@thomasatamian.com'
# inbox = parse_mailbox('mailbox_replied_to_only')
conversations = defaultdict(list)
# get_raw_conversations()

with open('longest_conversation_data.json', 'r') as file:
    data = json.loads(file.read())
    chars = 0

    for line in data:
        line = line.replace('nSent from my iPhone', '')
        chars += len(line)
    print(chars)