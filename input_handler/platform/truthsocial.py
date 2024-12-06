import json  
import os  
import time  
from datetime import datetime, timedelta, timezone  
from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from selenium.common.exceptions import NoSuchElementException, TimeoutException  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  

def init_browser(headless=True):  
    options = Options()  
    if headless:  
        options.add_argument("--headless")  
        options.add_argument("--window-size=1920,1080")  
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36')  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service)  

    if headless:  
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  

    return driver  

def scrape_posts(driver, url, days_old=5):  
    driver.get(url)  
    time_threshold = datetime.now(timezone.utc) - timedelta(days=days_old)  
    data = []  

    try:  
        last_height = driver.execute_script("return document.body.scrollHeight")  
        while True:  
            try:  
                WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.status__wrapper')))  
            except TimeoutException:  
                print("Timed out waiting for posts to load.")  
                break  

            posts = driver.find_elements(By.CSS_SELECTOR, 'div.status__wrapper')
            print(len(posts))  
            for post in posts:  
                try:  
                    timestamp = post.find_element(By.CSS_SELECTOR, 'time').get_attribute('title')  
                    parsed_date = datetime.strptime(timestamp, '%b %d, %Y, %I:%M %p').replace(tzinfo=timezone.utc)  

                    if parsed_date < time_threshold:  
                        raise StopIteration  

                    article_url = post.find_element(By.CSS_SELECTOR, 'a.status-link').get_attribute('href')  
                    image_url = post.find_element(By.CSS_SELECTOR, 'div.status-card__image-image').get_attribute('style').split('"')[1]  
                    title = post.find_element(By.CSS_SELECTOR, 'div.status__content-wrapper p').text  
                    replies = post.find_element(By.CSS_SELECTOR, 'button[title="Reply"] span').text  
                    retweets = post.find_element(By.CSS_SELECTOR, 'button[title="ReTruth"] span').text  
                    likes = post.find_element(By.CSS_SELECTOR, 'button[title="Like"] span').text  

                    data.append({  
                        'date': parsed_date.isoformat(),  
                        'article_url': article_url,  
                        'image_url': image_url,  
                        'title': title,  
                        'replies': replies,  
                        'retweets': retweets,  
                        'likes': likes,  
                    })  
                except NoSuchElementException:  
                    continue  
                except ValueError:  
                    print("Error parsing the date of a post.")  
                    continue  

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
            time.sleep(1)  
            new_height = driver.execute_script("return document.body.scrollHeight")  
            if new_height == last_height:  
                break  
            last_height = new_height  

    except StopIteration:  
        print("Fetched all recent posts up to the specified 'days_old'.")  

    return data  

if __name__ == "__main__":  
    url = 'https://truthsocial.com/@RTMnews'  
    days_old = 5  

    driver = init_browser(headless=True)  
    try:  
        data = scrape_posts(driver, url, days_old)  
        script_name = os.path.splitext(os.path.basename(__file__))[0]  
        with open(f"{script_name}.json", 'w', encoding='utf-8') as f:  
            json.dump(data, f, ensure_ascii=False, indent=4)  
        print(f"Data saved to {script_name}.json")  
    finally:  
        driver.quit()