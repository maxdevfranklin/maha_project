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
    days_old = 10  
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
        WebDriverWait(driver, 10).until(  
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".mvp-blog-story-col"))  
        )  

        article_elements = driver.find_elements(By.CSS_SELECTOR, ".mvp-blog-story-col")  
        articles_info = []  

        # Store the basic info and URLs first  
        for element in article_elements:  
            article_info = {  
                "url": element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href'),  
                "main_image_url": element.find_element(By.CSS_SELECTOR, '.mvp-blog-story-img img').get_attribute('src'),  
                "category": element.find_element(By.CSS_SELECTOR, '.mvp-cd-cat').text,  
                "headline": element.find_element(By.CSS_SELECTOR, 'h2').text,  
                # 'summary' will be added after returning from the article page  
            }  
            articles_info.append(article_info)  

        # Iterate over each article to extract the date and summary  
        for article in articles_info:  
            # Extract the publication date from the article page  
            published_date = extract_date_from_article(article['url'], driver)  
            
            # Navigate back to the listing page  
            driver.back()  
            WebDriverWait(driver, 10).until(  
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".mvp-blog-story-col"))  
            )  
            
            # Check to stop extraction based on date condition  
            if (today - published_date).days > days_old:  
                continue_scraping = False  
                break  
            
            # Find the element with the matching URL to extract the summary  
            article_elements = driver.find_elements(By.CSS_SELECTOR, ".mvp-blog-story-col")  
            for elem in article_elements:  
                if elem.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') == article['url']:  
                    article['summary'] = elem.find_element(By.CSS_SELECTOR, '.mvp-blog-story-text p').text  
                    break  

            # Update the article dictionary with the date and add it to the data list  
            article['published_date'] = published_date.strftime('%Y-%m-%d')  
            data.append(article)  

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