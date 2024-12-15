from selenium import webdriver
import time
import json

links = json.loads(open('coresignal_verification_links.json', 'r').read())
offset = 1
token_urls = []

for i, link in enumerate(links[offset:]):
    print(f'{i+offset}/{len(links)}')
    driver = webdriver.Chrome()
    driver.get(link)

    while driver.current_url == link:
        time.sleep(0.1)

    token_urls.append(driver.current_url)
    with open('coresignal_verification_tokens.json', 'w') as file:
        file.write(json.dumps(token_urls, indent=2))