#!/usr/bin/env python3
"""
Test Strategy Performance Fix

Verifies that strategy_performance table is correctly populated with field_name.
"""

import sys
import os
from pathlib import Path
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_strategy_performance():
    """Test strategy performance tracking"""
    db_path = 'data/app.db'
    
    print("\n" + "=" * 80)
    print("  🧪 TESTING STRATEGY PERFORMANCE FIX")
    print("=" * 80 + "\n")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Check total records
    cursor.execute("SELECT COUNT(*) as total FROM strategy_performance")
    total = cursor.fetchone()['total']
    print(f"📊 Total records: {total}")
    
    # 2. Check NULL field_name
    cursor.execute("SELECT COUNT(*) as null_count FROM strategy_performance WHERE field_name IS NULL")
    null_count = cursor.fetchone()['null_count']
    print(f"❌ NULL field_name: {null_count}")
    
    # 3. Check unique fields
    cursor.execute("SELECT COUNT(DISTINCT field_name) as unique_fields FROM strategy_performance WHERE field_name IS NOT NULL")
    unique_fields = cursor.fetchone()['unique_fields']
    print(f"✅ Unique fields: {unique_fields}")
    
    # 4. Show sample data
    print(f"\n📋 Sample records:")
    cursor.execute("""
        SELECT template_id, field_name, strategy_type, accuracy, total_extractions
        FROM strategy_performance
        WHERE field_name IS NOT NULL
        ORDER BY last_updated DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    if rows:
        print(f"{'Template':<10} {'Field':<25} {'Strategy':<15} {'Accuracy':<10} {'Count':<10}")
        print("-" * 80)
        for row in rows:
            print(f"{row['template_id']:<10} {row['field_name']:<25} {row['strategy_type']:<15} {row['accuracy']:<10.2%} {row['total_extractions']:<10}")
    else:
        print("   No records found")
    
    # 5. Check per-field breakdown
    print(f"\n📊 Per-field breakdown:")
    cursor.execute("""
        SELECT field_name, COUNT(*) as strategy_count, SUM(total_extractions) as total_attempts
        FROM strategy_performance
        WHERE field_name IS NOT NULL
        GROUP BY field_name
        ORDER BY field_name
    """)
    
    field_rows = cursor.fetchall()
    if field_rows:
        print(f"{'Field':<25} {'Strategies':<12} {'Total Attempts':<15}")
        print("-" * 52)
        for row in field_rows:
            print(f"{row['field_name']:<25} {row['strategy_count']:<12} {row['total_attempts']:<15}")
    else:
        print("   No field data found")
    
    conn.close()
    
    # Verdict
    print(f"\n" + "=" * 80)
    if null_count == 0 and unique_fields > 0:
        print("✅ PASS: Strategy performance tracking is working correctly!")
        print(f"   - No NULL field_name records")
        print(f"   - {unique_fields} unique fields tracked")
        print(f"   - {total} total performance records")
    else:
        print("❌ FAIL: Strategy performance tracking has issues!")
        if null_count > 0:
            print(f"   - {null_count} records with NULL field_name")
        if unique_fields == 0:
            print(f"   - No fields are being tracked")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    try:
        test_strategy_performance()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
