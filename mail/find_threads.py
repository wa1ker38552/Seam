
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from parse_json_mailbox import parse_mailbox
from collections import defaultdict
from bs4 import BeautifulSoup
import json

def get_longest_thread():
    inbox = parse_mailbox('mailbox')
    threads = defaultdict(list)
    i = 0
    for message in inbox:
        if message['in-reply-to'] and message['subject']:
            threads[message['subject']].append(len(message['content']))
        if (i := i + 1) % 10000 == 0:
            print(i)

    with open('threads.json', 'w') as file:
        file.write(json.dumps(threads, indent=2))

def analyze_longest_thread():
    with open('threads.json', 'r') as file:
        threads = json.loads(file.read())

        longest = [0, None]
        for subject in threads:
            if (length := len(threads[subject])) > longest[0]:
                longest = [length, subject]
        
        return threads[longest[1]]
    
def remove_duplicates(messages, threshold=0.99):
    vectorizer = TfidfVectorizer().fit_transform([message['content'] for message in messages])
    similarity_matrix = cosine_similarity(vectorizer)
    
    unique_messages = []
    seen_indices = set()
    
    for i, message in enumerate(messages):
        if i not in seen_indices:
            unique_messages.append(message['content'])
            for j, sim in enumerate(similarity_matrix[i]):
                if sim >= threshold and i != j:
                    seen_indices.add(j)
    
    return unique_messages

inbox = parse_mailbox('mailbox_replied_to_only')
vectorizer = TfidfVectorizer()

messages = []
i = 0
for message in inbox:
    if message['subject'] and 'Re: Woodland Hills, CA' in message['subject']:
        content = []
        for part in message['content']:
            for item in part:
                content.append({
                    'date': message['date'] if not item.startswith('On') else item.split('wrote:')[0],
                    'content': item.split('wrote:')[1].strip() if item.startswith('On') else item
                })
            # content.extend([item.split('wrote:')[1].strip() for item in part if item.startswith('On')])

        messages.extend(content)

# parse html
for i, message in enumerate(messages):
    soup = BeautifulSoup(message['content'], 'html.parser')
    messages[i]['content'] = soup.get_text(separator=' ', strip=True)

with open('threads_raw.json', 'w') as file:
    file.write(json.dumps(messages, indent=2))
            
reverse_index = {message['content']: message['date'] for message in messages}
messages = remove_duplicates(messages)

formatted = []
for message in messages:
    formatted.append({
        'date': reverse_index[message],
        'content': message
    })

with open('threads.json', 'w') as file:
    file.write(json.dumps(formatted, indent=2))
    

'''with open('threads.json', 'r') as file:
    data = json.loads(file.read())

    for ln in data:
        if ln.startswith('On'):
            ln = ln.split('wrote:')[1]
        print(ln)'''