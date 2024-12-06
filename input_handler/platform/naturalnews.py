from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager  
from datetime import datetime, timedelta  
import json
import os

filename_with_extension = os.path.basename(__file__)  
filename_without_extension = os.path.splitext(filename_with_extension)[0]  

# Create a headless browser session  
options = Options()  
options.add_argument("--headless")  # Run in headless mode  
options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)  
options.add_argument("--window-size=1920x1080")  # Specify window size (optional)  

def extract_posts(driver, days_old):  
    # Find all posts on the current page  
    posts = driver.find_elements(By.CLASS_NAME, "Post")  
    extracted_data = []  

    # Iterate through each post and extract the information  
    for post in posts:  
        date_str = post.find_element(By.CSS_SELECTOR, ".Date").text.split('/ By')[0].strip()  
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')  
        date_obj = date_obj.date()

        cutoff_date = datetime.now() -timedelta(days=days_old)
        cutoff_date = cutoff_date.date()

        # Compare the date to your cutoff  
        if date_obj <= cutoff_date:  
            break  # Stop extraction if date is before the cutoff  

        headline = post.find_element(By.CSS_SELECTOR, ".Headline a").text  
        description = post.find_element(By.CLASS_NAME, "Description").text  
        extracted_data.append({"title": headline, "description": description, "date": date_str, "url": post.find_element(By.CSS_SELECTOR, ".Headline a").get_attribute("href")})  
    
    return extracted_data  

def navigate_pages(driver, url, days_old, starting_page=1):  
    # Set up the Selenium driver (make sure to specify the path to your driver)  

    collected_data = []  
    page_number = starting_page  

    try:  
        while True:  
            page_url = f'{url}/page/{page_number}/' if page_number > 1 else url  
            driver.get(page_url)  
            new_data = extract_posts(driver, days_old)  
            
            if not new_data:  # Break the loop if no new data is found  
                break  

            collected_data.extend(new_data)  
            page_number += 1  # Increment page number to navigate to the next page  
        
        return collected_data  
    finally:  
        driver.quit()  # Make sure to close the driver after the scraping is done  

# Base URL without the page number  
url = 'https://naturalnews.com/category/health' 
days_old = 20

service = Service(ChromeDriverManager().install())  
driver = webdriver.Chrome(service=service, options=options)  

collected_posts = navigate_pages(driver, url, days_old)  
# Convert your list of dictionaries to a JSON string  
json_data = json.dumps(collected_posts, indent=4)  

# Write the JSON string to a file  
with open(f'{filename_without_extension}.json', 'w') as json_file:  
    json_file.write(json_data)
