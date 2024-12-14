from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Thread
import json
import time

# authenticate

def save_cookies(driver):
    with open('cookies.json', 'w') as file:
        file.write(json.dumps(driver.get_cookies(), indent=2))

def create_instance(chunk, thread_identifier):
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(800, 800)
    driver.set_window_position(thread_identifier*300, thread_identifier*100)

    driver.get('https://linkedin.com')
    for cookie in cookies:
        driver.add_cookie(cookie)

    for i, organization in enumerate(chunk):
        print(f'{thread_identifier}: {i}/{len(chunk)}')
        if organization['linkedin']:
            driver.get(organization['linkedin']+'/jobs/')
            soup = BeautifulSoup(driver.page_source, 'lxml')

            try:
                openings = int(soup.find('h4', attrs={'class': 'org-jobs-job-search-form-module__headline'}).get_text().split('has ')[1].split()[0].strip().replace(',', ''))

                if openings > 9:
                    more_jobs_link = soup.find('a', attrs={'class': 'ember-view org-jobs-recently-posted-jobs-module__show-all-jobs-btn-link link-without-hover-visited'})['href']
                    more_jobs_link = more_jobs_link.split('f_C=')[1].split('&')[0]
                    driver.get(f'https://www.linkedin.com/jobs/search/?f_C={more_jobs_link}')

                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    card_titles = soup.find_all('div', attrs={'class': 'full-width artdeco-entity-lockup__title ember-view'})
                    jobs = [title.find('strong').get_text().strip().replace('\n', '') for title in card_titles]
                else:
                    soup = BeautifulSoup(driver.page_source, 'lxml')
                    cards = soup.find_all('div', attrs={'class': 'job-card-square__title'})
                    jobs = [card.find('strong').get_text().strip().replace('\n', '') for card in cards]
                job_list[organization['name']] = jobs
            except AttributeError:
                # no openings
                job_list[organization['name']] = []
                time.sleep(5)    


options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])

NUM_INSTANCES = 1
cookies = json.loads(open('cookies.json', 'r').read())
organizations = json.loads(open('organizations.json', 'r').read())
job_list = {}

threads = []
for i, chunk in enumerate([organizations[i::NUM_INSTANCES] for i in range(NUM_INSTANCES)]):
    thread = Thread(target=lambda: create_instance(chunk, i))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

with open('job_list.json', 'w') as file:
    file.write(json.dumps(job_list, indent=2))
