import requests
import json

tokens = open('coresignal account creation/coresignal_tokens.txt', 'r').read().split('\n')
token = tokens[0]
token_index = 0


def fetch_job(jobid):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    r = requests.get(f'https://api.coresignal.com/cdapi/v1/professional_network/job/collect/{jobid}', headers=headers)
    return r.json()

job_ids = []
for item in json.loads(open('job_ids.json', 'r').read()):
    job_ids.extend([{'id': jobid, 'company': item['name']} for jobid in item['ids']])

job_details = json.loads(open('job_details.json', 'r').read())
offset = 3586

for i, item in enumerate(job_ids[offset:]):
    print(f'{offset+i}/{len(job_ids)}, token_index: {token_index}')
    job_data = fetch_job(item['id'])
    try:
        job_details.append({
            'description': job_data['description'],
            'title': job_data['title'],
            'company': item['company']
        })

        with open('job_details.json', 'w') as file:
            file.write(json.dumps(job_details, indent=2))
    except Exception as e:
        print(e, job_data)
        token_index += 1
        token = tokens[token_index]