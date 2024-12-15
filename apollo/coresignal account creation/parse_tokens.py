from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Thread
import time

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])

tokens = []

offset = 17
for i in range(56):
    print(i+offset, 'token')
    driver = webdriver.Chrome(options=options)
    driver.get('https://dashboard.coresignal.com/sign-in')
    driver.find_element(By.XPATH, '/html/body/div/div/div/div[3]/form/div/div[1]/div/input').send_keys(f'coresignal@mailroute{i+offset}.ps99rap.com')
    driver.find_element(By.XPATH, '/html/body/div/div/div/div[3]/form/div/div[2]/div/div/input').send_keys('password123')
    driver.find_element(By.XPATH, '/html/body/div/div/div/div[3]/form/div/div[3]/button').click()

    while driver.current_url == 'https://dashboard.coresignal.com/sign-in':
        time.sleep(0.1)

    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    token = soup.find('input', attrs={'name': 'apiKey'})['value']
    tokens.append(token)

    with open('coresignal_tokens.txt', 'w') as file:
        file.write('\n'.join(tokens))