
import firebase_admin  
from firebase_admin import credentials  
from firebase_admin import firestore  

def init_src_db():
    cred = credentials.Certificate('path/to/serviceAccountKey.json')
    dest_app = firebase_admin.initialize_app(cred, name = 'dest_app')
     # Create a Firestore client  
    db = firestore.client(app = dest_app)
    return db

def update_category(db):
    categories_ref = db.collection('categories')
    docs = categories_ref.where('title', '>=', 'Title for Category').get()

    batch = db.batch()

    for doc in docs:
        # if doc.get('title').starts_with('Title for Category'):
        new_title = doc.get('title').replace('Title for Category', '').strip()
        doc_ref = categories_ref.document(doc.id)
        batch.update(doc_ref, {'title': new_title})
        print(f'Updated document with ID: {doc.id}: {new_title}')
    batch.commit()

def main():
    db = init_src_db()
    update_category(db)

if __name__ == '__main__':  
    main()  