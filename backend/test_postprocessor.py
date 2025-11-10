#!/usr/bin/env python3
"""
Test PostProcessor functionality
"""
import sys
from database.db_manager import DatabaseManager
from core.extraction.post_processor import AdaptivePostProcessor

def main():
    print("=" * 70)
    print("🧪 Testing PostProcessor")
    print("=" * 70)
    
    # Initialize database
    db = DatabaseManager()
    
    # Create PostProcessor
    print("\n1️⃣ Creating PostProcessor...")
    try:
        post_processor = AdaptivePostProcessor(template_id=1, db_manager=db)
        print(f"✅ PostProcessor created successfully")
    except Exception as e:
        print(f"❌ Failed to create PostProcessor: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check loaded patterns
    print(f"\n2️⃣ Checking loaded patterns...")
    patterns = post_processor.learned_patterns
    print(f"   Loaded patterns for {len(patterns)} fields:")
    for field_name in ['issue_place', 'supervisor_name', 'chairman_name', 'event_location']:
        if field_name in patterns:
            p = patterns[field_name]
            print(f"   - {field_name}:")
            print(f"       Prefixes: {p.get('common_prefixes', [])}")
            print(f"       Suffixes: {p.get('common_suffixes', [])}")
            print(f"       Structural: {list(p.get('structural_noise', {}).keys())}")
    
    # Test cleaning
    print(f"\n3️⃣ Testing cleaning...")
    test_cases = [
        ('issue_place', 'Biak Numfor, 07 November 2025', 'Biak Numfor'),
        ('supervisor_name', 'H. Eman Pranowo, M.TI.) (Puti Ophelia Wibowo', 'H. Eman Pranowo, M.TI.'),
        ('chairman_name', '(Puti Ophelia Wibowo)', 'Puti Ophelia Wibowo'),
    ]
    
    passed = 0
    failed = 0
    
    for field_name, original, expected in test_cases:
        cleaned = post_processor.clean_value(field_name, original)
        status = '✅' if cleaned == expected else '❌'
        if cleaned == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n   {status} {field_name}:")
        print(f"       Original:  '{original}'")
        print(f"       Expected:  '{expected}'")
        print(f"       Cleaned:   '{cleaned}'")
        if cleaned != expected:
            print(f"       ⚠️  MISMATCH!")
    
    # Summary
    print(f"\n" + "=" * 70)
    print(f"📊 Test Summary:")
    print(f"   Passed: {passed}/{len(test_cases)}")
    print(f"   Failed: {failed}/{len(test_cases)}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
