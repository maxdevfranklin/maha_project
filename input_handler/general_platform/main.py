import time  
import sys
import json  

from loguru import logger
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  

from parse_utils import (  
    clean_article_url,  
    get_domain_from_url,
    parse_html,  
    parse_post_date,  
    calculate_days_behind,  
    check_url_status,   
)

logger.configure(handlers=[{  
    "sink": sys.stdout,  
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
        
        webdriver_service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=webdriver_service, options = chrome_options)

    def get_one_article_data(self, element, url_domain):
        article_data = []
        count = 0
        while True:
            if count == 5:
                logger.info("Tried 5 times to upper level. But couldn't find actual article")
                break            
            post_html = element.get_attribute("outerHTML")  
            article_data = parse_html(post_html)
            if article_data["article_url"] and article_data["article_title"]:
                # logger.info("Found actual article_information")
                article_data["article_url"], article_data["article_image_url"] = clean_article_url(article_data["article_url"], article_data["article_image_url"], url_domain)
                break
            else:
                article_data = []
                element = element.find_element(By.XPATH, './..') 
                with open("log.txt", "a") as f:
                    f.write(f"\nDidn't found, dive deep one level more- {count}\n")
                count += 1
                continue
        
        return article_data

    def get_article_data_from_one_page(self, driver, url, exception_list, days_behind):  
        days_behind_count = 0
        article_list = []
        driver.get(url)  
        url_domain = get_domain_from_url(url)

        logger.info(f"Our main domain is - {url_domain}")
        logger.info(f"Checking structure of {url}")  
        time.sleep(10)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")  

        if not exception_list:
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
            structures = [{"name": exception_list[0], "type": exception_list[1], "selector": exception_list[2]}]
        
        # Process each structure type in sequence  
        for structure in structures:  
            try:  
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
                        article_data = self.get_one_article_data(element, url_domain) 
                        if article_data: 
                            # logger.info(f"article_data: {article_data}")
                            if self.add_article(article_list, article_data) == 1:
                                if calculate_days_behind(article_data["article_age"]) > days_behind:
                                    days_behind_count += 1
                                    if days_behind_count > 5:
                                        return article_list, days_behind_count
                                else: 
                                    days_behind_count = 0
                        
            except Exception as e:  
                logger.error(f"Error processing {structure['name']}: {e}")  
                continue  
        
        if len(article_list) > 0:
            logger.info("Started saving data to json file")
            with open(f"output/{url_domain}.json", 'w') as json_file:  
                json.dump(article_list, json_file, indent=4) 
            logger.info("Successfully saved data to json file")
        else:
            logger.info("No data to save")
    
        return article_list, days_behind_count

    def add_article(self, article_list, article_data):  
        article_title = article_data.get("article_title", "")    
        if not article_title:  
            logger.error("Invalid article_data: Missing 'article_title'")  
            return 0
            
        for i, article in enumerate(article_list):  
            # Find if there's already an article with the same title  
            if article_title == article.get("article_title", ""):  
                logger.info("We found duplicating one. Checking which will be added.")
                # Count non-empty values for comparison  
                non_empty_count_first = sum(1 for value in article.values() if value)  
                non_empty_count_second = sum(1 for value in article_data.values() if value)  
                
                # Replace the article if the new one has more non-empty values  
                if non_empty_count_second >= non_empty_count_first:  
                    article_data["article_age"] = parse_post_date(article_data["article_age"])
                    article_list[i] = article_data
                    logger.info("Replaced previous article")
                    print(f"{article_data}\n")
                    return 1
                else:
                    logger.info("\nDuplicated article")
                    return 0
                
        # If no matching article, append the new one  
        # logger.info(f"article_data['article_age'] - {article_data['article_age']}")
        article_data["article_age"] =  parse_post_date(article_data["article_age"]) 
        article_list.append(article_data)

        logger.info("New article")
        print(f"{article_data}\n")
        return 1

    def get_whole_article_data(self, driver, url, exception_list, days_behind):
        whole_article = []
        choice = "none"
        try:
            page = 1
            while True:
                article_list, days_behind_count = self.get_article_data_from_one_page(driver, url, exception_list, days_behind)
                if days_behind_count > 5:
                    choice = "page"
                    logger.info("\n We have more than 5 articles exceeds days limit. Choice is set as page")
                    break
                whole_article.extend(article_list)
                page += 1
                url = f"{url}/page/{page}/"
                if check_url_status(url) == 0:
                    url = f"{url}?page={page}/"
                    if check_url_status(url) == 0:
                        break
                choice = "page"
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        
        if choice == "page":
            return whole_article
        
        try:  
            # Get the initial page height  
            last_height = driver.execute_script("return document.body.scrollHeight")  
            
            while True:  
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  
                time.sleep(5)  # Adjust this value based on the site's load time  
                
                # Extract articles from the current page  
                article_list, days_behind_count = self.get_article_data_from_one_page(driver, url, exception_list)  
                if days_behind_count > 5:
                    choice = "scroll"
                    logger.info("\n We have more than 5 articles exceeds days limit. Choice is set as scroll")
                    break
                
                new_articles = []  
                for article in article_list:  
                    if article['id'] not in [a['id'] for a in whole_article]:  
                        new_articles.append(article)  
                
                whole_article.extend(new_articles)  
                
                new_height = driver.execute_script("return document.body.scrollHeight")  
                if new_height == last_height:  
                    print("Reached the end of the page or no new content loaded.")  
                    break  
                
                last_height = new_height  # Update last height for the next iteration   
        except Exception as e:  
            logger.error(f"An error occurred: {e}")  
        
        if choice == "scroll":
            return whole_article
        logger.info("\n We have no choice to get more data!")
        driver.quit()
    
    def main(self):
        urls = [  
            "https://www.actforamerica.org/in-the-news"
        ]
        
        exception_dicts = {
            "thehighwire": ["videos__list-item format", "xpath", "//li[contains(@class, 'videos__list-item')]"],
            "actforamerica": ["tr format", "xpath", "//tr"]
        }
        
        for url in urls:
            exception_list = []
            for key, value in exception_dicts.items():
                if key in url:
                    logger.info("URL is exceptional URL.")
                    exception_list = value
                    break
                    
            driver = self.setup_driver()
            self.get_whole_article_data(driver, url, exception_list, days_behind=7)

if __name__ == "__main__":
    general_scrapper = Generalscrapper()
    general_scrapper.main()