#!/usr/bin/env python3
"""
Batch update strategy performance for ALL existing documents
"""

from database.db_manager import DatabaseManager
from core.extraction.hybrid_strategy import HybridExtractionStrategy
import json

db = DatabaseManager()

# Get CRF performance BEFORE
conn = db.get_connection()
cursor = conn.execute("""
    SELECT strategy_type, accuracy, total_extractions, correct_extractions
    FROM strategy_performance
    WHERE template_id = 1 AND field_name = 'event_location' AND strategy_type = 'crf'
""")
before = cursor.fetchone()
print(f"📊 CRF Performance BEFORE:")
print(f"  Total: {before[2]}, Correct: {before[3]}, Accuracy: {before[1] * 100:.2f}%")

# Get all documents with corrections
cursor = conn.execute("""
    SELECT DISTINCT document_id 
    FROM feedback 
    WHERE original_value != corrected_value
    ORDER BY document_id
""")
doc_ids = [row[0] for row in cursor.fetchall()]

print(f"\n🔄 Processing {len(doc_ids)} documents with corrections...")

hybrid = HybridExtractionStrategy(db)
processed = 0
skipped = 0

for i, doc_id in enumerate(doc_ids):
    if (i + 1) % 50 == 0:
        print(f"  Progress: {i + 1}/{len(doc_ids)}...")
    
    docs = db.execute_query(f'SELECT * FROM documents WHERE id = {doc_id}')
    if not docs:
        skipped += 1
        continue
    
    doc = docs[0]
    
    # Parse extraction_result
    if not doc['extraction_result']:
        skipped += 1
        continue
    
    try:
        extraction_results = json.loads(doc['extraction_result'])
    except:
        skipped += 1
        continue
    
    # Get feedback (corrections)
    feedbacks = db.execute_query(f'SELECT * FROM feedback WHERE document_id = {doc_id}')
    corrections = {fb['field_name']: fb['corrected_value'] for fb in feedbacks if fb['original_value'] != fb['corrected_value']}
    
    if not corrections:
        skipped += 1
        continue
    
    # Trigger learning (suppress logging)
    try:
        hybrid.learn_from_feedback(1, extraction_results, corrections)
        processed += 1
    except Exception as e:
        print(f"  ⚠️ Error processing document {doc_id}: {e}")
        skipped += 1

print(f"\n✅ Processed: {processed}")
print(f"⏭️  Skipped: {skipped}")

# Get CRF performance AFTER
cursor = conn.execute("""
    SELECT strategy_type, accuracy, total_extractions, correct_extractions
    FROM strategy_performance
    WHERE template_id = 1 AND field_name = 'event_location' AND strategy_type = 'crf'
""")
after = cursor.fetchone()
print(f"\n📊 CRF Performance AFTER:")
print(f"  Total: {after[2]}, Correct: {after[3]}, Accuracy: {after[1] * 100:.2f}%")

# Summary
improvement = after[3] - before[3]
print(f"\n🎯 IMPROVEMENT:")
print(f"  Correct count: +{improvement}")
print(f"  Accuracy: {before[1] * 100:.2f}% → {after[1] * 100:.2f}% (+{(after[1] - before[1]) * 100:.2f}%)")
