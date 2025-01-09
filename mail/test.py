import json

with open('dump.json', 'r') as file:
    print(len(json.loads(file.read())))