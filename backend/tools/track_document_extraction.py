#!/usr/bin/env python3
"""
Document Extraction Tracker

Detailed tracking of extraction process for a specific document:
- Strategy selection per field
- Confidence scores
- Extraction results vs ground truth
- Why certain strategies were chosen/rejected

Usage:
    python track_document_extraction.py --document-id 149
"""

import sys
import os
from pathlib import Path
import json
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class Database:
    def __init__(self):
        self.db_path = 'data/app.db'
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def track_document(doc_id: int):
    """Track extraction for specific document"""
    db = Database()
    conn = db.get_connection()
    
    print("\n" + "=" * 80)
    print(f"  📄 DOCUMENT EXTRACTION TRACKER: ID {doc_id}")
    print("=" * 80 + "\n")
    
    # Get document info
    cursor = conn.execute("""
        SELECT d.*, t.name as template_name
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
    print(f"✅ Status: {doc['status']}")
    print(f"📅 Created: {doc['created_at']}")
    
    # Parse extraction results
    extraction_result = json.loads(doc['extraction_result'])
    extracted_data = extraction_result.get('extracted_data', {})
    confidence_scores = extraction_result.get('confidence_scores', {})
    metadata = extraction_result.get('metadata', {})
    strategies_used = metadata.get('strategies_used', [])
    
    print(f"\n⏱️  Extraction Time: {metadata.get('extraction_time', 'N/A')}")
    print(f"📊 Fields Extracted: {len(extracted_data)}")
    
    # Get feedback/corrections
    cursor = conn.execute("""
        SELECT field_name, original_value, corrected_value
        FROM feedback
        WHERE document_id = ?
        ORDER BY field_name
    """, (doc_id,))
    
    feedbacks = cursor.fetchall()
    feedback_dict = {fb['field_name']: fb for fb in feedbacks}
    
    print(f"📝 Corrections: {len(feedbacks)}")
    
    # Get strategy performance for this template
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
    
    # Analyze each field
    print("\n" + "=" * 80)
    print("  📊 FIELD-BY-FIELD ANALYSIS")
    print("=" * 80)
    
    # Group by accuracy
    perfect_fields = []
    good_fields = []
    poor_fields = []
    failed_fields = []
    
    for field_name in sorted(extracted_data.keys()):
        extracted = extracted_data.get(field_name, '')
        confidence = confidence_scores.get(field_name, 0.0)
        feedback = feedback_dict.get(field_name)
        
        # Determine if correct
        is_correct = True
        ground_truth = None
        if feedback:
            ground_truth = feedback['corrected_value']
            is_correct = (str(extracted).strip() == str(ground_truth).strip())
        
        # Find strategy used
        strategy_info = None
        for s in strategies_used:
            if s.get('field_name') == field_name:
                strategy_info = s
                break
        
        strategy_used = strategy_info.get('method', 'unknown') if strategy_info else 'unknown'
        
        # Get historical performance
        field_perf = perf_by_field.get(field_name, [])
        field_perf_sorted = sorted(field_perf, key=lambda x: x['accuracy'], reverse=True)
        
        # Categorize
        if is_correct:
            if confidence >= 0.9:
                perfect_fields.append((field_name, confidence, strategy_used))
            else:
                good_fields.append((field_name, confidence, strategy_used))
        else:
            if not extracted or extracted.strip() == '':
                failed_fields.append((field_name, strategy_used, ground_truth, field_perf_sorted))
            else:
                poor_fields.append((field_name, extracted, ground_truth, confidence, strategy_used, field_perf_sorted))
    
    # Print perfect fields
    if perfect_fields:
        print(f"\n✅ PERFECT EXTRACTION ({len(perfect_fields)} fields)")
        print("-" * 80)
        for field, conf, strategy in perfect_fields[:5]:
            print(f"   {field:25} | Conf: {conf:.2f} | Strategy: {strategy}")
        if len(perfect_fields) > 5:
            print(f"   ... and {len(perfect_fields) - 5} more")
    
    # Print good fields
    if good_fields:
        print(f"\n🟢 GOOD EXTRACTION ({len(good_fields)} fields)")
        print("-" * 80)
        for field, conf, strategy in good_fields:
            print(f"   {field:25} | Conf: {conf:.2f} | Strategy: {strategy}")
    
    # Print poor fields (wrong extraction)
    if poor_fields:
        print(f"\n🟡 POOR EXTRACTION ({len(poor_fields)} fields)")
        print("-" * 80)
        for field, extracted, truth, conf, strategy, perf in poor_fields:
            print(f"\n   🔸 {field}")
            print(f"      Strategy Used: {strategy} (Conf: {conf:.2f})")
            print(f"      Extracted: '{extracted[:60]}'")
            print(f"      Truth:     '{truth[:60]}'")
            
            # Show why this strategy was chosen
            if perf:
                print(f"      Historical Performance:")
                for p in perf[:3]:
                    status = "✅" if p['accuracy'] > 0.7 else "🟡" if p['accuracy'] > 0.3 else "🔴"
                    print(f"         {status} {p['strategy']:12} | Acc: {p['accuracy']:.1%} ({p['attempts']} attempts)")
                
                # Check if better strategy exists
                best_strategy = perf[0]
                if best_strategy['strategy'] != strategy and best_strategy['accuracy'] > 0.5:
                    print(f"      ⚠️  Better strategy available: {best_strategy['strategy']} ({best_strategy['accuracy']:.1%})")
    
    # Print failed fields (empty extraction)
    if failed_fields:
        print(f"\n🔴 FAILED EXTRACTION ({len(failed_fields)} fields)")
        print("-" * 80)
        for field, strategy, truth, perf in failed_fields:
            print(f"\n   🔸 {field}")
            print(f"      Strategy Used: {strategy}")
            print(f"      Expected: '{truth[:60]}'")
            
            if perf:
                print(f"      Historical Performance:")
                for p in perf[:3]:
                    status = "✅" if p['accuracy'] > 0.7 else "🟡" if p['accuracy'] > 0.3 else "🔴"
                    print(f"         {status} {p['strategy']:12} | Acc: {p['accuracy']:.1%} ({p['attempts']} attempts)")
                
                # Check if any strategy works
                best_strategy = perf[0]
                if best_strategy['accuracy'] > 0.5:
                    print(f"      💡 Try: {best_strategy['strategy']} ({best_strategy['accuracy']:.1%} accuracy)")
                else:
                    print(f"      ⚠️  No strategy works well for this field (best: {best_strategy['accuracy']:.1%})")
    
    # Summary
    print("\n" + "=" * 80)
    print("  📊 SUMMARY")
    print("=" * 80)
    
    total_fields = len(extracted_data)
    correct_fields = len(perfect_fields) + len(good_fields)
    accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 0
    
    print(f"\n   Total Fields: {total_fields}")
    print(f"   ✅ Perfect: {len(perfect_fields)} ({len(perfect_fields)/total_fields*100:.1f}%)")
    print(f"   🟢 Good: {len(good_fields)} ({len(good_fields)/total_fields*100:.1f}%)")
    print(f"   🟡 Poor: {len(poor_fields)} ({len(poor_fields)/total_fields*100:.1f}%)")
    print(f"   🔴 Failed: {len(failed_fields)} ({len(failed_fields)/total_fields*100:.1f}%)")
    print(f"\n   📈 Overall Accuracy: {accuracy:.1f}%")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("  💡 RECOMMENDATIONS")
    print("=" * 80 + "\n")
    
    if failed_fields:
        print(f"1. 🔴 {len(failed_fields)} fields failed to extract")
        print(f"   → Check if these fields exist in template config")
        print(f"   → Review extraction patterns/rules")
        print(f"   → Consider training CRF model for these fields\n")
    
    if poor_fields:
        print(f"2. 🟡 {len(poor_fields)} fields extracted incorrectly")
        print(f"   → Review strategy selection logic")
        print(f"   → Check if better strategies are available but not used")
        print(f"   → Improve confidence threshold\n")
    
    # Check if unused feedback
    cursor = conn.execute("""
        SELECT COUNT(*) as unused
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ? AND f.used_for_training = 0
    """, (doc['template_id'],))
    
    unused_count = cursor.fetchone()['unused']
    if unused_count > 50:
        print(f"3. 🔄 {unused_count} unused feedback records")
        print(f"   → Trigger retraining to use these corrections")
        print(f"   → Model will learn from recent feedback\n")
    
    conn.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Track document extraction')
    parser.add_argument('--document-id', type=int, required=True, help='Document ID to track')
    
    args = parser.parse_args()
    
    try:
        track_document(args.document_id)
    except KeyboardInterrupt:
        print("\n\n❌ Tracking cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Tracking failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
