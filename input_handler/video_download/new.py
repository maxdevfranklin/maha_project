from seleniumwire import webdriver  # Import from seleniumwire

# Create a new instance of the Chrome driver
driver = webdriver.Chrome()

# Go to the Google home page
driver.get('https://podcasts.apple.com/us/podcast/101-make-america-healthy-again-ft-del-bigtree/id1764140307?i=1000675452034&uo=4')

# Access requests via the `requests` attribute
for request in driver.requests:
    if request.response:
        print(
            request.url,
            request.response.status_code,
            request.response.headers['Content-Type']
        )