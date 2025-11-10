#!/usr/bin/env python3
"""
Batch update strategy performance for existing documents
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

# Process documents 268-276
doc_ids = [268, 269, 270, 272, 273, 275, 276]
hybrid = HybridExtractionStrategy(db)

processed = 0
for doc_id in doc_ids:
    docs = db.execute_query(f'SELECT * FROM documents WHERE id = {doc_id}')
    if not docs:
        continue
    
    doc = docs[0]
    
    # Parse extraction_result
    if not doc['extraction_result']:
        continue
    
    extraction_results = json.loads(doc['extraction_result'])
    
    # Get feedback (corrections)
    feedbacks = db.execute_query(f'SELECT * FROM feedback WHERE document_id = {doc_id}')
    corrections = {fb['field_name']: fb['corrected_value'] for fb in feedbacks if fb['original_value'] != fb['corrected_value']}
    
    if not corrections:
        continue
    
    print(f"\n📄 Processing document {doc_id} ({len(corrections)} corrections)...")
    
    # Trigger learning
    hybrid.learn_from_feedback(1, extraction_results, corrections)
    processed += 1

print(f"\n✅ Processed {processed} documents")

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
