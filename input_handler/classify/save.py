import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

# Initialize Firebase Admin
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Retrieve data from Firebase
projects_ref = db.collection('Healthcare Reform and Policy')
projects_docs = projects_ref.stream()

# Format the data
projects_data = []
for doc in projects_docs:
    project = doc.to_dict()
    projects_data.append({
        'name': project.get('article_title', ''),
        'description': project.get('summary', ''),
        'image': project.get('article_imge', '/projects/project.png'),
        'url': project.get('article_url', 'http://localhost:3000/'),
        'text': project.get('text', ''),
        'date': project.get('article_age', ''),
    })

# Create TypeScript output
ts_output = 'const projects = [\n'
for project in projects_data:
    ts_output += '{\n'
    ts_output += f'  name: "{project["name"]}",\n'
    ts_output += f'  description: "{project["description"]}",\n'
    ts_output += f'  image: "{project["image"]}",\n'
    ts_output += f'  url: "{project["url"]}",\n'
    ts_output += f'  date: "{project["date"]}",\n'
    ts_output += '},\n'
ts_output += '];\n\nexport default projects;'

# Save to TypeScript file
os.makedirs('output', exist_ok=True)

# Get current working directory
current_dir = os.getcwd()
output_path = os.path.join(current_dir, 'output', 'projects.ts')

# Save to TypeScript file
with open(output_path, 'w') as f:
    f.write(ts_output)

# Print confirmation
print(f"File created successfully at: {output_path}")