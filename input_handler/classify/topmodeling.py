
import firebase_admin  
from firebase_admin import credentials  
from firebase_admin import firestore  
import torch
from transformers import AutoModel, AutoTokenizer, pipeline
from sklearn.metrics.pairwise import cosine_similarity
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline

# Initialize the app with a service account, granting admin privileges  
def init_src_db():
    cred = credentials.Certificate('path/from/serviceAccountKey.json')  
    firebase_admin.initialize_app(cred)  
    # Create a Firestore client  
    db = firestore.client() 
    return db

def init_dest_db():
    cred = credentials.Certificate('path/to/serviceAccountKey.json')
    dest_app = firebase_admin.initialize_app(cred, name = 'dest_app')
     # Create a Firestore client  
    db = firestore.client(app = dest_app)
    return db

def write_to_dest_db(dest_db, article_title, text, similarities, keywords, article_url, article_image_url, article_age):
    try:
        tag_scores = {}
        similarities = [float(sim) for sim in similarities] 

        # get catogory from keywords
        users_ref_tag = dest_db.collection('categories')
        doc_tag_stream = users_ref_tag.stream()
        tag_dict = {tag.to_dict().get("title"): tag.to_dict().get("category") for tag in doc_tag_stream}
        summary = summarize_article(text)

        for keyword, similarity_score in zip(keywords, similarities):
            if similarity_score > 0.2:
                tag_scores[keyword] = similarity_score
                category = tag_dict.get(keyword)  
        
        if tag_scores:
            doc_ref = dest_db.collection(category).document(article_title)
            doc_ref.set({
                'article_title': article_title,
                'article_url':article_url,
                'article_image': article_image_url,
                'article_age': article_age,
                'tag_scores': tag_scores,
                'text': text,
                'summary': summary
            })
            print(f'Document written with ID: {doc_ref.id}')  
        else:  
            print(f"Category not found for keyword: {keyword}") 
    except Exception as e:
        print(f"An error occurred: {e}")
            
        
    # tag_scores = {keyword: similarity for keyword, similarity in zip(keywords, similarities)}  

def get_article_data(source_db, db):
    # Adding data  
    # doc_ref = db.collection('citizenfreepress.com').document('Anthony Weiner files to run for office, despite child sexting conviction.')  
    # doc_ref.set({  
    #     'name': 'John Doe',  
    #     'email': 'john@example.com'  
    # })  

    # Retrieving data  
    try:
        users_ref = db.collection(source_db)
        # Convert stream to list immediately with timeout settings
        docs = list(users_ref.limit(100).stream())  # Process in smaller batches
        return docs
    except Exception as e:
        print(f"Fetching data error: {str(e)}")
        return []

# Step 2: Define a helper function for mean pooling  
def mean_pooling(model_output, attention_mask):  
    # Perform mean pooling on token embeddings  
    token_embeddings = model_output.last_hidden_state  
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())  
    return torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)

def get_tag_data(db):
    users_ref_tag = db.collection('categories')
    doc_tag = users_ref_tag.stream()
    keywords = []
    for tag in doc_tag:
        keywords.append(tag.to_dict().get("title"))

    return keywords

def get_similarity(docs, keywords, db, dest_db):
    # Tekken-Step 1: Load the tokenizer and model  
    model_name = "sentence-transformers/all-MiniLM-L6-v2"  
    tokenizer = AutoTokenizer.from_pretrained(model_name)  
    model = AutoModel.from_pretrained(model_name) 

    for doc in docs: 
        try: 
            # print(f'{doc.to_dict().get("article_title")}')

            # Step 3: Define the document and keywords  
            document = doc.to_dict().get("text")  
            

            # Step 4: Compute embeddings for the document and keywords  
            # Tokenizing and encoding the document  
            doc_inputs = tokenizer(document, return_tensors="pt", padding=True, truncation=True)  
            with torch.no_grad():  
                doc_model_output = model(**doc_inputs)  #Teken: converting dictionary key-value pairs into keyword arguments
            doc_embedding = mean_pooling(doc_model_output, doc_inputs['attention_mask'])
            doc_embedding = doc_embedding.squeeze().numpy()

            # Tokenizing and encoding the keywords  
            keyword_inputs = tokenizer(keywords, return_tensors="pt", padding=True, truncation=True)  
            with torch.no_grad():  
                keyword_model_output = model(**keyword_inputs)  
            keyword_embeddings = mean_pooling(keyword_model_output, keyword_inputs['attention_mask'])
            keyword_embeddings = keyword_embeddings.squeeze().numpy()

            # Step 5: Compute cosine similarities for the document and keywords  
            similarities = cosine_similarity([doc_embedding], keyword_embeddings) 

            article_url = doc.to_dict().get("article_url")
            article_image_url = doc.to_dict().get("article_image_url")
            article_age = doc.to_dict().get("article_age")

            # Step 6: Display Results  
            # print("\nCosine Similarities between the Document and Keywords:")  
            write_to_dest_db(dest_db, doc.to_dict().get("article_title"), document, similarities[0], keywords, article_url, article_image_url, article_age)
            # for keyword, similarity_score in zip(keywords, similarities[0]):  
                # print(f"Keyword: {keyword}, Similarity: {similarity_score:.4f}")
        except Exception as e:
            print(f"Error processing document: {e}")
            
def summarize_article(input_text):
    tokenizer = T5Tokenizer.from_pretrained('t5-base')
    model = T5ForConditionalGeneration.from_pretrained('t5-base')
    # Add input text truncation
    max_chunk_length = 1024  # BART's maximum input length
    
    # If text is too long, truncate it
    if len(input_text.split()) > max_chunk_length:
        input_text = ' '.join(input_text.split()[:max_chunk_length])
    
    # Add error handling
    try:
        # Tokenize the input text
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        # Generate summary
        summary_ids = model.generate(
            inputs,
            max_length=150,
            min_length=40,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    
    except Exception as e:
        print(f"Summarization failed: {str(e)}")
        return input_text[:200] + "..."  # Return truncated text as fallback

def main():
    db = init_src_db()
    dest_db = init_dest_db()
    print("Hello, World!")
    source_db = 'naturalmedicine.news'
    docs = get_article_data(source_db, db)
    keywords = get_tag_data(dest_db)
    get_similarity(docs, keywords, db, dest_db)
    # summarize_article()

if __name__ == "__main__":
    main()

