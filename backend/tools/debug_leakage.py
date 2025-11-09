"""
Debug script to check for actual content duplication
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

from database.db_manager import DatabaseManager
from core.learning.training_utils import split_training_data
import json
import pdfplumber

db = DatabaseManager()

# Get validated documents
validated_docs = db.get_validated_documents(template_id=1)
print(f"Total documents: {len(validated_docs)}")

# Prepare training data (simplified)
X_train = []
doc_ids = []

for doc in validated_docs[:50]:  # Check first 50
    doc_id = doc['id']
    extraction_result = json.loads(doc['extraction_result'])
    extracted_data = extraction_result.get('extracted_data', {})
    
    # Extract words
    with pdfplumber.open(doc['file_path']) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)
    
    # Create simple content string
    content = ' '.join([w['text'].lower() for w in words])
    X_train.append(content)
    doc_ids.append(doc_id)

print(f"\nProcessed {len(X_train)} documents")

# Split
from sklearn.model_selection import train_test_split
X_train_split, X_test_split, ids_train, ids_test = train_test_split(
    X_train, doc_ids,
    test_size=0.2,
    random_state=42
)

print(f"Train: {len(X_train_split)}, Test: {len(X_test_split)}")

# Check for exact duplicates
print(f"\n🔍 Checking for exact content duplicates...")
train_hashes = {}
for i, content in enumerate(X_train_split):
    h = hash(content)
    if h in train_hashes:
        print(f"   ⚠️  Duplicate in TRAIN: doc {ids_train[i]} == doc {ids_train[train_hashes[h]]}")
    train_hashes[h] = i

duplicates_found = 0
for i, test_content in enumerate(X_test_split):
    test_hash = hash(test_content)
    if test_hash in train_hashes:
        train_idx = train_hashes[test_hash]
        print(f"   ❌ LEAKAGE: test doc {ids_test[i]} == train doc {ids_train[train_idx]}")
        duplicates_found += 1

if duplicates_found == 0:
    print(f"   ✅ No exact content duplicates found!")
else:
    print(f"\n   Total duplicates: {duplicates_found}/{len(X_test_split)}")
