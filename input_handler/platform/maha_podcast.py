import json  
import os  
from datetime import datetime, timedelta  
from selenium import webdriver  
from selenium.webdriver.chrome.service import Service  
from selenium.webdriver.common.by import By  
from selenium.webdriver.chrome.options import Options  
from webdriver_manager.chrome import ChromeDriverManager  

# Inputs  
URL = "https://makeamericahealthy.com/episodes/"  
DAYS_OLD = 90  
service = Service(ChromeDriverManager().install())  
CURRENT_DATE = datetime.now()

# JSON output file named after this Python script  
script_name = os.path.splitext(os.path.basename(__file__))[0]  
output_file_name = f"{script_name}.json"  

# WebDriver setup for Headless Chrome  
options = Options()  
options.add_argument("--headless")  # Hide browser UI  
options.add_argument("--disable-gpu")  
options.add_argument("--window-size=1920x1080")  
options.add_argument("--log-level=3")  
options.add_argument("--disable-extensions")  


def format_date(date_text):  
    """  
    Convert date from 'Month Day, Year' to 'yyyy-mm-dd' format.  
    Example: 'October 8, 2024' → '2024-10-08'  
    """  
    return datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")  


def fetch_episodes(driver, days_limit):  
    """  
    Find podcast episodes and extract `date`, `title`, URLs (Apple, Spotify).  
    Stops processing when it encounters episodes beyond the `days_limit`.  
    """  
    results = []  

    # Locate all containers with episodes  
    episode_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'elementor-element') and contains(@class, 'e-flex')]")  
    print(f"Found {len(episode_elements)} episodes to potentially process...")  

    for element in episode_elements:  
        try:  
            # Extract Date  
            raw_date_text = element.find_element(By.XPATH, ".//div[contains(@class, 'elementor-widget-heading')][1]//h2").text.strip()  
            formatted_date = format_date(raw_date_text)  

            # Check if the episode falls outside the date limit  
            episode_date = datetime.strptime(formatted_date, "%Y-%m-%d")  
            if CURRENT_DATE - episode_date > timedelta(days=days_limit):  
                print(f"Stopping: Episode date {formatted_date} is older than {days_limit} days.")  
                break  # Stop processing further elements  

            # Extract Title  
            title = element.find_element(By.XPATH, ".//div[contains(@class, 'elementor-widget-heading')][2]//h2").text.strip()  

            summary = element.find_element(By.XPATH, ".//div[contains(@class, 'elementor-widget-text-editor')]//p").text.strip()  
            
            # Extract Apple Podcast URL  
            try:  
                apple_podcast_url = element.find_element(By.XPATH, ".//a[contains(@href, 'podcasts.apple')]").get_attribute("href")  
            except Exception:  
                apple_podcast_url = "Not Available"  

            # Extract Spotify URL  
            try:  
                spotify_url = element.find_element(By.XPATH, ".//a[contains(@href, 'open.spotify')]").get_attribute("href")  
            except Exception:  
                spotify_url = "Not Available"  

            # Append extracted episode data to results list  
            results.append({  
                "title": title,  
                "date": formatted_date,  
                "summary": summary,
                "apple_podcast_url": apple_podcast_url,  
                "spotify_url": spotify_url  
            })  
            print(f"Extracted: {title} | {formatted_date} | Apple Podcast: {apple_podcast_url} | Spotify: {spotify_url}")  

        except Exception as e:  
            print(f"Error processing element: {e}")  

    return results  


def main():  
    # Initialize WebDriver  
    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=options)  

    try:  
        # Load the webpage in the driver  
        print(f"Opening URL: {URL}")  
        driver.get(URL)  

        # Fetch podcast episodes data  
        all_episodes = fetch_episodes(driver, DAYS_OLD)  

        # Save the data in a JSON file  
        with open(output_file_name, "w") as json_file:  
            json.dump(all_episodes, json_file, indent=4)  
        print(f"\nData successfully saved to {output_file_name}.")  

    except Exception as e:  
        print(f"An error occurred during execution: {e}")  

    finally:  
        driver.quit()  # Ensure the driver is closed  


if __name__ == "__main__":  
    main()