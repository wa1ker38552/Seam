import csv
import json

with open('zillow_agent_data.json', 'r') as json_file, open('data.csv', 'w', newline='') as csv_file:
    data = json.loads(json_file.read())
    writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)