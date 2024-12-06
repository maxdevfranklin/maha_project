from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from datetime import datetime, timedelta  
import json
import os
import pytz  

# Inputs  
url = "https://freevoicemedianewsletter.beehiiv.com/archive?page=1"  
days_old = 20  

cutoff_date = datetime.now() -timedelta(days=days_old)
cutoff_date = cutoff_date.date()

# Setup headless ChromeDriver  
options = webdriver.ChromeOptions()  
options.add_argument('--headless')  
driver = webdriver.Chrome(options=options)  

extracted_data = []  

# Function to extract data from a page using WebDriverWait  
def extract_data(driver):  
    # Wait for the elements to be present on the page  
    WebDriverWait(driver, 10).until(  
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.transparent"))  
    )  
    elements = driver.find_elements(By.CSS_SELECTOR, "div.transparent")  
    page_data = []  
    for element in elements:  
        img_url = element.find_element(By.CSS_SELECTOR, "img").get_attribute('src')  
        time_elem = element.find_element(By.CSS_SELECTOR, "time")  
        publication_date_str = time_elem.get_attribute('datetime').rstrip('Z')  
        publication_date = datetime.fromisoformat(publication_date_str)  
        publication_date = publication_date.replace(tzinfo=pytz.utc) 
        publication_date = publication_date.date()

        if publication_date < cutoff_date:  
            return None, True  

        article_url = element.find_element(By.CSS_SELECTOR, "a[href*='/p/']").get_attribute('href')  
        title = element.find_element(By.CSS_SELECTOR, "h2").text  

        page_data.append({  
            "image_url": img_url,  
            "publication_date": publication_date.isoformat(),  
            "article_url": article_url,  
            "title": title  
        })  
    return page_data, False  
    # except Exception as e:  
    #     print(str(e))  
    #     return None, True  

# Start extracting data from pages  
page_num = 1  
finished = False  

while not finished:  
    driver.get(url)  
    data, is_finished = extract_data(driver)  
    if data:  
        extracted_data.extend(data)  
    if not is_finished:  
        page_num += 1  
        url = f"https://freevoicemedianewsletter.beehiiv.com/archive?page={page_num}"  
    else:  
        break  

driver.quit()  

# Save extracted data to JSON file  
script_name = os.path.basename(__file__)  
json_filename = script_name.replace('.py', '.json')  
with open(json_filename, 'w') as json_file:  
    json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)  

print(f"Data saved to {json_filename}")