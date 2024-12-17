import requests
import json
import time

with open(r'C:\Users\walke\Downloads\VSCode\seam\apollo\job_details.json', 'r') as file:
    job_details = json.loads(file.read())


headers = {
    "TR-Dataset": "fb4bbea7-484c-482d-b818-e9e5e41781e6",
    "Authorization": open('authorization.txt', 'r').read(),
    "Content-Type": "application/json"
}


MAX_LENGTH = 120
chunks = []
current_chunk = []
for item in job_details:
    current_chunk.append(item)
    if len(current_chunk) == MAX_LENGTH:
        chunks.append(current_chunk)
        current_chunk = []
chunks.append(current_chunk)
print(len(job_details))

'''for chunk in chunks:
    payload = []
    for item in chunk:
        payload.append({
            "chunk_html": item['description'],
            "metadata": {
                "title": item['title'],
                "company": item['company']
            },
            "tracking_id": f'{item["title"]}_{item["company"]}_{time.time()}'
        })
        time.sleep(0.001)
    response = requests.post('https://api.trieve.ai/api/chunk', json=payload, headers=headers).json()
    print(len(payload), len(response['chunk_metadata']))
'''