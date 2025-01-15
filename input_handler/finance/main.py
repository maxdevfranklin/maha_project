# Python 3
import http.client, urllib.parse
import firebase_admin  
from firebase_admin import credentials  
from firebase_admin import firestore  

def init_dest_db():
    cred = credentials.Certificate('path/service_finance_db.json')
    finance_db = firebase_admin.initialize_app(cred, name = 'finance_db')
     # Create a Firestore client  
    db = firestore.client(app = finance_db)
    return db

def get_article():
    conn = http.client.HTTPSConnection('api.thenewsapi.com')

    params = urllib.parse.urlencode({
        'api_token': 'JlJbCN82J4BNMPwzR6Gx4NbYwvtbpcs91BXyAiVi',
        'categories': 'business',
        'language' : "en",
        'limit': 20,
        'published_on' : '2025-01-09',
        })

    conn.request('GET', '/v1/news/all?{}'.format(params))

    res = conn.getresponse()
    data = res.read()

    print(data.decode('utf-8'))

def main():
    dest_db = init_dest_db()
    print("Hello, World!")
    source_db = 'nopharmfilm.com'
    get_article()

if __name__ == "__main__":
    main()