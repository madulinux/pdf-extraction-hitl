"""
Test hybrid strategy scoring with database performance
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

from database.db_manager import DatabaseManager

db = DatabaseManager()

# Check performance for specific fields
fields = ['event_date', 'issue_place', 'issue_date']

print("📊 STRATEGY PERFORMANCE FROM DATABASE:")
print("=" * 80)

for field in fields:
    print(f"\n🎯 Field: {field}")
    print("-" * 80)
    
    conn = db.get_connection()
    cursor = conn.execute("""
        SELECT 
            strategy_type,
            ROUND(accuracy * 100, 2) as acc_pct,
            total_extractions,
            correct_extractions
        FROM strategy_performance
        WHERE template_id = 1 AND field_name = ?
        ORDER BY accuracy DESC
    """, (field,))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("  No performance data")
        continue
    
    for row in rows:
        strategy = row['strategy_type']
        acc = row['acc_pct']
        total = row['total_extractions']
        correct = row['correct_extractions']
        
        # Calculate score contribution (30% of total score)
        score_contribution = (acc / 100) * 0.3
        
        print(f"  {strategy:15s}: {acc:6.2f}% ({correct}/{total}) → score contrib: {score_contribution:.4f}")
    
    # Show winner
    best = rows[0]
    print(f"  ✅ BEST: {best['strategy_type']} with {best['acc_pct']}% accuracy")

print("\n" + "=" * 80)
print("\n💡 SCORING FORMULA:")
print("  combined_score = (confidence × 0.4) + (strategy_weight × 0.3) + (db_accuracy × 0.3)")
print("\nFor CRF to win, it needs:")
print("  - High confidence from model")
print("  - High historical accuracy from database (now enabled!)")
print("=" * 80)
