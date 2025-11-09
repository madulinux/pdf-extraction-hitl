"""
Debug scoring for document 145
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

from database.db_manager import DatabaseManager
import json

db = DatabaseManager()
conn = db.get_connection()

# Get document 145 extraction result
cursor = conn.execute("SELECT extraction_result FROM documents WHERE id = 145")
row = cursor.fetchone()
result = json.loads(row['extraction_result'])

strategies = result['metadata']['strategies_used']

print("📊 DOCUMENT 145 - STRATEGY SELECTION ANALYSIS")
print("=" * 80)

# Focus on problematic fields
problem_fields = ['event_date', 'issue_date']

for field_name in problem_fields:
    print(f"\n🎯 Field: {field_name}")
    print("-" * 80)
    
    # Get selected strategy
    selected = next((s for s in strategies if s['field'] == field_name), None)
    if selected:
        print(f"  Selected: {selected['method']} (confidence: {selected['confidence']:.4f})")
    
    # Get DB performance
    cursor = conn.execute("""
        SELECT strategy_type, ROUND(accuracy * 100, 2) as acc_pct, total_extractions
        FROM strategy_performance
        WHERE template_id = 1 AND field_name = ?
        ORDER BY accuracy DESC
    """, (field_name,))
    
    perf_rows = cursor.fetchall()
    
    print(f"\n  Database Performance:")
    for p in perf_rows:
        print(f"    {p['strategy_type']:15s}: {p['acc_pct']:6.2f}% ({p['total_extractions']} samples)")
    
    # Calculate what scores SHOULD be
    print(f"\n  Score Calculation (formula: conf×0.4 + weight×0.3 + db_acc×0.3):")
    
    # Assume typical values
    strategy_weights = {'rule_based': 0.4, 'position_based': 0.5, 'crf': 0.5}
    
    for p in perf_rows:
        strategy = p['strategy_type']
        db_acc = p['acc_pct'] / 100
        weight = strategy_weights.get(strategy, 0.5)
        
        # We don't know actual confidence, so show formula
        print(f"    {strategy:15s}: conf×0.4 + {weight}×0.3 + {db_acc:.4f}×0.3")
        print(f"                     = conf×0.4 + {weight*0.3:.4f} + {db_acc*0.3:.4f}")
        print(f"                     = conf×0.4 + {weight*0.3 + db_acc*0.3:.4f}")
        
        # For CRF to win, it needs:
        if strategy == 'crf':
            crf_base = weight*0.3 + db_acc*0.3
            print(f"                     → CRF needs conf > ? to beat others")
        elif strategy == 'position_based' and selected and selected['method'] == 'position_based':
            pos_conf = selected['confidence']
            pos_score = pos_conf * 0.4 + weight*0.3 + db_acc*0.3
            print(f"                     → With conf={pos_conf:.4f}: score = {pos_score:.4f}")

print("\n" + "=" * 80)
print("\n💡 CONCLUSION:")
print("If position_based wins, it means:")
print("  1. CRF confidence was too low, OR")
print("  2. Position-based confidence was very high")
print("\nSOLUTION: Increase weight of historical accuracy (db_acc) from 0.3 to 0.4")
print("=" * 80)

conn.close()
