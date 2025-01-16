import json

# sort data
data = json.loads(open('dump.json', 'r').read())
data = sorted(data, key=lambda x: x['score'])[::-1]
with open('dump.json', 'w') as file:
    file.write(json.dumps(data, indent=2))