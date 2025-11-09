#!/usr/bin/env python3
"""
Quick test for adaptive rule-based learning

Tests the full workflow:
1. Generate test documents
2. Extract with current rules
3. Submit corrections (feedback)
4. Analyze patterns
5. Apply learned patterns
6. Re-extract and compare
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.db_manager import DatabaseManager
from core.extraction.rule_optimizer import RulePatternOptimizer
import json


def main():
    print("=" * 80)
    print("🧪 Testing Adaptive Rule-Based Learning")
    print("=" * 80)
    
    # Initialize
    db = DatabaseManager('data/app.db')
    optimizer = RulePatternOptimizer(db)
    
    # Test with invoice template
    template_id = 1
    field_name = 'invoice_number'
    
    print(f"\n📊 Step 1: Analyze current feedback")
    print("-" * 80)
    
    analysis = optimizer.analyze_feedback_patterns(
        template_id=template_id,
        field_name=field_name,
        min_frequency=2  # Low threshold for testing
    )
    
    if not analysis:
        print("❌ No feedback data found")
        print("   Please run batch_seeder first to generate feedback")
        db.close()
        return
    
    print(f"✅ Found {analysis['total_feedback']} feedback entries")
    print(f"   Unique values: {analysis['unique_corrected']}")
    
    # Show discovered patterns
    patterns = analysis.get('patterns', {})
    print(f"\n🔍 Discovered Patterns:")
    
    if patterns.get('token_shapes'):
        print(f"\n   Token Shapes (top 3):")
        for shape, freq in list(patterns['token_shapes'].items())[:3]:
            print(f"      {shape}: {freq}x")
    
    if patterns.get('delimiters'):
        print(f"\n   Delimiters:")
        for delim, freq in patterns['delimiters'].items():
            print(f"      '{delim}': {freq}x")
    
    # Show suggestions
    suggestions = analysis.get('suggestions', [])
    print(f"\n💡 Generated {len(suggestions)} regex suggestions:")
    
    for i, sugg in enumerate(suggestions[:5], 1):  # Top 5
        print(f"\n   {i}. {sugg['description']}")
        print(f"      Pattern: {sugg['pattern']}")
        print(f"      Frequency: {sugg['frequency']}")
        if sugg.get('examples'):
            print(f"      Examples: {', '.join(sugg['examples'][:2])}")
    
    # Validate patterns
    if suggestions:
        print(f"\n✓ Step 2: Validate patterns")
        print("-" * 80)
        
        # Get test values
        cursor = db.conn.execute("""
            SELECT DISTINCT f.corrected_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ? AND f.field_name = ?
            LIMIT 50
        """, (template_id, field_name))
        
        test_values = [row[0] for row in cursor.fetchall() if row[0]]
        
        if test_values:
            patterns_to_test = [s['pattern'] for s in suggestions[:3]]
            results = optimizer.validate_patterns(patterns_to_test, test_values)
            
            print(f"Testing {len(patterns_to_test)} patterns against {len(test_values)} values:")
            
            for pattern, result in results.items():
                if result['valid']:
                    match_rate = result['match_rate'] * 100
                    print(f"\n   Pattern: {pattern[:50]}...")
                    print(f"      ✅ Valid - Matches: {result['matches']}/{len(test_values)} ({match_rate:.1f}%)")
                else:
                    print(f"\n   Pattern: {pattern[:50]}...")
                    print(f"      ❌ Invalid: {result['error']}")
    
    # Show next steps
    print(f"\n📝 Next Steps:")
    print("-" * 80)
    print(f"1. Review suggestions above")
    print(f"2. Apply patterns:")
    print(f"   python tools/optimize_rules.py apply --template {template_id} --field {field_name} --auto")
    print(f"3. Test extraction:")
    print(f"   cd ../tools/seeder && python batch_seeder.py --template invoice_template --generate --count 5")
    print(f"4. Compare accuracy before/after")
    
    # Save analysis
    output_file = f"test_analysis_{template_id}_{field_name}.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Full analysis saved to: {output_file}")
    
    db.close()
    
    print("\n" + "=" * 80)
    print("✅ Test completed!")
    print("=" * 80)


if __name__ == '__main__':
    main()
