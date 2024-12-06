import json  
import os  
from datetime import datetime  
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.chrome.service import Service  
from webdriver_manager.chrome import ChromeDriverManager  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  

def extract_date_from_article(article_url, driver):  
    driver.get(article_url)  
    date_element = WebDriverWait(driver, 10).until(  
        EC.presence_of_element_located((By.XPATH, "//time[@itemprop='datePublished']"))  
    )  
    date_string = date_element.get_attribute("datetime")  
    return datetime.strptime(date_string, '%Y-%m-%d').date()  

def main():  
    days_old = 2
    today = datetime.now().date()  
    base_url = "https://vigilantnews.com/post/category/health/"  
    url = base_url  

    # Set up headless Chrome driver  
    options = Options()  
    options.add_argument("--headless")  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=options)  

    data = []  
    page = 1  
    continue_scraping = True  

    while continue_scraping and url:  
        driver.get(url)  
        elements = WebDriverWait(driver, 10).until(  
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".mvp-blog-story-col"))  
        )  
        
        article_links = [element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') for element in elements]  
        
        for article_url in article_links:  
            published_date = extract_date_from_article(article_url, driver)  
            
            if (today - published_date).days > days_old:  
                continue_scraping = False  
                break  
            
            # After extracting the date, navigate back to the listing page  
            driver.back()  
            WebDriverWait(driver, 10).until(  
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".mvp-blog-story-col"))  
            )  

            # The indexes need to be recalculated in case the page updates dynamically  
            # So fetch the elements again and select the current one  
            elements = driver.find_elements(By.CSS_SELECTOR, ".mvp-blog-story-col")  
            element = elements[article_links.index(article_url)]  
            
            item = {  
                "url": article_url,  
                "main_image_url": element.find_element(By.CSS_SELECTOR, '.mvp-blog-story-img img').get_attribute('src'),  
                "category": element.find_element(By.CSS_SELECTOR, '.mvp-cd-cat').text,  
                "published_date": published_date.strftime('%Y-%m-%d'),  
                "headline": element.find_element(By.CSS_SELECTOR, 'h2').text,  
                "summary": element.find_element(By.CSS_SELECTOR, 'p').text,  
                "title": element.get_attribute('data-image-title'),  
                "image_url": element.find_element(By.CSS_SELECTOR, '.mvp-blog-story-img img').get_attribute('src'),  
            }  
            data.append(item)  

        # Prepare the URL for the next page  
        if continue_scraping:  
            page += 1  
            url = f"{base_url}page/{page}/"  

    # Close the browser  
    driver.quit()  

    # Save the data to a JSON file  
    script_name = os.path.basename(__file__)  
    json_filename = script_name.replace('.py', '.json')  
    with open(json_filename, 'w') as f:  
        json.dump(data, f, indent=4)  

    print(f"Data saved to {json_filename}")  

if __name__ == "__main__":  
    main()