from geopy.geocoders import Nominatim
import requests
import urllib
import json
import math

'''
"west": -122.20735192578124, # bl
"east": -121.54267907421874, #tl
"south": 36.996706638779465, # bl
"north": 37.61985503803353 #tl
'''
    
def get_coordinates(query):
    location = geolocator.geocode(query)
    return location.latitude, location.longitude

def create_bounding_box(lat, lon, side_length=20):
    # side length is in km
    lat_offset = side_length/2/111
    lon_offset = side_length/2/(111 * math.cos(math.radians(lat)))

    return {
        "bottom_left": (lat - lat_offset, lon - lon_offset),
        "top_right": (lat + lat_offset, lon + lon_offset)
    }

def scrape_listings_by_query(query, output=True):
    lat, lon = get_coordinates(query)
    bbox = create_bounding_box(lat, lon) # create bounding box (required for api request)
    r = requests.put('https://www.zillow.com/async-create-search-page-state', json={
        "searchQueryState": {
            "pagination": {},
            "isMapVisible": True,
            "mapBounds":{
                "west": bbox['bottom_left'][1],
                "east": bbox['top_right'][1],
                "south": bbox['bottom_left'][0],
                "north": bbox['top_right'][0]
            },
            "usersSearchTerm": query,
            "filterState": { 
                "sortSelection": {
                    "value": "globalrelevanceex"
                }
            },
            "isListVisible": True
        },
        "wants":{
            "cat1":["mapResults"]
        }
    }, headers={
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    parsed_data = r.json()

    listings = []
    for item in parsed_data['cat1']['searchResults']['mapResults']:
        listings.append({
            'zpid': item['zpid'] if 'zpid' in item else None,
            'address': item['address'] if 'address' in item else None
        })
    
    if output:
        with open('zillow_listings_out.json', 'w') as file:
            file.write(json.dumps(listings, indent=2))
    return listings

def get_agent_data(zpid):
    # create encoded parameters
    variable_encoded = urllib.parse.quote(json.dumps({'zpid': zpid}))
    encoded_url = f'https://www.zillow.com/graphql/?extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22b28c6dddeaff7d853544684711b936fcbdbeff4c4800844352b0755e3e06a133%22%7D%7D&variables={variable_encoded}'
    r = requests.get(encoded_url, 
                     headers={
                        'Content-Type': 'application/json',
                        'Referrer': 'http://zillow.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
                     })
    try:
        parsed_data = r.json()['data']['property']
        agent_email = parsed_data['attributionInfo']['agentEmail']
        agent_broker = parsed_data['attributionInfo']['brokerName']
        agents = [i['memberFullName'] for i in parsed_data['attributionInfo']['listingAgents']]
        return {
            'email': agent_email,
            'broker': agent_broker,
            'agents': agents
        }
    except requests.exceptions.JSONDecodeError:
        print(r.status_code, encoded_url)

geolocator = Nominatim(user_agent='zillow_scraper')

# scrape_listings_by_query('Orange County, CA')
