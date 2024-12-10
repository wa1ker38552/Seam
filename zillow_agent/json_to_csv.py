import csv
import json

with open('zillow_agent_data.json', 'r') as json_file, open('data.csv', 'w', newline='') as csv_file:
    data = json.loads(json_file.read())
    parsed = []

    for item in data:
        item['listing_1'] = item['last_two_listings'][0]
        item['listing_2'] = item['last_two_listings'][1]
        del item['last_two_listings']
        parsed.append(item)

    writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)