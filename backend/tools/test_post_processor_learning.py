#!/usr/bin/env python3
"""
Test Post-Processor Learning

This script tests if post-processor learns from feedback correctly.
"""

import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
import json

# Get latest document with corrections
db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT 
        d.id,
        d.template_id,
        d.extraction_result,
        COUNT(f.id) as correction_count
    FROM documents d
    LEFT JOIN feedback f ON d.id = f.document_id
    WHERE d.extraction_result IS NOT NULL
    GROUP BY d.id
    HAVING correction_count > 0
    ORDER BY d.id DESC
    LIMIT 1
''')

doc = cursor.fetchone()

if not doc:
    print("❌ No documents with corrections found")
    sys.exit(1)

print(f"📄 Testing with Document ID: {doc['id']}")
print(f"   Template ID: {doc['template_id']}")
print(f"   Corrections: {doc['correction_count']}")

# Get corrections
cursor.execute('''
    SELECT field_name, original_value, corrected_value
    FROM feedback
    WHERE document_id = ?
    ORDER BY field_name
''', (doc['id'],))

corrections = cursor.fetchall()

print(f"\n📝 Corrections:")
for corr in corrections:
    print(f"   {corr['field_name']:20s}: '{corr['original_value'][:40]}' → '{corr['corrected_value'][:40]}'")

# Now test post-processor learning
print(f"\n🧪 Testing Post-Processor Learning...")

from core.extraction.post_processor import AdaptivePostProcessor

# Create post-processor
post_processor = AdaptivePostProcessor(template_id=doc['template_id'], db_manager=db)

# Prepare data
extraction_results = json.loads(doc['extraction_result'])
corrections_dict = {c['field_name']: c['corrected_value'] for c in corrections}

# Trigger learning
print(f"\n🎓 Triggering learn_from_feedback...")
post_processor.learn_from_feedback(extraction_results, corrections_dict)

print(f"\n✅ Test completed!")
