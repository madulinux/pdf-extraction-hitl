#!/usr/bin/env python3
"""
Trace hybrid strategy decision for a specific document
Shows what each strategy extracted and why hybrid chose what it did
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pdfplumber
from database.db_manager import DatabaseManager
from core.extraction.strategies import (
    CRFExtractionStrategy,
    RuleBasedExtractionStrategy,
    PositionExtractionStrategy
)

def trace_extraction(doc_id: int):
    """Trace extraction for a specific document"""
    
    print("="*80)
    print(f"🔍 TRACING HYBRID EXTRACTION DECISION - Document {doc_id}")
    print("="*80)
    
    # Get document
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, t.config_path, t.name as template_name
        FROM documents d
        JOIN templates t ON d.template_id = t.id
        WHERE d.id = ?
    ''', (doc_id,))
    
    doc = cursor.fetchone()
    if not doc:
        print(f"❌ Document {doc_id} not found")
        return
    
    print(f"\n📄 Document: {os.path.basename(doc['file_path'])}")
    print(f"📋 Template: {doc['template_name']}")
    
    # Load template config
    with open(doc['config_path'], 'r') as f:
        template_config = json.load(f)
    
    # Extract words
    with pdfplumber.open(doc['file_path']) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)
    
    print(f"📝 Total words: {len(words)}")
    
    # Get model path
    model_path = f"models/template_{doc['template_id']}_model.joblib"
    
    # Initialize strategies
    strategies = {}
    
    if os.path.exists(model_path):
        strategies['CRF'] = CRFExtractionStrategy(model_path)
        print(f"✅ CRF strategy loaded")
    else:
        print(f"❌ CRF model not found: {model_path}")
        return
    
    strategies['Rule-Based'] = RuleBasedExtractionStrategy()
    strategies['Position-Based'] = PositionExtractionStrategy()
    
    print(f"✅ All strategies initialized\n")
    
    # Extract with each strategy
    print("="*80)
    print("📊 EXTRACTION RESULTS BY STRATEGY")
    print("="*80)
    
    fields = template_config.get('fields', {})
    
    for field_name, field_config in fields.items():
        print(f"\n{'='*80}")
        print(f"🔍 Field: {field_name}")
        print(f"{'='*80}")
        
        results = {}
        
        # Try each strategy
        for strategy_name, strategy in strategies.items():
            try:
                # Add field_name to config for CRF
                field_config_with_name = dict(field_config)
                field_config_with_name['field_name'] = field_name
                
                if strategy_name == 'CRF':
                    result = strategy.extract(doc['file_path'], field_config_with_name, words)
                else:
                    result = strategy.extract(words, field_name, field_config)
                
                results[strategy_name] = result
                
                if result and result.value:
                    print(f"\n✅ {strategy_name}:")
                    print(f"   Value: '{result.value}'")
                    print(f"   Confidence: {result.confidence:.4f}")
                    print(f"   Method: {result.method}")
                else:
                    print(f"\n❌ {strategy_name}: No result")
                    
            except Exception as e:
                print(f"\n❌ {strategy_name}: Error - {e}")
                results[strategy_name] = None
        
        # Show what hybrid chose
        print(f"\n{'─'*80}")
        extraction_result = json.loads(doc['extraction_result'])
        chosen_value = extraction_result['extracted_data'].get(field_name, 'N/A')
        chosen_method = extraction_result['extraction_methods'].get(field_name, 'N/A')
        chosen_confidence = extraction_result['confidence_scores'].get(field_name, 0)
        
        print(f"🎯 HYBRID CHOSE:")
        print(f"   Value: '{chosen_value}'")
        print(f"   Method: {chosen_method}")
        print(f"   Confidence: {chosen_confidence:.4f}")
        
        # Analyze decision
        print(f"\n💡 ANALYSIS:")
        
        crf_result = results.get('CRF')
        if crf_result and crf_result.value:
            if chosen_method == 'hybrid-crf':
                print(f"   ✅ Correctly chose CRF (highest confidence)")
            else:
                print(f"   ⚠️  DID NOT choose CRF despite having result!")
                print(f"   CRF value: '{crf_result.value}' (conf: {crf_result.confidence:.4f})")
                print(f"   Chosen: {chosen_method} (conf: {chosen_confidence:.4f})")
                
                # Calculate why
                if chosen_confidence > crf_result.confidence:
                    print(f"   Reason: Other strategy has higher confidence")
                else:
                    print(f"   ⚠️  UNEXPECTED: CRF has higher confidence but wasn't chosen!")
        else:
            print(f"   ℹ️  CRF had no result, fallback to other strategies")
    
    conn.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Trace hybrid extraction decision')
    parser.add_argument('--doc-id', type=int, required=True, help='Document ID to trace')
    
    args = parser.parse_args()
    trace_extraction(args.doc_id)
