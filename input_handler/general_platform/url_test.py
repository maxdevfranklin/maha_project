import requests  

def check_url_status(url):  
    try:  
        response = requests.get(url, timeout=5)  # Timeout set to 5 seconds  
        if response.status_code == 200:  
            return {"url": url, "status": "Accessible", "response_time": response.elapsed.total_seconds()}  
        else:  
            return {"url": url, "status": f"Not Accessible ({response.status_code})", "response_time": None}  
    except requests.exceptions.RequestException as e:  
        return {"url": url, "status": f"Error: {e}", "response_time": None}  

# List of URLs  
urls = [  
    "https://childrenshealthdefense.org/defender/ys",
    "https://www.google.com",   
    "https://www.nonexistentwebsite123.com"  
]  

# Test each URL  
results = [check_url_status(url) for url in urls]  
for result in results:  
    print(result)