from bs4 import BeautifulSoup
import requests
import math
import json


def scrape_agents(query, pages=10):
    links = []
    for i in range(pages):
        print(f'Requesting {i+1}/{pages}')
        r = requests.get(f'https://www.zillow.com/professionals/real-estate-agent-reviews/{"-".join(query.split())}/?page={i+1}', headers={
            'Content-Type': 'application/json',
            'Referrer': 'http://zillow.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        })
        
        soup = BeautifulSoup(r.text, 'html.parser')
        card_links = soup.find_all('a', attrs={'class': 'StyledCard-c11n-8-101-3__sc-1w6p0lv-0 cfmRww'})
        for item in card_links:
            links.append('https://www.zillow.com/'+item['href'])
    with open('zillow_agent_links.json', 'w') as file:
        file.write(json.dumps(links, indent=2))
    return links

def parse_number(n):
    n = n.lower()
    for i, suffix in enumerate(['k', 'm', 'b']):
        if suffix in n:
            return math.ceil(float(n.replace(suffix, ''))*(1000**(i+1))) # use 1000^(index of suffix)
    try:
        return int(n)
    except ValueError:
        return 0

def scrape_agent_page(url):
    r = requests.get(url, headers={
        'Content-Type': 'application/json',
        'Referrer': 'http://zillow.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })

    soup = BeautifulSoup(r.text, 'html.parser')
    name = soup.find('h1', attrs={'class': 'Text-c11n-8-107-0__sc-aiai24-0 StyledHeading-c11n-8-107-0__sc-s7fcif-0 gmdEgd'}).get_text()
    broker = soup.find('span', attrs={'class': 'Text-c11n-8-107-0__sc-aiai24-0 bmGggf'}).get_text()

    stats = soup.find_all('div', attrs={'class': 'Text-c11n-8-107-0__sc-aiai24-0 StyledHeading-c11n-8-107-0__sc-s7fcif-0 gmdEgd'})
    average_price = int(stats[0].get_text().replace(',', ''))
    total_sales = int(stats[1].get_text().replace(',', ''))
    yearly_sales = parse_number(stats[-1].get_text().replace('$', ''))

    # lucky me the address is the alt tag for the images :)
    images = soup.find_all('img', attrs={'class': 'Image-c11n-8-107-0__sc-1rtmhsc-0'})
    listings = [i['alt'] for i in images][1:3] # only take first 2 (first one is empty always)
    return {
        'first_name': name.split()[0],
        'full_name': name,
        'broker': broker,
        'average_price': average_price,
        'total_sales': total_sales,
        'yearly_sales': yearly_sales,
        'last_two_listings': listings
    }


# scrape_agents('san jose, ca')

# logic to go through agent list and scrape individual agent pages
with open('zillow_agent_links.json', 'r') as file:
    agent_links = json.loads(file.read())

offset = 75
agent_data = json.loads(open('zillow_agent_data.json', 'r').read())
for i, item in enumerate(agent_links[offset:]):
    print(f'{offset+i}/{len(agent_links)}', item)
    agent_data.append(scrape_agent_page(item))
    with open('zillow_agent_data.json', 'w') as file:
        file.write(json.dumps(agent_data, indent=2))