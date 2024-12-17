import json

with open('semantic_search_results.json', 'r') as file:
    data = json.loads(file.read())

# clean data
parsed = []
for item in data:
    if not 'jr' in item['metadata']['title'].lower() and not 'intern' in item['metadata']['title'].lower():
        parsed.append(item)

with open('semantic_search_results.json', 'w') as file:
    file.write(json.dumps(parsed, indent=2))
