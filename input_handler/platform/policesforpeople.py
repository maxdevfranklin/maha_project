from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.common.by import By  
import json  
from selenium import webdriver  
from datetime import datetime, timedelta  

# Inputs  
url = "https://freevoicemedianewsletter.beehiiv.com/archive?page=1"  
days_old = 10  
cutoff_date = datetime.now() - timedelta(days=days_old)  

# Setup headless ChromeDriver  
options = webdriver.ChromeOptions()  
options.add_argument('--headless')  
driver = webdriver.Chrome(options=options)  

extracted_data = []  

# Function to extract data from a page using WebDriverWait  
def extract_data(driver):  
    try:  
        page_data = []  
        # Wait for the elements to be present on the page  
        WebDriverWait(driver, 10).until(  
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.transparent"))  
        )  
        elements = driver.find_elements(By.CSS_SELECTOR, "div.transparent")  
        for element in elements:  
            img_url = element.find_element(By.CSS_SELECTOR, "img").get_attribute('src')  
            time_elem = element.find_element(By.CSS_SELECTOR, "time")  
            publication_date = datetime.fromisoformat(time_elem.get_attribute('datetime').replace('Z', '+00:00'))  
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
    except Exception as e:  
        print(str(e))  
        return None, True  
    return page_data, False  

# Start extracting data from pages  
page_num = 1  
finished = False  

while not finished:  
    driver.get(url)  
    data, finished = extract_data(driver)  
    if data:  
        extracted_data.extend(data)  
    if not finished:  
        page_num += 1  
        url = f"https://freevoicemedianewsletter.beehiiv.com/archive?page={page_num}"  
    else:  
        break  

driver.quit()  

# Save extracted data to JSON file  
json_filename = 'data_extracted.json'  
with open(json_filename, 'w') as json_file:  
    json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)  

print(f"Data saved to {json_filename}")