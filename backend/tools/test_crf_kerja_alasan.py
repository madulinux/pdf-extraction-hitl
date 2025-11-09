#!/usr/bin/env python3
"""
Test CRF extraction for kerja_alasan field to debug why it returns None
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.database.manager import DatabaseManager
from core.extraction.services import ExtractionService
import json

def main():
    print("=" * 80)
    print("🔍 Testing CRF Extraction for kerja_alasan")
    print("=" * 80)
    
    # Initialize
    db = DatabaseManager('data/app.db')
    service = ExtractionService(db)
    
    # Get latest document
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT id, pdf_path, template_id, extraction_result
        FROM documents
        WHERE template_id = 1
        ORDER BY id DESC
        LIMIT 1
    """)
    doc = cursor.fetchone()
    conn.close()
    
    if not doc:
        print("❌ No documents found!")
        return
    
    print(f"\n📄 Document ID: {doc['id']}")
    print(f"📄 PDF: {doc['pdf_path']}")
    print(f"📄 Template ID: {doc['template_id']}")
    
    # Parse extraction result
    extraction_result = json.loads(doc['extraction_result'])
    
    # Check kerja_alasan
    print(f"\n🎯 Checking field: kerja_alasan")
    print("-" * 80)
    
    # Find kerja_alasan in strategies_used
    strategies_used = extraction_result.get('metadata', {}).get('strategies_used', [])
    kerja_alasan_info = None
    for strategy in strategies_used:
        if strategy.get('field_name') == 'kerja_alasan':
            kerja_alasan_info = strategy
            break
    
    if kerja_alasan_info:
        print(f"✅ Found in strategies_used:")
        print(json.dumps(kerja_alasan_info, indent=2))
        
        # Check all_strategies_attempted
        all_attempts = kerja_alasan_info.get('all_strategies_attempted', {})
        if all_attempts:
            print(f"\n📊 All strategies attempted:")
            for strategy_name, attempt_info in all_attempts.items():
                print(f"\n  {strategy_name}:")
                print(f"    Success: {attempt_info.get('success')}")
                print(f"    Confidence: {attempt_info.get('confidence')}")
                print(f"    Value: {attempt_info.get('value', '')[:100]}...")
        else:
            print(f"\n⚠️ NO all_strategies_attempted metadata!")
    else:
        print(f"❌ kerja_alasan NOT found in strategies_used!")
    
    # Check extracted value
    extracted_value = extraction_result.get('extracted_data', {}).get('kerja_alasan', '')
    print(f"\n📝 Extracted value: {extracted_value[:200]}...")
    
    # Check feedback
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT original_value, corrected_value
        FROM feedback
        WHERE document_id = ? AND field_name = 'kerja_alasan'
    """, (doc['id'],))
    feedback = cursor.fetchone()
    conn.close()
    
    if feedback:
        print(f"\n✏️ Feedback:")
        print(f"  Original: {feedback['original_value'][:200]}...")
        print(f"  Corrected: {feedback['corrected_value'][:200]}...")
        print(f"  Match: {feedback['original_value'] == feedback['corrected_value']}")
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()
