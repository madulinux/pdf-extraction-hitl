#!/usr/bin/env python3
"""
Test strategy scoring logic
"""

from database.db_manager import DatabaseManager

db = DatabaseManager()

# Get performance for event_location
conn = db.get_connection()
cursor = conn.execute("""
    SELECT strategy_type, accuracy, total_extractions, correct_extractions
    FROM strategy_performance
    WHERE template_id = 1 AND field_name = 'event_location'
    ORDER BY strategy_type
""")

print("📊 Strategy Performance for event_location:")
print("=" * 70)

for row in cursor.fetchall():
    strategy = row[0]
    accuracy = row[1]
    total = row[2]
    correct = row[3]
    
    print(f"\n{strategy}:")
    print(f"  Total attempts: {total}")
    print(f"  Correct: {correct}")
    print(f"  Accuracy: {accuracy * 100:.2f}%")
    
    # Determine weights
    if total >= 10:
        weights = {'confidence': 0.15, 'strategy': 0.05, 'performance': 0.80}
        category = 'proven'
    elif total >= 5:
        weights = {'confidence': 0.20, 'strategy': 0.10, 'performance': 0.70}
        category = 'established'
    else:
        weights = {'confidence': 0.35, 'strategy': 0.25, 'performance': 0.40}
        category = 'new'
    
    print(f"  Category: {category}")
    print(f"  Weights: conf={weights['confidence']}, strat={weights['strategy']}, perf={weights['performance']}")
    
    # Example scoring with CRF conf=0.96, rule conf=0.19
    if strategy == 'crf':
        conf = 0.96
    elif strategy == 'rule_based':
        conf = 0.19
    else:
        conf = 0.95
    
    strategy_weight = 0.5  # Default
    
    score = (
        conf * weights['confidence'] +
        strategy_weight * weights['strategy'] +
        accuracy * weights['performance']
    )
    
    print(f"  Example score (conf={conf:.2f}): {score:.4f}")

print("\n" + "=" * 70)
