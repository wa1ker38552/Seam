# analyze the data and parse it. Also get list of jobs for each company using coresignal
import requests
import json
import csv


token = open('token.txt', 'r').read()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

def get_job_ids(linkedin):
    payload = {
        'company_linkedin_url': linkedin,
        "application_active":"True",
        "deleted":"False"
    }
    r = requests.post('https://api.coresignal.com/cdapi/v1/professional_network/job/search/filter', json=payload, headers=headers)
    return r.json()

with open('apollo-accounts-export.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    data = [row for row in reader]


job_ids = json.loads(open('job_ids.json', 'r').read())
offset = 1195
for i, item in enumerate(data[offset:]):
    print(i+offset, len(data))
    ids = get_job_ids(item['Company Linkedin Url'])
    if isinstance(ids, list):
        job_ids.append({
            'name': item['Company'],
            'ids': ids
        })
        with open('job_ids.json', 'w') as file:
            file.write(json.dumps(job_ids, indent=2))
    else:
        print(ids)
        break
