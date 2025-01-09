import json

data = json.loads(open('dump.json', 'r').read())
data = sorted(data, key=lambda x: x['score'])[::-1]

with open('sorted.json', 'w') as file:
    file.write(json.dumps(data, indent=2))