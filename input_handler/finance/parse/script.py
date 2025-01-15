# Example usage:
import json

def transform_json_data(raw_data):
    transformed = {
        "status": raw_data["status"],
        "numResults": raw_data["numResults"],
        "articles": []
    }
    
    for article in raw_data["articles"]:
        transformed_article = {
            "url": article["url"],
            "authorsByline": article["authorsByline"],
            "articleId": article["articleId"],
            "title": article["title"],
            "description": article["description"].split(".")[0] + ".",  # Take first sentence only
            "pubDate": article["pubDate"]
        }
        transformed["articles"].append(transformed_article)
    
    return transformed

with open('data.json', 'r') as file:
    content = file.read()
    raw_json_data = json.loads(content)


# Assuming your raw JSON data is stored in a variable called 'raw_json_data'
transformed_data = transform_json_data(raw_json_data)

# Print the transformed data in a formatted way
print(json.dumps(transformed_data, indent=2))

with open('result.json', 'w') as file:
    json.dump(transformed_data, file, indent=4)
