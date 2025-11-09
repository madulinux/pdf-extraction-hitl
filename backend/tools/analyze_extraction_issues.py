#!/usr/bin/env python3
"""
Comprehensive Analysis Tool for Extraction Issues

Analyzes why extraction results are not improving despite training with 100+ documents.
Focuses on:
1. Strategy selection logic
2. Training data quality
3. Model performance
4. Feedback utilization
5. Field-specific issues

Usage:
    python analyze_extraction_issues.py [--document-id 130]
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3

class Database:
    def __init__(self):
        self.db_path = 'data/app.db'
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def analyze_document(doc_id: int, db: Database):
    """Analyze specific document extraction"""
    conn = db.get_connection()
    
    print_section(f"📄 DOCUMENT ANALYSIS: ID {doc_id}")
    
    # Get document info
    cursor = conn.execute("""
        SELECT d.id, d.filename, d.template_id, t.name as template_name, 
               d.status, d.created_at
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
    
    # Get feedback/corrections
    cursor = conn.execute("""
        SELECT field_name, original_value, corrected_value, used_for_training
        FROM feedback
        WHERE document_id = ?
        ORDER BY field_name
    """, (doc_id,))
    
    feedbacks = cursor.fetchall()
    
    print(f"\n📊 Corrections: {len(feedbacks)} fields")
    print("-" * 80)
    
    issues = {
        'wrong_extraction': [],
        'empty_extraction': [],
        'partial_extraction': []
    }
    
    for fb in feedbacks:
        field = fb['field_name']
        original = fb['original_value'] or ''
        corrected = fb['corrected_value'] or ''
        used = fb['used_for_training']
        
        # Classify issue
        if not original or original.strip() == '':
            issue_type = 'empty_extraction'
        elif len(original) < len(corrected) * 0.5:
            issue_type = 'partial_extraction'
        else:
            issue_type = 'wrong_extraction'
        
        issues[issue_type].append({
            'field': field,
            'original': original[:80],
            'corrected': corrected[:80],
            'used': used
        })
    
    # Print issues by type
    for issue_type, items in issues.items():
        if items:
            print(f"\n🔴 {issue_type.replace('_', ' ').title()}: {len(items)} fields")
            for item in items[:5]:  # Show first 5
                print(f"   • {item['field']}")
                print(f"     Extracted: '{item['original']}'")
                print(f"     Correct:   '{item['corrected']}'")
                print(f"     Used for training: {'✅' if item['used'] else '❌'}")


def analyze_strategy_performance(template_id: int, db: Database):
    """Analyze strategy performance"""
    conn = db.get_connection()
    
    print_section("📈 STRATEGY PERFORMANCE ANALYSIS")
    
    cursor = conn.execute("""
        SELECT field_name, strategy_type, 
               total_extractions, correct_extractions, accuracy
        FROM strategy_performance
        WHERE template_id = ?
        ORDER BY field_name, accuracy DESC
    """, (template_id,))
    
    perfs = cursor.fetchall()
    
    # Group by field
    by_field = {}
    for p in perfs:
        field = p['field_name']
        if field not in by_field:
            by_field[field] = []
        by_field[field].append(p)
    
    print(f"📊 Fields analyzed: {len(by_field)}")
    print("-" * 80)
    
    problematic_fields = []
    
    for field, strategies in by_field.items():
        best_strategy = max(strategies, key=lambda x: x['accuracy'])
        worst_strategy = min(strategies, key=lambda x: x['accuracy'])
        
        # Check if best strategy is still poor
        if best_strategy['accuracy'] < 0.5:
            problematic_fields.append({
                'field': field,
                'best_acc': best_strategy['accuracy'],
                'best_strategy': best_strategy['strategy_type'],
                'total_attempts': sum(s['total_extractions'] for s in strategies)
            })
        
        print(f"\n🔹 {field}")
        for s in strategies:
            status = "🟢" if s['accuracy'] > 0.7 else "🟡" if s['accuracy'] > 0.3 else "🔴"
            print(f"   {status} {s['strategy_type']:15} | "
                  f"Acc: {s['accuracy']:.1%} | "
                  f"Correct: {s['correct_extractions']}/{s['total_extractions']}")
    
    if problematic_fields:
        print("\n" + "=" * 80)
        print("⚠️  PROBLEMATIC FIELDS (Best accuracy < 50%)")
        print("=" * 80)
        for pf in sorted(problematic_fields, key=lambda x: x['best_acc']):
            print(f"   🔴 {pf['field']:25} | Best: {pf['best_acc']:.1%} ({pf['best_strategy']}) | "
                  f"Attempts: {pf['total_attempts']}")


def analyze_training_data(template_id: int, db: Database):
    """Analyze training data quality"""
    conn = db.get_connection()
    
    print_section("🎓 TRAINING DATA ANALYSIS")
    
    # Total feedback
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN used_for_training = 1 THEN 1 ELSE 0 END) as used,
            SUM(CASE WHEN used_for_training = 0 THEN 1 ELSE 0 END) as unused
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ?
    """, (template_id,))
    
    stats = cursor.fetchone()
    
    print(f"📊 Total Feedback: {stats['total']}")
    print(f"   ✅ Used for training: {stats['used']} ({stats['used']/stats['total']*100:.1f}%)")
    print(f"   ⏳ Unused: {stats['unused']} ({stats['unused']/stats['total']*100:.1f}%)")
    
    # Check if model exists
    model_path = f"models/template_{template_id}_model.joblib"
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / 1024  # KB
        mtime = datetime.fromtimestamp(os.path.getmtime(model_path))
        print(f"\n🤖 CRF Model: {model_path}")
        print(f"   Size: {size:.1f} KB")
        print(f"   Last updated: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n❌ CRF Model not found: {model_path}")
    
    # Feedback per field
    cursor = conn.execute("""
        SELECT field_name, 
               COUNT(*) as total,
               SUM(CASE WHEN used_for_training = 1 THEN 1 ELSE 0 END) as used
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ?
        GROUP BY field_name
        ORDER BY total DESC
    """, (template_id,))
    
    field_stats = cursor.fetchall()
    
    print(f"\n📋 Feedback per Field:")
    print("-" * 80)
    for fs in field_stats[:10]:  # Top 10
        print(f"   {fs['field_name']:25} | Total: {fs['total']:3} | "
              f"Used: {fs['used']:3} ({fs['used']/fs['total']*100:.0f}%)")


def analyze_adaptive_learning(template_id: int, db: Database):
    """Analyze adaptive learning behavior"""
    conn = db.get_connection()
    
    print_section("🔄 ADAPTIVE LEARNING ANALYSIS")
    
    # Check strategy weight adjustments over time
    cursor = conn.execute("""
        SELECT field_name, strategy_type, accuracy, last_updated
        FROM strategy_performance
        WHERE template_id = ?
        ORDER BY last_updated DESC
        LIMIT 20
    """, (template_id,))
    
    recent = cursor.fetchall()
    
    print("📅 Recent Strategy Updates (Last 20):")
    print("-" * 80)
    for r in recent:
        print(f"   {r['field_name']:25} | {r['strategy_type']:12} | "
              f"Acc: {r['accuracy']:.1%} | {r['last_updated']}")
    
    # Check if learning is happening
    cursor = conn.execute("""
        SELECT COUNT(DISTINCT field_name) as fields_learning
        FROM strategy_performance
        WHERE template_id = ? AND total_extractions > 10
    """, (template_id,))
    
    learning = cursor.fetchone()
    print(f"\n📊 Fields with >10 extractions: {learning['fields_learning']}")


def identify_root_causes(template_id: int, db: Database):
    """Identify root causes of poor performance"""
    conn = db.get_connection()
    
    print_section("🔍 ROOT CAUSE ANALYSIS")
    
    issues = []
    
    # Issue 1: Unused feedback
    cursor = conn.execute("""
        SELECT COUNT(*) as unused
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ? AND f.used_for_training = 0
    """, (template_id,))
    unused = cursor.fetchone()['unused']
    
    if unused > 100:
        issues.append({
            'severity': '🔴 CRITICAL',
            'issue': f'{unused} feedback records NOT used for training',
            'impact': 'Model tidak belajar dari koreksi user',
            'solution': 'Trigger retraining dengan feedback yang belum digunakan'
        })
    
    # Issue 2: Rule-based dominance
    cursor = conn.execute("""
        SELECT strategy_type, SUM(total_extractions) as total
        FROM strategy_performance
        WHERE template_id = ?
        GROUP BY strategy_type
    """, (template_id,))
    
    strategy_usage = {row['strategy_type']: row['total'] for row in cursor.fetchall()}
    total_extractions = sum(strategy_usage.values())
    
    if strategy_usage.get('rule_based', 0) / total_extractions > 0.7:
        issues.append({
            'severity': '🟡 WARNING',
            'issue': f'Rule-based strategy dominates ({strategy_usage.get("rule_based", 0)/total_extractions:.1%})',
            'impact': 'CRF model tidak digunakan secara optimal',
            'solution': 'Review strategy selection logic dan CRF confidence threshold'
        })
    
    # Issue 3: Poor CRF performance
    cursor = conn.execute("""
        SELECT AVG(accuracy) as avg_acc, COUNT(*) as fields
        FROM strategy_performance
        WHERE template_id = ? AND strategy_type = 'crf'
    """, (template_id,))
    
    crf_stats = cursor.fetchone()
    if crf_stats['avg_acc'] and crf_stats['avg_acc'] < 0.5:
        issues.append({
            'severity': '🟡 WARNING',
            'issue': f'CRF average accuracy is low ({crf_stats["avg_acc"]:.1%})',
            'impact': 'Model CRF tidak efektif untuk template ini',
            'solution': 'Review feature engineering dan training data quality'
        })
    
    # Issue 4: Insufficient training data per field
    cursor = conn.execute("""
        SELECT field_name, COUNT(*) as samples
        FROM feedback f
        JOIN documents d ON f.document_id = d.id
        WHERE d.template_id = ? AND f.used_for_training = 1
        GROUP BY field_name
        HAVING samples < 20
    """, (template_id,))
    
    low_sample_fields = cursor.fetchall()
    if low_sample_fields:
        issues.append({
            'severity': '🟡 WARNING',
            'issue': f'{len(low_sample_fields)} fields have <20 training samples',
            'impact': 'Model tidak cukup data untuk belajar pattern field tersebut',
            'solution': 'Generate lebih banyak dokumen atau fokus pada field dengan data cukup'
        })
    
    # Print issues
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue['severity']} {issue['issue']}")
            print(f"   💥 Impact: {issue['impact']}")
            print(f"   💡 Solution: {issue['solution']}")
            print()
    else:
        print("✅ No critical issues detected!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze extraction issues')
    parser.add_argument('--document-id', type=int, help='Specific document to analyze')
    parser.add_argument('--template-id', type=int, default=1, help='Template ID (default: 1)')
    
    args = parser.parse_args()
    
    db = Database()
    
    print("\n" + "🔬 " * 40)
    print("  COMPREHENSIVE EXTRACTION ANALYSIS")
    print("🔬 " * 40)
    
    # Analyze specific document if provided
    if args.document_id:
        analyze_document(args.document_id, db)
    
    # Analyze strategy performance
    analyze_strategy_performance(args.template_id, db)
    
    # Analyze training data
    analyze_training_data(args.template_id, db)
    
    # Analyze adaptive learning
    analyze_adaptive_learning(args.template_id, db)
    
    # Identify root causes
    identify_root_causes(args.template_id, db)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
