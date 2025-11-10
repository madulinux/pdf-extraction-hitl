#!/usr/bin/env python3
"""
Test feedback tracking for CRF performance update
"""

from database.db_manager import DatabaseManager
from core.extraction.hybrid_strategy import HybridExtractionStrategy
import json

db = DatabaseManager()

# Get document 270
docs = db.execute_query('SELECT * FROM documents WHERE id = 270')
doc = docs[0]

print(f"📄 Document ID: {doc['id']}")

# Parse extraction_result
extraction_results = json.loads(doc['extraction_result'])

# Get feedback (corrections)
feedbacks = db.execute_query(f'SELECT * FROM feedback WHERE document_id = {doc["id"]}')
corrections = {fb['field_name']: fb['corrected_value'] for fb in feedbacks if fb['original_value'] != fb['corrected_value']}

print(f"\n📝 Corrections: {len(corrections)} fields")
for field, value in corrections.items():
    print(f"  - {field}: {value[:50]}")

# Check CRF performance BEFORE
conn = db.get_connection()
cursor = conn.execute("""
    SELECT strategy_type, accuracy, total_extractions, correct_extractions
    FROM strategy_performance
    WHERE template_id = 1 AND field_name = 'event_location' AND strategy_type = 'crf'
""")
before = cursor.fetchone()
print(f"\n📊 CRF Performance BEFORE:")
print(f"  Total: {before[2]}, Correct: {before[3]}, Accuracy: {before[1] * 100:.2f}%")

# Trigger learning from feedback
print(f"\n🔄 Triggering learn_from_feedback...")
hybrid = HybridExtractionStrategy(db)
hybrid.learn_from_feedback(1, extraction_results, corrections)

# Check CRF performance AFTER
cursor = conn.execute("""
    SELECT strategy_type, accuracy, total_extractions, correct_extractions
    FROM strategy_performance
    WHERE template_id = 1 AND field_name = 'event_location' AND strategy_type = 'crf'
""")
after = cursor.fetchone()
print(f"\n📊 CRF Performance AFTER:")
print(f"  Total: {after[2]}, Correct: {after[3]}, Accuracy: {after[1] * 100:.2f}%")

# Check if improved
if after[3] > before[3]:
    print(f"\n✅ SUCCESS! CRF correct count increased from {before[3]} to {after[3]}")
else:
    print(f"\n❌ FAILED! CRF correct count did not increase (still {after[3]})")
