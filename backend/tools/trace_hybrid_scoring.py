#!/usr/bin/env python3
"""
Trace hybrid scoring calculation for document 298
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from database.db_manager import DatabaseManager

def trace_scoring(doc_id: int):
    """Trace hybrid scoring for specific document"""
    
    print("="*80)
    print(f"🔍 TRACING HYBRID SCORING - Document {doc_id}")
    print("="*80)
    
    # Get document
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT extraction_result FROM documents WHERE id = ?
    ''', (doc_id,))
    
    doc = cursor.fetchone()
    if not doc:
        print(f"❌ Document {doc_id} not found")
        return
    
    extraction_result = json.loads(doc['extraction_result'])
    
    # Get historical performance
    cursor.execute('''
        SELECT strategy_type, accuracy, total_extractions
        FROM strategy_performance
        WHERE template_id = 1
    ''')
    
    performance = {}
    for row in cursor.fetchall():
        performance[row['strategy_type']] = {
            'accuracy': row['accuracy'],
            'total': row['total_extractions']
        }
    
    print("\n📊 HISTORICAL PERFORMANCE:")
    print("="*80)
    for strategy, perf in performance.items():
        print(f"{strategy:20s}: accuracy={perf['accuracy']:.4f}, total={perf['total']}")
    
    # Strategy weights
    weights = {
        'crf': 0.8,  # User just changed this
        'rule_based': 0.5,
        'position_based': 0.5
    }
    
    print("\n⚖️  STRATEGY WEIGHTS:")
    print("="*80)
    for strategy, weight in weights.items():
        print(f"{strategy:20s}: {weight:.2f}")
    
    # Analyze problematic fields
    problematic_fields = ['event_date', 'issue_place', 'issue_date']
    
    print("\n🔍 SCORING ANALYSIS FOR PROBLEMATIC FIELDS:")
    print("="*80)
    
    for field in problematic_fields:
        method = extraction_result['extraction_methods'].get(field, 'N/A')
        confidence = extraction_result['confidence_scores'].get(field, 0)
        value = extraction_result['extracted_data'].get(field, 'N/A')
        
        print(f"\n{'='*80}")
        print(f"Field: {field}")
        print(f"Chosen: {method} (confidence: {confidence:.4f})")
        print(f"Value: '{value}'")
        print(f"{'='*80}")
        
        # Simulate scoring for each strategy
        print("\n📊 Simulated Scoring:")
        
        # We don't have individual strategy results, but we can estimate
        # based on the chosen method
        strategy_type = method.replace('hybrid-', '')
        
        if strategy_type in performance:
            perf = performance[strategy_type]
            weight = weights.get(strategy_type, 0.5)
            
            combined_score = (
                confidence * 0.4 +
                weight * 0.3 +
                perf['accuracy'] * 0.3
            )
            
            print(f"\n{strategy_type}:")
            print(f"  Confidence:  {confidence:.4f} × 0.4 = {confidence*0.4:.4f}")
            print(f"  Weight:      {weight:.4f} × 0.3 = {weight*0.3:.4f}")
            print(f"  Performance: {perf['accuracy']:.4f} × 0.3 = {perf['accuracy']*0.3:.4f}")
            print(f"  ─────────────────────────────────────")
            print(f"  TOTAL:       {combined_score:.4f}")
        
        # Estimate CRF score if it wasn't chosen
        if strategy_type != 'crf' and 'crf' in performance:
            print(f"\n💡 If CRF had similar confidence:")
            crf_perf = performance['crf']
            crf_weight = weights['crf']
            
            # Assume CRF would have slightly higher confidence
            estimated_crf_conf = min(confidence + 0.15, 1.0)
            
            crf_score = (
                estimated_crf_conf * 0.4 +
                crf_weight * 0.3 +
                crf_perf['accuracy'] * 0.3
            )
            
            print(f"  Confidence:  {estimated_crf_conf:.4f} × 0.4 = {estimated_crf_conf*0.4:.4f}")
            print(f"  Weight:      {crf_weight:.4f} × 0.3 = {crf_weight*0.3:.4f}")
            print(f"  Performance: {crf_perf['accuracy']:.4f} × 0.3 = {crf_perf['accuracy']*0.3:.4f}")
            print(f"  ─────────────────────────────────────")
            print(f"  TOTAL:       {crf_score:.4f}")
            
            if crf_score > combined_score:
                print(f"  ✅ CRF would WIN if confidence was {estimated_crf_conf:.4f}")
            else:
                print(f"  ❌ CRF would still LOSE even with {estimated_crf_conf:.4f} confidence")
    
    conn.close()

if __name__ == '__main__':
    trace_scoring(298)
