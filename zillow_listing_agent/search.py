from googlesearch import search
import json

listing_data = json.loads(open('zillow_data.json', 'r').read())
offset = 404 # in case you need to re-run
for i, listing in enumerate(listing_data[offset:]):
    print(offset+i, listing['zpid'], listing['address'])
    agents = []
    for agent in listing['agents']:
        if agent:
            link = None
            for item in search(f'{agent} {listing["broker"]} linkedin'):
                if item.startswith('https://www.linkedin.com/in/'):
                    link = item
                    break
            agents.append({
                'name': agent,
                'link': link
            })
    listing['agents'] = agents
    # save after every search just in-case it fails and need to re-run
    with open('zillow_data.json', 'w') as file:
        file.write(json.dumps(listing_data, indent=2))
