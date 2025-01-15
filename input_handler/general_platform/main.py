import time  
import sys
import json  
import logging
import os

from loguru import logger
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  

from db import insert_article
from parse_utils import (  
    clean_article_url,  
    get_domain_from_url,
    parse_html,  
    parse_post_date,  
    calculate_days_behind,  
)


file = open("program_log.log", "w")  
logger.configure(handlers=[{  
    "sink": sys.stdout,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
},
{  
    "sink": file,  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
            "<level>{level}</level> | "  
            "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
            "<yellow>{message}</yellow>",  
    "colorize": True   
}])  

class Generalscrapper():
    def setup_driver(self):
        chrome_options = webdriver.ChromeOptions()  
        chrome_options.add_argument('--headless')  # Run in headless mode (no browser window)  
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36')  
        chrome_options.add_argument('--disable-popup-blocking')  # Disable popup blocks  
        chrome_options.add_argument('--disable-background-timer-throttling')  # Disable background throttling  
        chrome_options.add_argument('--disable-infobars')  # Disable info bars in the UI (e.g., "Chrome is being controlled...")  
        chrome_options.add_argument('--ignore-gpu-blacklist')  # Force enabling GPU even if unsupported by default  
        chrome_options.add_argument('--no-sandbox')  # Bypass OS security model (needed in some environments)  
        chrome_options.add_argument('--disable-dev-shm-usage')  # Prevent crashes due to limited /dev/shm  
        chrome_options.add_argument('--disable-gpu')  # Disable GPU (needed for some rendering issues in headless mode)  
        chrome_options.add_argument('--window-size=1920,1080')  # Set browser window size (needed for responsive web pages)  
        chrome_options.add_argument('--start-maximized')  # Ensure full content is visible  
        chrome_options.add_argument('--disable-extensions')  # Disable extensions for stability  
        chrome_options.add_argument('--page-load-timeout=300')
        chrome_options.add_argument('--script-timeout=300')
        
        webdriver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    
        # Set explicit timeouts
        driver.set_page_load_timeout(300)
        driver.set_script_timeout(300)
        
        return driver

    def get_one_article_data(self, element, url_domain, filename):
        article_data = []
        upper_trying_count = 0
        while True:
            if upper_trying_count == 5:
                logger.info("Tried 5 times to upper level. But couldn't find actual article")
                break            
            post_html = element.get_attribute("outerHTML")  
            article_data = parse_html(post_html)
            if article_data["article_url"] and article_data["article_title"]:
                # logger.info("Found actual article_information")
                article_data["article_url"], article_data["article_image_url"] = clean_article_url(article_data["article_url"], article_data["article_image_url"], url_domain)
                article_data["date"] = filename
                break
            else:
                article_data = []
                element = element.find_element(By.XPATH, './..') 
                with open("log.txt", "a") as f:
                    f.write(f"\nDidn't found, dive deep one level more- {upper_trying_count}\n")
                upper_trying_count += 1
                continue
        
        return article_data

    def add_article(self, article_list, whole_article_list, article_data):  
        article_title = article_data.get("article_title", "")    
        if not article_title:  
            logger.error("Invalid article_data: Missing 'article_title'")  
            return 0
            
        for article in whole_article_list:  
            # Find if there's already an article with the same title  
            if article_title == article.get("article_title", ""):  
                logger.info("We found duplicating one. Checking which will be added.")
                # Count non-empty values for comparison  
                non_empty_count_first = sum(1 for value in article.values() if value)  
                non_empty_count_second = sum(1 for value in article_data.values() if value)  
                
                # Replace the article if the new one has more non-empty values  
                if non_empty_count_second > non_empty_count_first:
                    article_data["article_age"] = parse_post_date(article_data["article_age"])
                    article_list = [article_data if article["article_title"] == article_data["article_title"] else article for article in article_list]
                    logger.info("Replaced previous article")
                    print(f"{article_data}\n")
                    return 1
                else:
                    logger.info("Duplicated article\n")
                    return 0
                
        # If no matching article, append the new one  
        # logger.info(f"article_data['article_age'] - {article_data['article_age']}")
        article_data["article_age"] =  parse_post_date(article_data["article_age"]) 
        article_list.append(article_data)

        logger.info("New article")
        print(f"{article_data}\n")
        return 1

    def get_article_data_from_one_page(self, driver, url, days_behind, whole_article_list, view_type, filename): 
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Attempt {retry_count + 1} to load page {url}")
                # if view_type != "scroll":
                driver.get(url)
                url_domain = get_domain_from_url(url)
                time.sleep(2)
                
                driver.execute_script("return document.body.scrollHeight")
                logger.info(f"before driver get")
                days_behind_count = 0
                article_list = []

                logger.info(f"Our main domain is - {url_domain}")
                logger.info(f"Checking structure of {url}")  

                if not self.exception_list:
                    # Define all the potential structures in a list (XPath and CSS selectors)  
                    structures = [  
                        {"name": "post format", "type": "xpath",   
                        "selector": '//div[contains(@class, "post") and not(.//div[contains(@class, "post")])]'},  
                        {"name": "capitalized post format", "type": "xpath",   
                        "selector": '//div[contains(@class, "Post") and not(.//div[contains(@class, "Post")])]'},  
                        {"name": "article format", "type": "xpath",   
                        "selector": '//article[not(.//article)]'},  
                        {"name": "blog format", "type": "xpath",   
                        "selector": '//div[contains(@class, "blog") and not(.//div[contains(@class, "blog")])]'},  
                        {"name": "topic-list-item", "type": "xpath",
                        "selector": "//tr[contains(@class, 'topic-list-item')]"},
                        {"name": "drudgery-link format", "type": "xpath",   
                        "selector": "//div[@class='drudgery-link']/a"},     
                        {"name": "videostream thumbnail__grid--item format", "type": "xpath",   
                        "selector": "//div[contains(@class, 'videostream thumbnail__grid--item')]"},
                        {"name": "tmb enhanced-atc format", "type": "xpath",   
                        "selector": "//div[contains(@class, 'tmb enhanced-atc')]"},
                        {"name": "page-excerpt format", "type": "css",   
                        "selector": "div.page-excerpt"},  
                        {"name": "status__wrapper format", "type": "css",   
                        "selector": "div.status__wrapper"},  
                        {"name": "transparent format", "type": "css",   
                        "selector": "div.transparent"}, 
                        {"name": "headline link format", "type": "xpath",   
                        "selector": "//li/a[contains(@class, 'headline-link')]"}
                    ]  
                else:
                    logger.info(f"{url} is is exceptional_case!")
                    structures = [{"name": self.exception_list[0], "type": self.exception_list[1], "selector": self.exception_list[2]}]
                
                # Process each structure type in sequence  
                for structure in structures:  
                # try:  
                    # Find elements based on the type (XPath or CSS selector)  
                    if structure["type"] == "xpath":  
                        elements = driver.find_elements(By.XPATH, structure["selector"])  
                    elif structure["type"] == "css":  
                        elements = driver.find_elements(By.CSS_SELECTOR, structure["selector"])  
                    
                    # If elements are found, process them  
                    if elements:  
                        logger.info(f"The structure is {structure['name']}")  
                        logger.info(f"len(elements): {len(elements)}")  

                        # Iterate over all elements and process data extraction  
                        for element in elements:  
                            article_data = self.get_one_article_data(element, url_domain, filename) 
                            if article_data: 
                                # logger.info(f"article_data: {article_data}")
                                if self.add_article(article_list, whole_article_list, article_data) == 1:
                                    if article_data["article_age"] != "":
                                        if calculate_days_behind(article_data["article_age"]) > days_behind:
                                            days_behind_count += 1
                                            if days_behind_count > 5:
                                                return article_list, days_behind_count
                                        else:
                                            days_behind_count = 0
                                
                    # except Exception as e:  
                    #     logger.error(f"Error processing {structure['name']}: {e}")  
                    #     continue  
                
                if len(article_list) > 0:
                    logger.info(f"Successfully extract {len(article_list)} data in one page")
                else:
                    logger.info(f"No data to extract - {url}")
            
                return article_list, days_behind_count
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"Attempt {retry_count} failed: {e}")
                if retry_count == max_retries:
                    logger.error("Max retries reached")
                    return [], 0
                time.sleep(5)

    def get_whole_article_data(self, driver, url, view_type, filename, days_behind, ):
        base_url = url
        whole_article = []
        page_num = 1
        if view_type == "page1":
            while True:
                url = f"{base_url}?page={page_num}/"
                driver.delete_all_cookies()
                time.sleep(2)
                article_list, days_behind_count = self.get_article_data_from_one_page(driver, url, days_behind, whole_article, view_type, filename)
                whole_article.extend(article_list)
                logger.info(f"We have {len(whole_article)} articles in total================================================")
                if len(article_list) == 0:
                    logger.info("No data on this page.")
                    break
                if days_behind_count > 5:
                    logger.info("More than 5 articles exceeds days limit. Stop searching and choice is set as page\n")
                    break
                page_num += 1
                logger.info(url)
            # except Exception as e:
            #     logger.error(f"An error occurred in page type 1: {e}")
            
        
        
        logger.info(f"Finally we have {len(whole_article)} articles")  

        behind_article_count = 0  
        all_articles = []  # A new list for valid (not deleted) articles  

        for article in whole_article:  
            # article_age = article["article_age"]  
            # if calculate_days_behind(article_age) > days_behind:  
            #     logger.info(article_age)  
            #     behind_article_count += 1  
            # else:  
            #     logger.info(f'not {article_age}')  
            all_articles.append(article)  # Add valid articles to the new list  

        logger.info(f"We have deleted {behind_article_count} articles. The total number of articles is {len(all_articles)}")
        driver.quit()
        print("driver quit")
        return all_articles
    
    def add_firebase(self, all_articles):
        for article_data in all_articles:
            insert_article(article_data["article_title"], article_data)
        pass

    def generate_url(self, base_url, page_type):
        year_month = base_url.rstrip('/')
        urls = []

        for day in range(1, 32):
            formatted_day = f"{day:02d}"
            daily_url = f"{year_month}/{formatted_day}"
            urls.append({
                "url": daily_url,
                "type": page_type
            })
        return urls
    
    def extract_date(self, url):
        parts = url.split('/')
        year = parts[-3]
        month = parts[-2].zfill(2)
        day = parts[-1].zfill(2)
        return f"{year}{month}{day}"

    def main(self):
        inputs = {"url": "https://www.wsj.com/news/archive/2024/10/", "type": "page1"}
            # {"url": "https://forum.policiesforpeople.com/c/health/5?ascending=false&order=created", "type": "scroll"},
            # {"url": "https://thetruthaboutcancer.com/category/cancer-treatments/", "type": "page1"},
            # {"url": "https://vigilantnews.com/post/category/health/", "type": "page1"},

            # {"url":"https://forum.policiesforpeople.com/c/food/6?ascending=false&order=created", "type": "scroll"}

            # {"url":"https://naturalnews.com/category/health/", "type":"page1"},

            # {"url": "https://www.foodscience.news/all-posts/", "type": "page1"},
        input_urls = self.generate_url(inputs["url"], inputs["type"])
        
        
        exception_dicts = {
            "thehighwire": ["videos__list-item format", "xpath", "//li[contains(@class, 'videos__list-item')]"],
            "actforamerica": ["tr format", "xpath", "//tr"]
        }

        os.makedirs('output', exist_ok=True)

        for input in input_urls:
            print(input)
            url = input["url"]
            filename = self.extract_date(url)
            view_type = input["type"]

            self.exception_list = []
            for key, value in exception_dicts.items():
                if key in input:
                    logger.info("URL is exceptional URL.")
                    self.exception_list = value
                    break
                    
            driver = self.setup_driver()
            whole_article_data = self.get_whole_article_data(driver, url, view_type, filename, days_behind=7,)
            url_domain = get_domain_from_url(url)
            # self.add_firebase(whole_article_data)
            record_number = []
            record_number.append(f"{filename}_{len(whole_article_data)}")
            print("file save")
            with open(f"output/{filename}.json", 'w', encoding='utf-8') as f:
                json.dump(whole_article_data, f, ensure_ascii=False, indent=4)
            with open(f"output/record/number.json", 'w', encoding='utf-8') as f:
                json.dump(record_number, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    general_scrapper = Generalscrapper()
    general_scrapper.main()