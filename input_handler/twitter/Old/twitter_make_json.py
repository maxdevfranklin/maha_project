import csv
import json

def make_json(csvFilePath, jsonFilePath):
    
    data = []
    
    with open(csvFilePath, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        for rows in csvReader:

            data.append(rows)

    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))
        
csvFilePath = r'twitter_posts.csv'
jsonFilePath = r'twitter_posts1.json'

make_json(csvFilePath, jsonFilePath)