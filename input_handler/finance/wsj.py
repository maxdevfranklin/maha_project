from bs4 import BeautifulSoup
import requests

url = "https://www.wsj.com"
# Specify the `user-agent` in order not to be blocked
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

response = requests.get(url, headers=header)

soup = BeautifulSoup(response.content, "lxml")

def get_articles():
    print(soup)
    for item in soup.select(".WSJTheme--headline--7VCzo7Ay"):
        # Articles might be under an `h2` or `h3`, use a CSS selector to select both
        headline = item.select_one("h2, h3").get_text()
        link = item.find("a")["href"]
        noticia = headline + " - " + link

        print(noticia)

##bulleted items: `h4' too + note different class
for item in soup.select(".WSJTheme--bullet-item--5c1Mqfdr"):
    headline2 = item.select_one("h4").get_text()
    link2 = item.find("a")["href"]
    noticia2 = headline2 + " - " + link2

    print(noticia2)

##opinion articles --> note different class
for item in soup.select(".style--byline--1k-cTV4i"):
    headline3 = item.select_one("h3").get_text()
    link3 = item.find("a")["href"]
    noticia3 = headline3 + " - " + link3

    print(noticia3)

def main():
    get_articles()

if __name__ == "__main__":
    main()