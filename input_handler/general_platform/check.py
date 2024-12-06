import json  
import os  
import time  
import openai
import sys

from loguru import logger
from urllib.parse import urlparse
from datetime import datetime, timedelta  
from dateutil.relativedelta import relativedelta  
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from webdriver_manager.chrome import ChromeDriverManager  

logger.configure(handlers=[{  
    "sink": sys.stdout,   # Output to console  
    "format": "<yellow>{time:YYYY-MM-DD HH:mm:ss}</yellow> | "  
              "<level>{level}</level> | "  
              "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "  
              "<yellow>{message}</yellow>",  # Make the message yellow  
    "colorize": True   # Enable ANSI color codes  
}])  

def setup_driver():
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

def get_domain_from_url(url) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")

    return domain

def parse_html(post_html):
    openai.api_key = os.getenv('OPENAI_API_KEY')  

    with open("prompt/parse_html.txt", "r") as file:  
        parse_html_prompt = file.read()

    with open("log.txt", "a") as f:
        f.write("\n************************************str(post_html)\n************************************\n")

    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-11-20",
        messages=[
            {
                "role": "system", 
                "content": f"""{parse_html_prompt}"""
            },
            {
                "role": "user", 
                "content": f"target_html_contents - \n\n {str(post_html)}"
            }
        ],
        response_format={  
            "type": "json_schema",  
            "json_schema": {  
                "name": "json_schema",  
                "schema": {  
                    "type": "object",  
                    "properties": {  
                        "article_title": {  
                            "type": "string"  
                        },  
                        "article_url": {  
                            "type": "string"  
                        },  
                        "article_image_url": {  
                            "type": "string"  
                        },  
                        "short_article_description": {  
                            "type": "string"  
                        },  
                        "article_age": {  
                            "type": "string"  
                        }  
                    },  
                    "required": [  
                        "article_title",  
                        "article_url",  
                        "article_image_url",  
                        "short_article_description",  
                        "article_age"  
                        ]  
                }  
            }  
        }
    )
    article_data = json.loads(response.choices[0].message.content)
    return article_data

def parse_post_date(date_string):
    openai.api_key = os.getenv("OPENAI_API_KEY")  
    
    with open("prompt/parse_date.txt", "r") as file:  
        parse_date_prompt = file.read()

    with open("prompt/parse_old.txt", "r") as file:  
        parse_old_prompt = file.read()

    response = openai.ChatCompletion.create(  
        model="gpt-4o-2024-11-20",  # Ensure that we are using the correct model  
        messages=[  
            {  
                "role": "system",  
                "content": f"""{parse_date_prompt}"""  
            },  
            {  
                "role": "user",  
                "content": f"target_date_string:\n\n{str(date_string)}"  
            }  
        ]  
    )  

    # Extract the plain string response  
    response_string = response['choices'][0]['message']['content'].strip() 
    if response_string != '""':
        logger.info("We are here")
        return response_string
    
    response = openai.ChatCompletion.create(  
        model="gpt-4o-2024-11-20",  
        messages=[  
            {  
                "role": "system",  
                "content": f"""{parse_old_prompt}"""  
            },  
            {  
                "role": "user",  
                "content": f"target_date_string: \n\n{str(date_string)}"  
            }
        ],
        response_format={  
            "type": "json_schema",  
            "json_schema": {  
                "name": "json_schema",  
                "schema": {  
                    "type": "object",  
                    "properties": {  
                        "year": {  
                            "type": "integer"  
                        },  
                        "month": {  
                            "type": "integer"  
                        },  
                        "day": {  
                            "type": "integer"  
                        },  
                        "hour": {  
                            "type": "integer"  
                        }
                    },  
                    "required": [  
                        "year",  
                        "month",  
                        "day",  
                        "hour",  
                        ]  
                }  
            }  
        }    
    )

    age_dict = json.loads(response.choices[0].message.content)
    # logger.info(f"age_dict - {age_dict}")
    if age_dict:
        year = age_dict.get("year", 0) or 0  
        month = age_dict.get("month", 0) or 0  
        day = age_dict.get("day", 0) or 0  
        hour = age_dict.get("hour", 0) or 0  

        # Calculate the older date  
        current_date = datetime.now()  
        older_date = current_date - relativedelta(years=year, months=month)  
        older_date -= timedelta(days=day, hours=hour)  
        return older_date.strftime("%Y-%m-%d")  
    
    return ""

def add_article(article_list, article_data):  
    article_title = article_data.get("article_title", "")  # Use .get() to prevent KeyError  
    if not article_title:  
        logger.error("Invalid article_data: Missing 'article_title'")  
        return  # Exit if no valid title  

    for i, article in enumerate(article_list):  
        # Find if there's already an article with the same title  
        if article_title == article.get("article_title", ""):  
            # Count non-empty values for comparison  
            non_empty_count_first = sum(1 for value in article.values() if value)  
            non_empty_count_second = sum(1 for value in article_data.values() if value)  
            
            # Replace the article if the new one has more non-empty values  
            if non_empty_count_second > non_empty_count_first:  
                article_age = parse_post_date(article_data["article_age"])
                article_data["article_age"] = article_age 
                article_list[i] = article_data  # Replace in place  
                logger.info("Replaced previous article")
                print(f"{article_data}\n")
            return  # Exit after processing the matching article  

    # If no matching article, append the new one  
    # logger.info(f"article_data['article_age'] - {article_data['article_age']}")
    article_age = parse_post_date(article_data["article_age"])
    article_data["article_age"] = article_age 
    article_list.append(article_data)

    logger.info("New article")
    print(f"{article_data}\n")
    
def get_one_article_data(element, url_domain):
    article_data = []
    count = 0
    while True:
        if count == 5:
            break            
        post_html = element.get_attribute("outerHTML")  
        article_data = parse_html(post_html)
        if article_data["article_url"] and article_data["article_title"]:
            image_extensions = (  
                "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "svg", "webp", "ico",  
                "jfif", "pjpeg", "pjp", "avif", "heif", "heic", "raw", "cr2", "nef", "orf",  
                "sr2", "arw", "dng", "rw2", "pef", "raf", "3fr", "eip", "mrw", "nrw",  
                "x3f", "webp2"  
            )  

            # Check if the URL ends with any of the extensions  
            if not article_data["article_image_url"].lower().endswith(image_extensions):  # `.lower()` to make case-insensitive  
                article_data["article_image_url"] = ""            

            article_data["article_url"] = article_data["article_url"].replace("www.example.com", url_domain)
            article_data["article_url"] = article_data["article_url"].replace("example.com", url_domain)
            article_data["article_image_url"] = article_data["article_image_url"].replace("www.example.com", url_domain)
            article_data["article_image_url"] = article_data["article_image_url"].replace("example.com", url_domain)

            if not article_data["article_url"].startswith("https"):
                article_data["article_url"] = "https://" + url_domain + article_data["article_url"]
            

            if not article_data["article_image_url"].startswith("https"):
                article_data["article_image_url"] = "https://" + url_domain + article_data["article_image_url"] 

            break
        else:
            article_data = []
            element = element.find_element(By.XPATH, './..') 
            with open("log.txt", "a") as f:
                f.write(f"\nDidn't found, dive deep one level more- {count}\n")
            count += 1
            continue
    
    return article_data

def get_article_data(driver, url):  
    article_list = []
    driver.get(url)  
    url_domain = get_domain_from_url(url)

    print(url_domain)
    logger.info(f"Checking structure of {url}")  
    time.sleep(10)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")  

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
        {"name": "page-excerpt format", "type": "css",   
         "selector": "div.page-excerpt"},  
        {"name": "status__wrapper format", "type": "css",   
         "selector": "div.status__wrapper"},  
        {"name": "transparent format", "type": "css",   
         "selector": "div.transparent"}, 
        {"name": "headline link format", "type": "xpath",   
         "selector": "//li/a[contains(@class, 'headline-link')]"}
    ]  

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
                    article_data = get_one_article_data(element, url_domain) 
                    if article_data: 
                        add_article(article_list, article_data)

        except Exception as e:  
            logger.error(f"Error processing {structure['name']}: {e}")  
            continue  
    
    if len(article_list) > 0:
        logger.info("Started saving data to json file")
        with open(f"{url_domain}.json", 'w') as json_file:  
            json.dump(article_list, json_file, indent=4) 
        logger.info("Successfully saved data to json file")
    else:
        logger.info("No data to save")
    driver.quit()

def main():
    urls = [  
        # "https://citizenfreepress.com/",
        # "https://forum.policiesforpeople.com/c/health/5?ascending=false&order=created"
        "https://forum.policiesforpeople.com/c/health/5?ascending=false&order=created",
        # "https://www.foodscience.news/",
        # "https://www.naturalmedicine.news/"
        # "https://thetruthaboutcancer.com/category/cancer-causes/" (Bunch of thetruthaboutcancer)
        # "https://thelibertydaily.com/"
        # "https://vigilantnews.com/post/category/health/"
        # "https://vigilantnews.com/post/category/news/"
        # "https://vigilantnews.com/post/category/opinion/",
        # "https://resistthemainstream.com/category/media-watch/",
        # "https://depopulation.news/",
        # "https://www.theamericanconservative.com/"
        # "https://truthsocial.com/@ResisttheMainstream"
        # "https://foodbabe.com/blog/",
        # "https://nopharmfilm.com/blog",
        # "https://freevoicemedianewsletter.beehiiv.com/"
        # "https://kirschsubstack.com/archive"
        # "https://drhyman.com/blogs/content"
        # "https://childrenshealthdefense.org/defender-news/"
        # "https://revolver.news/"
        # "https://www.actforamerica.org/in-the-news"
        # "https://100percentfedup.com/",
        # "https://reformpharmanow.org/substack/",
        # "https://www.momsacrossamerica.com/blog"
        # "https://citizenfreepress.com/"
    ]
    
    for url in urls:
        driver = setup_driver()
        get_article_data(driver, url)

if __name__ == "__main__":
    with open("log.txt", "w") as f:
        f.write("Started Development")
    main()