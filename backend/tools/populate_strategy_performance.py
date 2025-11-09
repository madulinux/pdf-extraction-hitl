#!/usr/bin/env python3
"""
Populate strategy_performance table from historical extraction data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database.db_manager import DatabaseManager
from collections import defaultdict

def populate_performance():
    """Calculate and populate strategy performance from historical data"""
    
    print("="*80)
    print("📊 POPULATING STRATEGY PERFORMANCE")
    print("="*80)
    
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get all documents with extraction results
    cursor.execute('''
        SELECT 
            d.id,
            d.template_id,
            d.extraction_result,
            GROUP_CONCAT(f.field_name || ':' || f.corrected_value, '||') as corrections
        FROM documents d
        LEFT JOIN feedback f ON d.id = f.document_id
        WHERE d.extraction_result IS NOT NULL
        GROUP BY d.id
    ''')
    
    documents = cursor.fetchall()
    print(f"\n📄 Found {len(documents)} validated documents")
    
    # Track performance per template, strategy, and field
    performance = defaultdict(lambda: {
        'total': 0,
        'correct': 0
    })
    
    for doc in documents:
        template_id = doc['template_id']
        extraction_result = json.loads(doc['extraction_result'])
        
        # Parse corrections
        corrections = {}
        if doc['corrections']:
            for correction in doc['corrections'].split('||'):
                if ':' in correction:
                    field, value = correction.split(':', 1)
                    corrections[field] = value
        
        # Check each field
        extracted_data = extraction_result.get('extracted_data', {})
        extraction_methods = extraction_result.get('extraction_methods', {})
        
        for field_name, extracted_value in extracted_data.items():
            method = extraction_methods.get(field_name, 'unknown')
            strategy_type = method
            
            # ✅ UNIFY: Treat 'crf-model' same as 'crf' (both use same CRF model)
            if strategy_type == 'crf-model':
                strategy_type = 'crf'
            
            # Check if extraction was correct
            if field_name in corrections:
                # Had correction = was incorrect
                is_correct = False
            else:
                # No correction = was correct
                is_correct = True
            
            # Track overall performance
            key_overall = (template_id, strategy_type, None)  # None = all fields
            performance[key_overall]['total'] += 1
            if is_correct:
                performance[key_overall]['correct'] += 1
            
            # Track per-field performance
            key_field = (template_id, strategy_type, field_name)
            performance[key_field]['total'] += 1
            if is_correct:
                performance[key_field]['correct'] += 1
    
    # Insert into database
    print(f"\n💾 Inserting performance data...")
    
    for (template_id, strategy_type, field_name), stats in performance.items():
        total = stats['total']
        correct = stats['correct']
        accuracy = correct / total if total > 0 else 0.0
        
        # Use 'ALL' instead of NULL for overall performance
        field_name_db = field_name if field_name else 'ALL'
        
        cursor.execute('''
            INSERT OR REPLACE INTO strategy_performance 
            (template_id, strategy_type, field_name, accuracy, total_extractions, correct_extractions, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (template_id, strategy_type, field_name_db, accuracy, total, correct))
        
        print(f"  ✅ Template {template_id} | {strategy_type:15s} | {field_name_db:20s} | {accuracy:.2%} ({correct}/{total})")
    
    conn.commit()
    
    # Show summary
    print(f"\n{'='*80}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'='*80}")
    
    cursor.execute('''
        SELECT 
            strategy_type,
            COUNT(*) as field_count,
            AVG(accuracy) as avg_accuracy,
            SUM(total_extractions) as total_extractions
        FROM strategy_performance
        WHERE template_id = 1 AND field_name IS NULL
        GROUP BY strategy_type
        ORDER BY avg_accuracy DESC
    ''')
    
    for row in cursor.fetchall():
        print(f"{row['strategy_type']:15s}: {row['avg_accuracy']:.2%} ({row['total_extractions']} extractions)")
    
    conn.close()
    print(f"\n✅ Strategy performance populated!")

if __name__ == '__main__':
    populate_performance()
