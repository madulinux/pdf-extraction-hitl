#!/usr/bin/env python3
"""
Debug CRF extraction for issue_place field
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import json
import pdfplumber
from core.extraction.strategies import CRFExtractionStrategy

def main():
    print("=" * 80)
    print("🔍 Debug CRF for issue_place")
    print("=" * 80)
    
    # Get latest certificate document
    conn = sqlite3.connect('data/app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT d.id, d.file_path, d.template_id, d.extraction_result,
               t.config_path
        FROM documents d
        JOIN templates t ON d.template_id = t.id
        WHERE d.template_id = 1
        ORDER BY d.id DESC
        LIMIT 1
    """)
    doc = cursor.fetchone()
    conn.close()
    
    if not doc:
        print("❌ No documents found!")
        return
    
    print(f"\n📄 Document ID: {doc['id']}")
    print(f"📄 PDF: {doc['file_path']}")
    
    # Load template config
    with open(doc['config_path'], 'r') as f:
        template_config = json.load(f)
    
    # Extract words from PDF
    print(f"\n📖 Extracting words from PDF...")
    all_words = []
    try:
        with pdfplumber.open(doc['file_path']) as pdf:
            for page in pdf.pages:
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                all_words.extend(words)
        print(f"   Total words: {len(all_words)}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Initialize CRF strategy
    model_path = f"models/template_{doc['template_id']}_model.joblib"
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    print(f"\n🤖 Loading CRF model: {model_path}")
    crf_strategy = CRFExtractionStrategy(model_path)
    
    # Test extraction for issue_place
    field_name = 'issue_place'
    print(f"\n🎯 Testing field: {field_name}")
    print("-" * 80)
    
    # Get field config
    field_config = template_config['fields'].get(field_name)
    if not field_config:
        print(f"❌ Field config not found!")
        return
    
    field_config['field_name'] = field_name
    
    # Extract
    print(f"\n🔍 Extracting with CRF...")
    result = crf_strategy.extract(doc['file_path'], field_config, all_words)
    
    print(f"\n📊 Result:")
    if result:
        print(f"   ✅ Success!")
        print(f"   Value: {result.value}")
        print(f"   Confidence: {result.confidence:.4f}")
        print(f"   Token count: {result.metadata.get('token_count', 0)}")
    else:
        print(f"   ❌ CRF returned None")
        print(f"   Check logs above for details")
    
    # Compare with extraction result
    if doc['extraction_result']:
        extraction_result = json.loads(doc['extraction_result'])
        strategies = extraction_result['metadata']['strategies_used']
        
        for s in strategies:
            if s['field_name'] == field_name:
                print(f"\n📝 From extraction result:")
                print(f"   Selected method: {s['method']}")
                print(f"   Confidence: {s['confidence']}")
                
                attempts = s.get('all_strategies_attempted', {})
                print(f"\n   All strategies:")
                for strategy, info in attempts.items():
                    print(f"     {strategy}: success={info['success']}, conf={info['confidence']:.4f}")
                    if info['value']:
                        print(f"       value: {info['value'][:50]}")
    
    # Check ground truth
    print(f"\n📝 Ground truth (from JSON):")
    json_path = doc['file_path'].replace('.pdf', '.json')
    try:
        with open(json_path, 'r') as f:
            ground_truth = json.load(f)
            print(f"   {ground_truth.get(field_name, 'N/A')}")
    except:
        print(f"   (JSON not found)")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
