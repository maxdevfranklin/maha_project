
import firebase_admin  
from firebase_admin import credentials  
from firebase_admin import firestore  

def init_src_db():
    cred = credentials.Certificate('path/to/serviceAccountKey.json')
    dest_app = firebase_admin.initialize_app(cred, name = 'dest_app')
     # Create a Firestore client  
    db = firestore.client(app = dest_app)
    return db

def add_multiple_categories(db):
    # Create a batch
    batch = db.batch()
    
    # Define your categories data
    category_data = "Policy and Advocacy"
    category_titles = ['Legislation', 'Health Reform Bills', 'Environmental Protection Acts', 'Food Safety Regulations', 'Advocacy Campaigns', 'Grassroots Movements', 'Lobbying Efforts', 'Public Petitions', 'Community Engagement', 'Town Halls', 'Partnerships', 'Volunteer Programs', 'Health Equity Advocacy', 'Addressing Disparities in Underserved Communities', 'Rural vs. Urban Health Solutions']
    # category_titles = ['School Programs', 'Physical Education', 'Nutrition Classes', 'Mental Health Awareness', 'Parent and Caregiver Education', 'Health Literacy for Families', 'Resources for Managing Chronic Conditions', 'Professional Training', 'Continuing Education', 'Digital Health Literacy']
    # category_titles = ['Non-Pharmaceutical Treatments', 'Holistic Therapies', 'Traditional Medicine', 'Mind-Body Practices', 'Natural Remedies and Supplements', 'Herbal Medicine', 'Dietary Supplements', 'Homeopathy', 'Detoxification Programs', 'Cultural and Traditional Practices', 'Indigenous Medicine', 'Ayurveda and Other Global Practices', 'Integration of Diet, Exercise, and Mental Health']
    for title in category_titles:
        doc_ref = db.collection('categories').document()
        category_dict = {
            'category': category_data,
            'title': f'{title}'
        }
        batch.set(doc_ref, category_dict)
        print(f'Document written with ID: {doc_ref.id}')
    
    # Commit the batch
    batch.commit()

def main():
    db = init_src_db()
    add_multiple_categories(db)

if __name__ == '__main__':  
    main()  