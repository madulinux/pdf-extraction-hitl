#!/usr/bin/env python3
"""
Test extraction for document 298 with new scoring
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from core.extraction.services import ExtractionService
import json

# Get document 298
db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('SELECT file_path, template_id FROM documents WHERE id = 298')
doc = cursor.fetchone()

if not doc:
    print("Document 298 not found")
    sys.exit(1)

print("="*80)
print("🔍 TESTING DOCUMENT 298 WITH NEW SCORING")
print("="*80)
print(f"File: {os.path.basename(doc['file_path'])}")
print(f"Template: {doc['template_id']}")

# Extract
service = ExtractionService(db)
result = service.extract_document(doc['file_path'], doc['template_id'])

print("\n" + "="*80)
print("📊 EXTRACTION RESULTS")
print("="*80)

extracted_data = result['extracted_data']
methods = result['extraction_methods']
confidences = result['confidence_scores']

# Focus on problematic fields
problem_fields = ['event_date', 'issue_place', 'issue_date']

for field in problem_fields:
    print(f"\n{field}:")
    print(f"  Value: '{extracted_data.get(field, 'N/A')}'")
    print(f"  Method: {methods.get(field, 'N/A')}")
    print(f"  Confidence: {confidences.get(field, 0):.4f}")

conn.close()
