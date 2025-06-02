import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time

url = 'https://aemmedi.it/sezione/news/'

def aemmedi_news(driver):
    news_number = int(os.getenv('AEMMEID_NEWS_NUMBER', 5))
    driver.get(url)


    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,'main article h3 a'))
    )
    
    links = driver.find_elements(By.CSS_SELECTOR, 'main article h3 a')
    links = links[:news_number]

    results = []
    for link in links:
        href = link.get_attribute('href')
        title = link.text.strip()
        if href:
            results.append({'title': title,'link':href})

    for result in results:
        driver.get(result['link'])

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'main article p'))
        )
        paragraphs = driver.find_elements(By.CSS_SELECTOR, 'main article p')

        result['description'] = ''
        for paragraph in paragraphs:
            result['description'] += paragraph.text.strip() + '\n'
        # print(f"Processed article: {result['title']}")
        # print(f"Description: {result['description'][:9999]}...")  # Print first 100 characters of description
        # exit()

    return {'source':f'{url}','articles':results}