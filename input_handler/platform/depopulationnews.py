import datetime  
import os
import json

from selenium import webdriver  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager  

filename_with_extension = os.path.basename(__file__)  
filename_without_extension = os.path.splitext(filename_with_extension)[0]  

# Set up headless Chrome driver  
options = Options()  
options.add_argument("--headless")  
service = Service(ChromeDriverManager().install())  
driver = webdriver.Chrome(service=service, options=options)  

# Function to convert the date string to a datetime object  
def convert_date(date_str):  
    return datetime.datetime.strptime(date_str, '%m/%d/%Y')  

# Function to find posts within the desired time period  
def find_posts(driver, url, days_old):  
    current_date = datetime.datetime.now()  
    delta = datetime.timedelta(days=days_old)  
    posts_data = []  

    page_number = 1  
    while True:  
        driver.get(f"{url}/page/{page_number}/")  
        elements = driver.find_elements(By.CLASS_NAME, "Post")  

        for element in elements:  
            date_str = element.find_element(By.CLASS_NAME, "Date").text  
            post_date = convert_date(date_str)  

            # If the post is older than the specified days, stop scraping  
            if current_date - post_date > delta:  
                print(f"Post is older than {days_old} days. Stopping search.")  
                return posts_data  

            # Extracting the details  
            title_element = element.find_element(By.CLASS_NAME, "Title").find_element(By.TAG_NAME, "a")  
            author_element = element.find_element(By.CLASS_NAME, "Author").find_element(By.TAG_NAME, "a")  
            
            post_url = title_element.get_attribute("href")  
            title = title_element.text  
            author = author_element.text.strip("By ")  

            posts_data.append({  
                'url': post_url,  
                'title': title,  
                'date': date_str,  
                'author': author  
            })  

        page_number += 1  

    return posts_data  

# Parameters  
days_old = 10  # number of days_old as specified  
base_url = "https://depopulation.news/all-posts"  

# Start scraping  
posts = find_posts(driver, base_url, days_old)  

# Close the driver  
driver.quit()  

# Convert your list of dictionaries to a JSON string  
json_data = json.dumps(posts, indent=4)  

# Write the JSON string to a file  
with open(f'{filename_without_extension}.json', 'w') as json_file:  
    json_file.write(json_data)
