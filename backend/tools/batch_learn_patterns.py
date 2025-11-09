#!/usr/bin/env python3
"""
Batch Learn Post-Processor Patterns

This script learns post-processor patterns from ALL existing feedback.
"""

import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from core.extraction.post_processor import AdaptivePostProcessor
import json

print("🎓 Batch Learning Post-Processor Patterns")
print("="*60)

# Get all documents with feedback
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
    ORDER BY d.id
''')

documents = cursor.fetchall()

print(f"📊 Found {len(documents)} documents with corrections")

# Group by template
templates = {}
for doc in documents:
    template_id = doc['template_id']
    if template_id not in templates:
        templates[template_id] = []
    templates[template_id].append(doc)

# Learn patterns for each template
for template_id, docs in templates.items():
    print(f"\n📚 Template {template_id}: {len(docs)} documents")
    
    # Create post-processor
    post_processor = AdaptivePostProcessor(template_id=template_id, db_manager=db)
    
    # Learn from each document
    learned_count = 0
    for doc in docs:
        # Get corrections
        cursor.execute('''
            SELECT field_name, original_value, corrected_value
            FROM feedback
            WHERE document_id = ?
        ''', (doc['id'],))
        
        corrections_list = cursor.fetchall()
        
        if not corrections_list:
            continue
        
        # Prepare data
        extraction_results = json.loads(doc['extraction_result'])
        corrections = {c['field_name']: c['corrected_value'] for c in corrections_list}
        
        # Learn
        post_processor.learn_from_feedback(extraction_results, corrections)
        learned_count += 1
    
    print(f"   ✅ Learned from {learned_count} documents")
    
    # Show learned patterns
    print(f"\n   📝 Learned Patterns:")
    for field, data in post_processor.learned_patterns.items():
        structural = data.get('structural_noise', {})
        sample_count = data.get('sample_count', 0)
        
        issues = []
        if structural.get('has_parentheses_both', 0) > 0:
            issues.append(f"parens(both)={structural['has_parentheses_both']}")
        if structural.get('has_quotes', 0) > 0:
            issues.append(f"quotes={structural['has_quotes']}")
        if structural.get('has_trailing_comma', 0) > 0:
            issues.append(f"comma={structural['has_trailing_comma']}")
        
        if issues:
            print(f"      {field:20s}: {sample_count:3d} samples - {', '.join(issues)}")

print(f"\n✅ Batch learning completed!")
