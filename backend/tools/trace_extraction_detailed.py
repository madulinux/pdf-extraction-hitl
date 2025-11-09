#!/usr/bin/env python3
"""
Detailed Extraction Tracer

Traces extraction process for a specific document:
- Shows results from EACH strategy (rule-based, position, CRF)
- Shows confidence scores for each
- Shows why certain strategy was selected
- Shows historical performance data used in decision

Usage:
    python trace_extraction_detailed.py --document-id 167
"""

import sys
import os
from pathlib import Path
import json
import sqlite3
import pdfplumber

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.extraction.strategies import (
    RuleBasedExtractionStrategy,
    PositionExtractionStrategy,
    CRFExtractionStrategy
)


class Database:
    def __init__(self):
        self.db_path = 'data/app.db'
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def extract_words_from_pdf(pdf_path):
    """Extract words from PDF"""
    all_words = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                all_words.extend(words)
    except Exception as e:
        print(f"❌ Error extracting words: {e}")
    return all_words


def trace_document(doc_id: int):
    """Trace extraction for specific document"""
    db = Database()
    conn = db.get_connection()
    
    print("\n" + "=" * 100)
    print(f"  🔬 DETAILED EXTRACTION TRACER: Document ID {doc_id}")
    print("=" * 100 + "\n")
    
    # Get document info
    cursor = conn.execute("""
        SELECT d.*, t.name as template_name, t.config_path
        FROM documents d
        JOIN templates t ON d.template_id = t.id
        WHERE d.id = ?
    """, (doc_id,))
    
    doc = cursor.fetchone()
    if not doc:
        print(f"❌ Document {doc_id} not found!")
        return
    
    print(f"📋 Document: {doc['filename']}")
    print(f"📝 Template: {doc['template_name']} (ID: {doc['template_id']})")
    print(f"📁 Path: {doc['file_path']}")
    
    # Load template config
    if not doc['config_path'] or not os.path.exists(doc['config_path']):
        print(f"❌ Template config not found: {doc['config_path']}")
        return
    
    with open(doc['config_path'], 'r') as f:
        template_config = json.load(f)
    
    # Check model
    model_path = f"models/template_{doc['template_id']}_model.joblib"
    has_model = os.path.exists(model_path)
    print(f"🤖 CRF Model: {'✅ Available' if has_model else '❌ Not found'} ({model_path})")
    
    # Extract words
    print(f"\n📄 Extracting words from PDF...")
    all_words = extract_words_from_pdf(doc['file_path'])
    print(f"   Found {len(all_words)} words")
    
    # Initialize strategies
    rule_strategy = RuleBasedExtractionStrategy()
    pos_strategy = PositionExtractionStrategy()
    crf_strategy = CRFExtractionStrategy(model_path) if has_model else None
    
    # Get feedback/corrections
    cursor = conn.execute("""
        SELECT field_name, original_value, corrected_value
        FROM feedback
        WHERE document_id = ?
        ORDER BY field_name
    """, (doc_id,))
    
    feedbacks = cursor.fetchall()
    feedback_dict = {fb['field_name']: fb for fb in feedbacks}
    
    # Get historical performance
    cursor = conn.execute("""
        SELECT field_name, strategy_type, accuracy, total_extractions
        FROM strategy_performance
        WHERE template_id = ?
    """, (doc['template_id'],))
    
    perf_rows = cursor.fetchall()
    perf_by_field = {}
    for row in perf_rows:
        field = row['field_name']
        if field not in perf_by_field:
            perf_by_field[field] = []
        perf_by_field[field].append({
            'strategy': row['strategy_type'],
            'accuracy': row['accuracy'],
            'attempts': row['total_extractions']
        })
    
    # Parse extraction results
    extraction_result = json.loads(doc['extraction_result'])
    extracted_data = extraction_result.get('extracted_data', {})
    confidence_scores = extraction_result.get('confidence_scores', {})
    extraction_methods = extraction_result.get('extraction_methods', {})
    
    # Trace each field
    print("\n" + "=" * 100)
    print("  🔍 FIELD-BY-FIELD EXTRACTION TRACE")
    print("=" * 100)
    
    fields = template_config.get('fields', {})
    
    for field_name in sorted(fields.keys()):
        field_config = fields[field_name].copy()
        field_config['field_name'] = field_name
        
        print(f"\n{'─' * 100}")
        print(f"🔸 Field: {field_name}")
        print(f"{'─' * 100}")
        
        # Get ground truth
        feedback = feedback_dict.get(field_name)
        ground_truth = feedback['corrected_value'] if feedback else None
        
        # Get what was extracted
        final_value = extracted_data.get(field_name, '')
        final_confidence = confidence_scores.get(field_name, 0.0)
        final_method = extraction_methods.get(field_name, 'unknown')
        
        # Show final result first
        is_correct = False
        if ground_truth:
            is_correct = (str(final_value).strip() == str(ground_truth).strip())
            status = "✅ CORRECT" if is_correct else "❌ WRONG"
            print(f"\n📊 FINAL RESULT: {status}")
            print(f"   Selected Strategy: {final_method}")
            print(f"   Confidence: {final_confidence:.4f}")
            print(f"   Extracted: '{final_value[:80]}'")
            print(f"   Truth:     '{ground_truth[:80]}'")
        else:
            print(f"\n📊 FINAL RESULT:")
            print(f"   Selected Strategy: {final_method}")
            print(f"   Confidence: {final_confidence:.4f}")
            print(f"   Extracted: '{final_value[:80]}'")
        
        # Now trace each strategy
        print(f"\n🔬 STRATEGY RESULTS:")
        
        # 1. Rule-based
        print(f"\n   1️⃣  RULE-BASED:")
        try:
            rule_result = rule_strategy.extract(doc['file_path'], field_config, all_words)
            if rule_result:
                rule_correct = (str(rule_result.value).strip() == str(ground_truth).strip()) if ground_truth else None
                status = "✅" if rule_correct else "❌" if rule_correct is False else "❓"
                print(f"      {status} Value: '{rule_result.value[:60]}'")
                print(f"      Confidence: {rule_result.confidence:.4f}")
                print(f"      Method: {rule_result.method}")
            else:
                print(f"      ❌ No result (returned None)")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        # 2. Position-based
        print(f"\n   2️⃣  POSITION-BASED:")
        try:
            pos_result = pos_strategy.extract(doc['file_path'], field_config, all_words)
            if pos_result:
                pos_correct = (str(pos_result.value).strip() == str(ground_truth).strip()) if ground_truth else None
                status = "✅" if pos_correct else "❌" if pos_correct is False else "❓"
                print(f"      {status} Value: '{pos_result.value[:60]}'")
                print(f"      Confidence: {pos_result.confidence:.4f}")
                print(f"      Method: {pos_result.method}")
            else:
                print(f"      ❌ No result (returned None)")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        # 3. CRF
        print(f"\n   3️⃣  CRF:")
        if crf_strategy:
            try:
                crf_result = crf_strategy.extract(doc['file_path'], field_config, all_words)
                if crf_result:
                    crf_correct = (str(crf_result.value).strip() == str(ground_truth).strip()) if ground_truth else None
                    status = "✅" if crf_correct else "❌" if crf_correct is False else "❓"
                    print(f"      {status} Value: '{crf_result.value[:60]}'")
                    print(f"      Confidence: {crf_result.confidence:.4f}")
                    print(f"      Method: {crf_result.method}")
                else:
                    print(f"      ❌ No result (returned None)")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        else:
            print(f"      ⚠️  Model not available")
        
        # Show historical performance
        field_perf = perf_by_field.get(field_name, [])
        if field_perf:
            print(f"\n📈 HISTORICAL PERFORMANCE:")
            field_perf_sorted = sorted(field_perf, key=lambda x: x['accuracy'], reverse=True)
            for p in field_perf_sorted:
                status = "✅" if p['accuracy'] > 0.7 else "🟡" if p['accuracy'] > 0.3 else "🔴"
                print(f"      {status} {p['strategy']:15s}: {p['accuracy']:.1%} accuracy ({p['attempts']} attempts)")
        
        # Analysis
        print(f"\n💡 ANALYSIS:")
        
        # Check if correct strategy was chosen
        if ground_truth:
            strategies_correctness = []
            
            # Check rule-based
            try:
                rule_result = rule_strategy.extract(doc['file_path'], field_config, all_words)
                if rule_result:
                    is_rule_correct = (str(rule_result.value).strip() == str(ground_truth).strip())
                    strategies_correctness.append(('rule_based', is_rule_correct, rule_result.confidence))
            except:
                pass
            
            # Check position
            try:
                pos_result = pos_strategy.extract(doc['file_path'], field_config, all_words)
                if pos_result:
                    is_pos_correct = (str(pos_result.value).strip() == str(ground_truth).strip())
                    strategies_correctness.append(('position_based', is_pos_correct, pos_result.confidence))
            except:
                pass
            
            # Check CRF
            if crf_strategy:
                try:
                    crf_result = crf_strategy.extract(doc['file_path'], field_config, all_words)
                    if crf_result:
                        is_crf_correct = (str(crf_result.value).strip() == str(ground_truth).strip())
                        strategies_correctness.append(('crf', is_crf_correct, crf_result.confidence))
                except:
                    pass
            
            # Find which strategies got it right
            correct_strategies = [s for s in strategies_correctness if s[1]]
            
            if not is_correct and correct_strategies:
                print(f"      ⚠️  WRONG STRATEGY SELECTED!")
                print(f"      Selected: {final_method} (WRONG)")
                print(f"      Should use: {', '.join([s[0] for s in correct_strategies])} (CORRECT)")
                
                # Show why wrong strategy was chosen
                for strat, _, conf in correct_strategies:
                    perf = [p for p in field_perf if p['strategy'] == strat]
                    if perf:
                        p = perf[0]
                        print(f"         → {strat}: conf={conf:.4f}, hist_acc={p['accuracy']:.1%} ({p['attempts']} attempts)")
            elif is_correct:
                print(f"      ✅ Correct strategy selected: {final_method}")
            else:
                print(f"      ❌ No strategy got it right")
                if strategies_correctness:
                    print(f"      All strategies failed:")
                    for strat, _, conf in strategies_correctness:
                        print(f"         → {strat}: conf={conf:.4f} (WRONG)")
    
    conn.close()
    
    # Summary
    print(f"\n{'=' * 100}")
    print(f"  📊 SUMMARY")
    print(f"{'=' * 100}\n")
    
    total_fields = len(fields)
    correct_count = sum(1 for fn in fields.keys() 
                       if fn in feedback_dict and 
                       str(extracted_data.get(fn, '')).strip() == str(feedback_dict[fn]['corrected_value']).strip())
    
    print(f"Total Fields: {total_fields}")
    print(f"Correct: {correct_count} ({correct_count/total_fields*100:.1f}%)")
    print(f"Wrong: {total_fields - correct_count} ({(total_fields-correct_count)/total_fields*100:.1f}%)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Trace detailed extraction')
    parser.add_argument('--document-id', type=int, required=True, help='Document ID to trace')
    
    args = parser.parse_args()
    
    try:
        trace_document(args.document_id)
    except KeyboardInterrupt:
        print("\n\n❌ Tracing cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Tracing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
