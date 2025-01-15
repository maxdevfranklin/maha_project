import requests  
from bs4 import BeautifulSoup  

# Example Wayback Machine URL for a finance website  
wayback_url = "https://web.archive.org/web/20030501000000/https://www.reuters.com/"  

response = requests.get(wayback_url)  
soup = BeautifulSoup(response.text, 'html.parser')  

# Find and parse article links/titles  
articles = soup.find_all('a')  
for article in articles[:100]:  
    print(article.text, article.get('href'))