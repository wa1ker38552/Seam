from selenium.webdriver.common.by import By
from selenium import webdriver
from threading import Thread
import time

def run_instance(chunk):
    driver = webdriver.Chrome(options=options)

    for address in chunk:
        print(address)
        driver.get('https://dashboard.coresignal.com/sign-up')

        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div[3]/form/div/div[1]/div/input').send_keys(address)
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div[3]/form/div/div[2]/div[1]/div/input').send_keys('password123')
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/div[3]/form/div/div[3]/button').click()

        time.sleep(3)
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[1]/div/input').send_keys('alksfjklsadf alsdkf')
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[2]/div/div[1]/input').click()
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[2]/div/div[2]/ul/li[1]').click()

        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[3]/div/div/input').click()
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[3]/div/div[2]/ul/li[1]').click()

        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[4]/div/div/input').click()
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[4]/div/div[2]/ul/li[1]').click()

        driver.execute_script('''
            document.querySelector("body > div > div > div.css-15re2pk > form > div > div.css-gmiyr0 > div:nth-child(1) > div > div > div > input").click()
            document.querySelector("body > div > div > div.css-15re2pk > form > div > div.css-gmiyr0 > div:nth-child(2) > div > div > div > input").click()
        ''')

        time.sleep(0.5)
        driver.find_element(By.XPATH, '/html/body/div/div/div[2]/form/div/div[6]/button').click()
        time.sleep(1)


options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
NUM_INSTANCES = 2

remaining = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70] # the ones that failed
accounts = [f'coresignal@mailroute{i}.ps99rap.com' for i in remaining]
threads = []

for i, chunk in enumerate([accounts[i::NUM_INSTANCES] for i in range(NUM_INSTANCES)]):
    thread = Thread(target=lambda: run_instance(chunk))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()