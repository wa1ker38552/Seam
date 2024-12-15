import requests
import json

token = open('token.txt', 'r').read()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

def fetch_job(jobid):
    r = requests.get(f'https://api.coresignal.com/cdapi/v1/professional_network/job/collect/{jobid}', headers=headers)
    return r.json()

job_ids = []
for item in json.loads(open('job_ids.json', 'r').read()):
    job_ids.extend([{'id': jobid, 'company': item['name']} for jobid in item['ids']])

job_details = json.loads(open('job_details.json', 'r').read())
offset = 3383

for i, item in enumerate(job_ids[offset:]):
    print(f'{offset+i}/{len(job_ids)}')
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
        break