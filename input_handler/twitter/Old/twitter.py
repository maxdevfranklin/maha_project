from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from datetime import datetime, timedelta
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080') 
    
    webdriver_service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=webdriver_service, options=chrome_options)

def wait_for_posts(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//article[@role="article"]'))
        )
        return True
    except:
        return False

def get_last_post_timestamp(posts):
    """Get timestamp of the last visible post"""
    try:
        last_post = posts[-1]
        timestamp_str = last_post.find_element(By.XPATH, './/time').get_attribute('datetime')
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        return None

def extract_post_data(driver, profile_url, days_limit):
    print(f"Scraping profile: {profile_url}")
    driver.get(profile_url)
    
    if not wait_for_posts(driver):
        print(f"Failed to load posts for {profile_url}")
        return []

    posts_data = set()  
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")  
        while True:
            posts = driver.find_elements(By.XPATH, '//article[@role="article"]')

            # if len(posts) == last_posts_count:
            #     no_new_posts_count += 1
            #     if no_new_posts_count >= 3: 
            #         driver.refresh()
            #         wait_for_posts(driver)
            #         no_new_posts_count = 0
            #         continue
            # else:
            #     no_new_posts_count = 0

            # last_posts_count = len(posts)
            
            for post in posts:
                try:
                    timestamp_str = post.find_element(By.XPATH, './/time').get_attribute('datetime')
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    publication_date = timestamp.date()
                    
                    if datetime.now(tz=timestamp.tzinfo) - timestamp > timedelta(days=days_limit):
                        continue
                    
                    text_content = post.find_element(By.XPATH, './/div[@lang]').text
                    post_url = post.find_element(By.XPATH, './/a[contains(@href, "/status/")]').get_attribute('href')
                    
                    urls_in_post = post.find_elements(By.XPATH, './/a[contains(@href, "http")]')
                    urls_in_post = [url.get_attribute('href') for url in urls_in_post 
                                if not url.get_attribute('href').startswith(('https://twitter.com/', 'https://x.com/'))]
                    urls_in_post_str = ", ".join(urls_in_post)

                    post_data = {
                        "ProfileURL": profile_url,
                        "Text": text_content,
                        "Timestamp": publication_date.isoformat(),
                        "PostURL": post_url,
                        "URLsInPost": urls_in_post_str
                    }
                    
                    posts_data.add(tuple(post_data.items()))
                    
                except Exception as e:
                    print(f"Error processing post: {str(e)}")
                    continue
            
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
            time.sleep(1)  
            new_height = driver.execute_script("return document.body.scrollHeight")  
            if new_height == last_height:  
                break  
            last_height = new_height  

    except StopIteration:  
        print("Fetched all recent posts up to the specified 'days_old'.")  
    
    print(f"Scraped {len(posts_data)} posts from {profile_url}.")
    return [dict(post_data) for post_data in posts_data]

def save_to_csv(all_post_data, output_filename='twitter_posts.csv'):
    if not all_post_data:
        print("No data to save")
        return
        
    keys = all_post_data[0].keys()
    with open(output_filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(all_post_data)
    print(f"Data saved to {output_filename}")

def main():
    profile_urls = [
        "https://x.com/ResisttheMS",
        "https://x.com/tpvsean",
        "https://x.com/kennedyforthew",
        "https://x.com/okhprbears",
        "https://x.com/GlobalHProject",
        "https://x.com/fluorideaction",
        "https://x.com/paulsaladinomd",
        "https://x.com/theinsiderpaper",
        "https://x.com/disclosetv",
        # "https://x.com/childrenshd",
        # "https://x.com/TuckerCarlson",
        "https://x.com/real1fisherman",
        # "https://x.com/Red_Pill_US",
        "https://x.com/redpillb0t",
        "https://x.com/MAGAResource",
        "https://x.com/jillianmichaels",
        "https://x.com/paulsaladinomd",
        "https://x.com/in2thinair"
    ]

    days_limit = 60
    
    driver = setup_driver()
    all_post_data = []
    
    try:
        for profile_url in profile_urls:
            profile_data = extract_post_data(driver, profile_url, days_limit)
            print(f"Collected {len(profile_data)} posts from {profile_url}")
            all_post_data.extend(profile_data)
            time.sleep(3) 
            
        save_to_csv(all_post_data)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()