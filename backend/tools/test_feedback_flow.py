#!/usr/bin/env python3
"""
Test Feedback Flow

This script tests the complete feedback flow including post-processor learning.
"""

import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from core.extraction.services import ExtractionService
from database.repositories import DocumentRepository, FeedbackRepository
import json

# Setup
db = DatabaseManager()
doc_repo = DocumentRepository(db)
feedback_repo = FeedbackRepository(db)

extraction_service = ExtractionService(
    document_repo=doc_repo,
    feedback_repo=feedback_repo,
    upload_folder='uploads',
    model_folder='models',
    feedback_folder='feedback'
)

# Get latest document
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT id, extraction_result
    FROM documents
    WHERE extraction_result IS NOT NULL
    ORDER BY id DESC
    LIMIT 1
''')

doc = cursor.fetchone()

if not doc:
    print("❌ No documents found")
    sys.exit(1)

print(f"📄 Testing with Document ID: {doc['id']}")

# Get extracted data
result = json.loads(doc['extraction_result'])
extracted_data = result.get('extracted_data', {})

print(f"\n📊 Extracted Data:")
for field, value in extracted_data.items():
    print(f"   {field:20s}: {value[:50] if isinstance(value, str) else value}")

# Create fake corrections for problematic fields
corrections = {}

if 'chairman_name' in extracted_data:
    original = extracted_data['chairman_name']
    if original.startswith('(') and original.endswith(')'):
        corrections['chairman_name'] = original[1:-1].strip()
        print(f"\n✏️  Correcting chairman_name: '{original}' → '{corrections['chairman_name']}'")

if 'event_name' in extracted_data:
    original = extracted_data['event_name']
    if original.startswith('"') and original.endswith('"'):
        corrections['event_name'] = original[1:-1].strip()
        print(f"✏️  Correcting event_name: '{original}' → '{corrections['event_name']}'")

if 'issue_place' in extracted_data:
    original = extracted_data['issue_place']
    if original.endswith(','):
        corrections['issue_place'] = original[:-1].strip()
        print(f"✏️  Correcting issue_place: '{original}' → '{corrections['issue_place']}'")

if not corrections:
    print("\n⚠️  No corrections needed (fields already clean)")
    sys.exit(0)

# Save corrections
print(f"\n💾 Saving {len(corrections)} corrections...")
result = extraction_service.save_corrections(doc['id'], corrections)

print(f"\n✅ Feedback saved!")
print(f"   Feedback IDs: {result['feedback_ids']}")
print(f"   Corrections count: {result['corrections_count']}")
