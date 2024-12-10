import os
from dotenv import load_dotenv  # Import the dotenv support  

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv()
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)

app = firebase_admin.initialize_app(cred)
db = firestore.client()

def get_single_article(article_domain, article_title):
    article = db.collection(f"{article_domain}").document(article_title).get()
    if not article.exists:
        return None
    return article.to_dict()

def check_if_exists(article_domain, article):
    """Check if the article already exists in the database."""
    if get_single_article(article_domain, article["article_title"]) is not None:
        return True
    return False

def force_insert_article(article_domain, article):
    db.collection(f"{article_domain}").document(article["article_title"]).set(article)

def insert_article(article_domain, article):
    """Insert the article into the database."""
    try:
        # article_parsed = articles_model.Case.model_validate(article)
        if check_if_exists(article_domain, article):
            print(f"""Article "{article["article_title"]}" already exists""")
            return
        force_insert_article(article_domain, article)
        print(f"Succeeded to insert article {article['article_title']}")
    except Exception as e:
        print(f"Failed to insert article {article['article_title']}: {e}")
