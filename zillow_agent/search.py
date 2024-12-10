from googlesearch import search
import json

# duplicate with slight modifications
agent_data = json.loads(open('zillow_agent_data.json', 'r').read())
offset = 0 # in case you need to re-run
for i, agent in enumerate(agent_data[offset:]):
    print(f'{offset+i}/{len(agent_data)}', agent['full_name'])
    link = None
    for item in search(f'{agent["full_name"]} {agent["broker"]} linkedin'):
        if item.startswith('https://www.linkedin.com/in/'):
            link = item
            break
    agent_data[i+offset]['linkedin'] = link
    # save after every search just in-case it fails and need to re-run
    with open('zillow_agent_data.json', 'w') as file:
        file.write(json.dumps(agent_data, indent=2))
