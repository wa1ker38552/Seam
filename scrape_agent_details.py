import json
from zillow_scraper import get_agent_data

with open('zillow_listings_out.json', 'r') as file:
    listings = json.loads(file.read())

listing_data = json.loads(open('zillow_data.json', 'r').read())
offset = 0 # in case you need to re-run
for i, item in enumerate(listings[offset:]):
    print(offset+i, item['zpid'], item['address'])
    if item['zpid']:
        listing_data.append(
            item.update(get_agent_data(item['zpid'])) or item # combine the 2 dictionaries
        )
        # save after every search just in-case it fails and need to re-run
        with open('zillow_data.json', 'w') as file:
            file.write(json.dumps(listing_data, indent=2))