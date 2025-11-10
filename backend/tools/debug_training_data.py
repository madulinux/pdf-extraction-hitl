#!/usr/bin/env python3
"""
Debug Training Data
Check what's wrong with training data preparation
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

import json
from database.db_manager import DatabaseManager
from core.learning.learner import AdaptiveLearner
import pdfplumber

db = DatabaseManager()
learner = AdaptiveLearner()

# Get template config
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT id FROM template_configs 
    WHERE template_id = 1 AND is_active = 1
    ORDER BY version DESC
    LIMIT 1
''')
config_row = cursor.fetchone()
config_id = config_row[0]

cursor.execute('''
    SELECT field_name, field_type, base_pattern
    FROM field_configs
    WHERE config_id = ?
''', (config_id,))

fields = {}
for field_name, field_type, base_pattern in cursor.fetchall():
    fields[field_name] = {
        'field_type': field_type,
        'base_pattern': base_pattern
    }

template_config = {
    'template_id': 1,
    'fields': fields
}

print("📋 Template Config:")
print(f"   Fields: {list(fields.keys())}")

# Get one document with feedback
cursor.execute('''
    SELECT d.id, d.file_path, f.field_name, f.corrected_value
    FROM documents d
    JOIN feedback f ON f.document_id = d.id
    WHERE d.template_id = 1
    LIMIT 1
''')

doc = cursor.fetchone()
conn.close()

print(f"\n📄 Test Document:")
print(f"   ID: {doc[0]}")
print(f"   Path: {doc[1]}")
print(f"   Field: {doc[2]}")
print(f"   Value: {doc[3]}")

# Extract words
print(f"\n🔍 Extracting words...")
words = []
try:
    with pdfplumber.open(doc[1]) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_words = page.extract_words()
            for word in page_words:
                words.append({
                    'text': word['text'],
                    'x0': word['x0'],
                    'y0': word['top'],
                    'x1': word['x1'],
                    'y1': word['bottom'],
                    'page': page_num
                })
except Exception as e:
    print(f"❌ Error: {e}")

print(f"   Total words: {len(words)}")
if words:
    print(f"   First 5 words: {[w['text'] for w in words[:5]]}")

# Try to create BIO sequence
print(f"\n🧬 Creating BIO sequence...")
feedbacks = [{
    'field_name': doc[2],
    'corrected_value': doc[3]
}]

try:
    features, labels = learner._create_bio_sequence_multi(
        feedbacks,
        words,
        template_config=template_config,
        target_fields=[doc[2]]
    )
    
    print(f"   Features: {len(features)}")
    print(f"   Labels: {len(labels)}")
    print(f"   Unique labels: {set(labels)}")
    
    # Count labels
    label_counts = {}
    for label in labels:
        label_counts[label] = label_counts.get(label, 0) + 1
    
    print(f"   Label distribution: {label_counts}")
    
    if features:
        print(f"\n   Sample feature keys: {list(features[0].keys())[:10]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
