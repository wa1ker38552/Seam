import csv
import json

with open('zillow_data.json', 'r') as json_file, open('data.csv', 'w', newline='') as csv_file:
    data = json.loads(json_file.read())
    parsed = []

    for item in data:
        for agent in item['agents']:
            if agent:
                parsed.append({
                    'address': item['address'],
                    'first_name': agent['name'].split()[0],
                    'full_name': agent['name'],
                    'broker': item['broker'],
                    'linkedin': agent['link']
                })

    writer = csv.DictWriter(csv_file, fieldnames=parsed[0].keys())
    writer.writeheader()
    writer.writerows(parsed)