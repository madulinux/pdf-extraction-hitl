#!/usr/bin/env python3
"""
Rule Pattern Optimization Tool

Analyzes feedback and suggests/applies new regex patterns
for rule-based extraction strategy.

Usage:
    # Analyze patterns for a field
    python tools/optimize_rules.py analyze --template 1 --field invoice_number
    
    # Apply suggested patterns
    python tools/optimize_rules.py apply --template 1 --field invoice_number --auto
    
    # Validate patterns
    python tools/optimize_rules.py validate --template 1 --field invoice_number
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import json
from database.db_manager import DatabaseManager
from core.extraction.rule_optimizer import RulePatternOptimizer


def analyze_patterns(args):
    """Analyze feedback patterns for a field"""
    print("=" * 80)
    print(f"🔍 Analyzing patterns for field: {args.field}")
    print(f"   Template ID: {args.template}")
    print("=" * 80)
    
    db = DatabaseManager('data/app.db')
    optimizer = RulePatternOptimizer(db)
    
    analysis = optimizer.analyze_feedback_patterns(
        template_id=args.template,
        field_name=args.field,
        min_frequency=args.min_freq
    )
    
    if not analysis:
        print("❌ No analysis results")
        return
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total feedback: {analysis['total_feedback']}")
    print(f"   Unique values: {analysis['unique_corrected']}")
    
    print(f"\n🔍 Discovered Patterns:")
    patterns = analysis.get('patterns', {})
    
    if patterns.get('token_shapes'):
        print(f"\n   Token Shapes:")
        for shape, freq in list(patterns['token_shapes'].items())[:5]:
            print(f"      {shape}: {freq} occurrences")
    
    if patterns.get('word_counts'):
        print(f"\n   Word Counts:")
        for count, freq in list(patterns['word_counts'].items())[:5]:
            print(f"      {count} words: {freq} occurrences")
    
    if patterns.get('delimiters'):
        print(f"\n   Delimiters:")
        for delim, freq in patterns['delimiters'].items():
            print(f"      '{delim}': {freq} occurrences")
    
    print(f"\n💡 Regex Suggestions:")
    suggestions = analysis.get('suggestions', [])
    
    if not suggestions:
        print("   No suggestions generated")
    else:
        for i, sugg in enumerate(suggestions, 1):
            print(f"\n   {i}. {sugg['description']}")
            print(f"      Pattern: {sugg['pattern']}")
            print(f"      Type: {sugg['type']}")
            print(f"      Frequency: {sugg['frequency']}")
            if sugg.get('examples'):
                print(f"      Examples: {', '.join(sugg['examples'][:3])}")
    
    # Save to file
    output_file = f"analysis_{args.template}_{args.field}.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\n💾 Full analysis saved to: {output_file}")
    
    db.close()


def apply_patterns(args):
    """Apply suggested patterns to template config"""
    print("=" * 80)
    print(f"🔧 Applying patterns for field: {args.field}")
    print(f"   Template ID: {args.template}")
    print("=" * 80)
    
    db = DatabaseManager('data/app.db')
    optimizer = RulePatternOptimizer(db)
    
    # Get template config path
    cursor = db.conn.execute(
        "SELECT config_path FROM templates WHERE id = ?",
        (args.template,)
    )
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Template {args.template} not found")
        db.close()
        return
    
    config_path = row[0]
    print(f"📄 Config: {config_path}")
    
    # Analyze patterns
    analysis = optimizer.analyze_feedback_patterns(
        template_id=args.template,
        field_name=args.field,
        min_frequency=args.min_freq
    )
    
    suggestions = analysis.get('suggestions', [])
    
    if not suggestions:
        print("❌ No patterns to apply")
        db.close()
        return
    
    print(f"\n💡 Found {len(suggestions)} pattern suggestions")
    
    # Filter patterns if not auto mode
    patterns_to_apply = []
    
    if args.auto:
        # Auto mode: apply top patterns with high frequency
        patterns_to_apply = [
            s for s in suggestions
            if s['frequency'] >= args.min_freq
        ][:args.max_patterns]
        print(f"   Auto-applying top {len(patterns_to_apply)} patterns")
    else:
        # Interactive mode
        print("\nSelect patterns to apply (comma-separated numbers, or 'all'):")
        for i, sugg in enumerate(suggestions, 1):
            print(f"   {i}. {sugg['description']} (freq: {sugg['frequency']})")
            print(f"      Pattern: {sugg['pattern']}")
        
        choice = input("\nYour choice: ").strip()
        
        if choice.lower() == 'all':
            patterns_to_apply = suggestions
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                patterns_to_apply = [suggestions[i] for i in indices if 0 <= i < len(suggestions)]
            except (ValueError, IndexError):
                print("❌ Invalid selection")
                db.close()
                return
    
    if not patterns_to_apply:
        print("❌ No patterns selected")
        db.close()
        return
    
    # Apply patterns
    print(f"\n🔧 Applying {len(patterns_to_apply)} patterns...")
    
    success = optimizer.update_template_config(
        config_path=config_path,
        field_name=args.field,
        new_patterns=patterns_to_apply,
        backup=True
    )
    
    if success:
        print("✅ Patterns applied successfully!")
        print(f"   Config updated: {config_path}")
        print(f"   Backup created")
    else:
        print("❌ Failed to apply patterns")
    
    db.close()


def validate_patterns(args):
    """Validate patterns against test data"""
    print("=" * 80)
    print(f"✓ Validating patterns for field: {args.field}")
    print(f"   Template ID: {args.template}")
    print("=" * 80)
    
    db = DatabaseManager('data/app.db')
    optimizer = RulePatternOptimizer(db)
    
    # Get test values from feedback
    query = """
        SELECT DISTINCT f.corrected_value
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ? AND f.field_name = ?
        LIMIT 100
    """
    
    cursor = db.conn.execute(query, (args.template, args.field))
    test_values = [row[0] for row in cursor.fetchall() if row[0]]
    
    if not test_values:
        print("❌ No test values found")
        db.close()
        return
    
    print(f"📊 Testing against {len(test_values)} values")
    
    # Get template config
    cursor = db.conn.execute(
        "SELECT config_path FROM templates WHERE id = ?",
        (args.template,)
    )
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Template {args.template} not found")
        db.close()
        return
    
    config_path = row[0]
    
    # Load patterns from config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    field_config = config.get('fields', {}).get(args.field, {})
    learned_patterns = field_config.get('rules', {}).get('learned_patterns', [])
    
    if not learned_patterns:
        print("❌ No learned patterns found in config")
        db.close()
        return
    
    print(f"\n🔍 Found {len(learned_patterns)} learned patterns")
    
    # Validate each pattern
    patterns = [p['pattern'] for p in learned_patterns]
    results = optimizer.validate_patterns(patterns, test_values)
    
    print(f"\n📊 Validation Results:")
    for pattern, result in results.items():
        print(f"\n   Pattern: {pattern}")
        if result['valid']:
            print(f"      ✅ Valid")
            print(f"      Matches: {result['matches']}/{len(test_values)} ({result['match_rate']*100:.1f}%)")
            if result['examples']:
                print(f"      Examples:")
                for ex in result['examples']:
                    print(f"         '{ex['value']}' → '{ex['matched']}'")
        else:
            print(f"      ❌ Invalid: {result['error']}")
    
    db.close()


def main():
    parser = argparse.ArgumentParser(description='Rule Pattern Optimization Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze feedback patterns')
    analyze_parser.add_argument('--template', type=int, required=True, help='Template ID')
    analyze_parser.add_argument('--field', type=str, required=True, help='Field name')
    analyze_parser.add_argument('--min-freq', type=int, default=3, help='Minimum frequency')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply patterns to config')
    apply_parser.add_argument('--template', type=int, required=True, help='Template ID')
    apply_parser.add_argument('--field', type=str, required=True, help='Field name')
    apply_parser.add_argument('--min-freq', type=int, default=3, help='Minimum frequency')
    apply_parser.add_argument('--max-patterns', type=int, default=5, help='Max patterns to apply')
    apply_parser.add_argument('--auto', action='store_true', help='Auto-apply top patterns')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate patterns')
    validate_parser.add_argument('--template', type=int, required=True, help='Template ID')
    validate_parser.add_argument('--field', type=str, required=True, help='Field name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'analyze':
        analyze_patterns(args)
    elif args.command == 'apply':
        apply_patterns(args)
    elif args.command == 'validate':
        validate_patterns(args)


if __name__ == '__main__':
    main()
