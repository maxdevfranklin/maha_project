
import firebase_admin  
from firebase_admin import credentials  
from firebase_admin import firestore  

def init_src_db():
    cred = credentials.Certificate('path/from/serviceAccountKey.json')  
    firebase_admin.initialize_app(cred)  
    # Create a Firestore client  
    db = firestore.client()
    return db

def add_multiple_categories(db):
    # Create a batch
    batch = db.batch()
    
    # Define your categories data
    category_data = "Alternative Medicine and Wellness"
    category_title = ['1', '2']
    categories = {
        f'category-{title}': {
            'category': category_data,
            'title': f'Title for category {title}'
        }
        for title in category_title
    }
    
    # Add each category to batch
    for category in categories:
        doc_ref = db.collection('tags').document()
        batch.set(doc_ref, category)
        print(f'Document written with ID: {doc_ref.id}')
    
    # Commit the batch
    batch.commit()

def main():
    db = init_src_db()
    add_multiple_categories(db)

if __name__ == '__main__':  
    main()  