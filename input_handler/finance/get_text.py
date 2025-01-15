from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random

def extract_article_body(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # Find the article schema script tag
    schema_tag = soup.find('script', {'id': 'articleschema'})
    if schema_tag:
        # Parse the JSON content
        import json
        schema_data = json.loads(schema_tag.string)
        
        # Navigate to articleBody in the liveBlogUpdate array
        if isinstance(schema_data, list) and len(schema_data) > 0:
            live_blog_updates = schema_data[0].get('liveBlogUpdate', [])
            if live_blog_updates:
                article_body = live_blog_updates[0].get('articleBody', '')
                return article_body
    
    return "Article body not found"

def scroll_full_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def scrape_wsj_article():
    options = webdriver.ChromeOptions()
    
    # Add SSL error handling options
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--disable-web-security')
    
    # Keep existing anti-detection measures
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver = webdriver.Chrome(options=options)

    try:
        # driver.get('https://www.wsj.com/login')
        print("Please login manually and solve any security checks. You have 5 minutes.")
        time.sleep(20)
        
        # Rest of your code remains the same
        driver.get('https://www.wsj.com/livecoverage/stock-market-today-dow-sp500-nasdaq-live-01-13-2025/card/abercrombie-stock-falls-despite-strong-holiday-sales-cQ9hMn9YsmK06lf4ha37')
        

        # WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

        print("start sleep")

        time.sleep(5)

        print("start full page scraping")

        scroll_full_page(driver)

        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        # )
        
        # soup = BeautifulSoup(driver.page_source, 'html.parser')
        # article = soup.find('article')
        # title = article.find('h2').text if article.find('h2') else "No title found"
        # content = article.find('div', {'data-type': 'article-body'}).text if article.find('div', {'data-type': 'article-body'}) else "No content found"
        
        # print("Title:", title)
        # print("\nContent:", content)
        print(driver.page_source)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_wsj_article()
