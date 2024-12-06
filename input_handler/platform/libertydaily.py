import os  
import json  
import datetime  
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.by import By  
from selenium.common.exceptions import NoSuchElementException  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  

# Inputs  
base_url = "https://thelibertydaily.com/archive/"  
days_old = 3  # Example input, replace with your actual input  

# Configure the Chrome WebDriver in headless mode  
options = Options()  
options.headless = True  

driver = webdriver.Chrome(options=options)  
wait = WebDriverWait(driver, 10)  

archive_collected_data = []  

# Calculate the cut-off date based on the current time minus 'days_old'  
cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)  

page_number = 1  
while True:  
    driver.get(f"{base_url}page/{page_number}/")  
    items = driver.find_elements(By.CSS_SELECTOR, ".item")  # Selector for the items  
    try:  
        agree_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.css-47sehv")))  

        # Check if the button is visible and then click on it  
        if agree_button.is_displayed():  
            agree_button.click()  
            print("Clicked the 'AGREE' button.")  
        else:  
            print("The 'AGREE' button was not visible.")  
    except (NoSuchElementException, TimeoutException):  
        print("The 'AGREE' button was not found on the page within the given time.") 
    for item in items:  
        try:  
            # Get URL and title from the item  
            link_elem = item.find_element(By.CSS_SELECTOR, "a")  
            title = link_elem.text.strip()  
            url = link_elem.get_attribute('href')  

            # Get the date string from the item and convert it to a datetime object  
            date_elem = item.find_element(By.CSS_SELECTOR, "span.date")  
            date_string = date_elem.text.strip()  
            article_date = datetime.datetime.strptime(date_string, "%B %d, %Y")  
            date_string = date_elem.text.strip()  
    

            if article_date < cutoff_date:  
                # Stop collecting articles and break if the date is earlier than the cut-off  
                break  

            # Append the collected data dictionary to the list  
            archive_collected_data.append({  
                'url': url,  
                'title': title,  
                'date': article_date.strftime("%Y-%m-%d")
            })  
            
        except NoSuchElementException:  
            # Skip in case any essential element is missing  
            continue  
        except Exception as e:  
            print(f"An error occurred: {e}")  

    # Break the loop if we reached the cutoff date or no more items found  
    if not items or article_date < cutoff_date:  
        break  

    # Increment the page number  
    page_number += 1  

# Once data collection is done, close the Selenium driver  
driver.quit()  

# Save the collected data to a JSON file  
script_name = os.path.splitext(os.path.basename(__file__))[0]  # Get script name without extension  
json_file_name = f"{script_name}.json"  

with open(json_file_name, 'w', encoding='utf-8') as json_file:  
    json.dump(archive_collected_data, json_file, ensure_ascii=False, indent=4)  

print(f"Data is saved to {json_file_name}")