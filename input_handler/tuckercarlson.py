import json  
import os  
import time  
from datetime import datetime, timedelta  
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080') 
    
    webdriver_service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=webdriver_service, options=chrome_options)


def parse_posted_date(post_date_text):  
    """  
    Parse the posted date from text (e.g., "PUBLISHED 8 days ago") and return it in 'yyyy-mm-dd' format.  
    """  
    if "days ago" in post_date_text:  
        days_ago = int(post_date_text.split(" ")[1])  
        parsed_date = datetime.now() - timedelta(days=days_ago)  
    elif "yesterday" in post_date_text.lower():  # You can add other formats if needed  
        parsed_date = datetime.now() - timedelta(days=1)  
    else:  
        parsed_date = datetime.now()  # Assume "Today" or equivalent  

    return parsed_date.strftime('%Y-%m-%d')  


def extract_video_elements(driver, days_old):  
    """  
    Extract information from video elements that meet the date threshold.  
    """  
    videos = []  
    cutoff_date = datetime.now() - timedelta(days=days_old)  
    visited_urls = set()  

    while True:  
        # Locate all video elements on the current page  
        video_elements = driver.find_elements(By.CSS_SELECTOR, "div.video-card a[data-test-id='video-card']")  

        # Flag to determine if we should stop scrolling (no new matching videos found)  
        stop_scrolling = True  

        for video_element in video_elements:  
            # Extract key details  
            try:  
                title = video_element.find_element(By.CSS_SELECTOR, "h3").text.strip()  
                summary = video_element.find_element(By.CSS_SELECTOR, "p:nth-of-type(1)").text.strip()  
                posted_date_text = video_element.find_element(By.CSS_SELECTOR, "p:nth-of-type(2)").text.strip()  
                posted_date = parse_posted_date(posted_date_text)  
                url = video_element.get_attribute("href")  

                # Skip duplicates  
                if url in visited_urls:  
                    continue  

                visited_urls.add(url)  

                # Parse date and stop if date is older than cutoff  
                post_date_obj = datetime.strptime(posted_date, '%Y-%m-%d')  
                if post_date_obj < cutoff_date:  
                    continue  # Ignore older posts  

                # Save the video information  
                videos.append({  
                    'title': title,  
                    'summary': summary,  
                    'posted_date': posted_date,  
                    'url': url  
                })  
                stop_scrolling = False  # New matching result found, continue scrolling  

                print(f"Scraped Video: {title} | Date: {posted_date} | URL: {url}")  
            except Exception as e:  
                print(f"Error processing video element: {e}")  
                continue  

        # Scroll down to load more results if any new result is present  
        if stop_scrolling:  
            print("No new elements matching criteria found, stopping scroll.")  
            break  

        scroll_height_before = driver.execute_script("return document.body.scrollHeight")  
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")  
        time.sleep(2)  # Wait for new elements to load  
        scroll_height_after = driver.execute_script("return document.body.scrollHeight")  

        # If no additional content is loaded, break out of scrolling  
        if scroll_height_after == scroll_height_before:  
            print("Reached the bottom of the page, stopping scroll.")  
            break  

    return videos  

def save_results_to_json(data):  
    """  
    Save scraped data to a JSON file named after the Python script.  
    """  
    script_name = os.path.splitext(os.path.basename(__file__))[0]  
    json_filename = f"{script_name}.json"  

    with open(json_filename, 'w', encoding='utf-8') as json_file:  
        json.dump(data, json_file, indent=4, ensure_ascii=False)  

    print(f"Data saved to file: {json_filename}")  


def main():  
    """  
    Main workflow to scrape the website.  
    """  
    # Inputs  
    url = "https://tuckercarlson.com/explore"  
    days_old = 10  # Change to the desired threshold in days  

    # Set up the Selenium WebDriver  
    # driver = setup_driver()  

    # Configure headless mode for the Chrome browser  
    chrome_options = webdriver.ChromeOptions()  
    # chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--start-fullscreen")  # Launch the browser in full-screen mode  

    service = Service(ChromeDriverManager().install())  
    # Set up the Chrome driver  
    driver = webdriver.Chrome(service=service, options=chrome_options)  
    try:  
        # Open the webpage  
        print(f"Visiting URL: {url}")  
        driver.get(url)  

        # Wait for the page's contents to load completely  
        WebDriverWait(driver, 20).until(  
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.video-card"))  
        )  
        time.sleep(15)
        # Extract video elements information  
        videos = extract_video_elements(driver, days_old)  

        # Save results to JSON  
        save_results_to_json(videos)  

    except Exception as e:  
        print(f"An error occurred: {e}")  
    finally:  
        # Always quit WebDriver  
        driver.quit()  


if __name__ == "__main__":  
    main()