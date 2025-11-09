#!/usr/bin/env python3
"""
Diagnose training data quality for CRF model
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.db_manager import DatabaseManager
from core.learning.data_preparation import prepare_training_data_from_feedback
from core.extraction.template_config_loader import TemplateConfigLoader
import json

def diagnose_training_data(template_id: int):
    """Diagnose training data quality"""
    print("\n" + "=" * 80)
    print(f"  🔬 DIAGNOSING TRAINING DATA: Template {template_id}")
    print("=" * 80)
    
    db = DatabaseManager()
    
    # Get feedback
    print("\n📊 Fetching feedback data...")
    feedback_by_doc = db.get_feedback_by_document(template_id)
    print(f"   Documents with feedback: {len(feedback_by_doc)}")
    
    total_feedback = sum(len(feedbacks) for feedbacks in feedback_by_doc.values())
    print(f"   Total feedback records: {total_feedback}")
    
    # Load template config
    print("\n📋 Loading template config...")
    config_loader = TemplateConfigLoader()
    template = db.get_template_by_id(template_id)
    if not template:
        print(f"❌ Template {template_id} not found!")
        return False
    
    template_config = config_loader.load_config(template['config_path'])
    print(f"   Template: {template['name']}")
    print(f"   Fields: {len(template_config.get('fields', {}))}")
    
    # Prepare training data
    print("\n🔄 Preparing training data...")
    try:
        X_train, y_train = prepare_training_data_from_feedback(
            feedback_by_doc,
            template_config,
            db
        )
        print(f"✅ Training data prepared successfully")
        print(f"   Training samples: {len(X_train)}")
        print(f"   Label sequences: {len(y_train)}")
    except Exception as e:
        print(f"❌ Failed to prepare training data: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Analyze labels
    print("\n🏷️  LABEL ANALYSIS:")
    all_labels = set()
    label_counts = {}
    
    for labels in y_train:
        for label in labels:
            all_labels.add(label)
            label_counts[label] = label_counts.get(label, 0) + 1
    
    print(f"   Unique labels: {len(all_labels)}")
    print(f"   Total label instances: {sum(label_counts.values())}")
    
    # Group by field
    field_labels = {}
    for label in all_labels:
        if label == 'O':
            continue
        field = label.split('-', 1)[1] if '-' in label else label
        if field not in field_labels:
            field_labels[field] = []
        field_labels[field].append(label)
    
    print(f"\n   Labels by field ({len(field_labels)} fields):")
    for field in sorted(field_labels.keys()):
        labels = field_labels[field]
        b_count = label_counts.get(f'B-{field}', 0)
        i_count = label_counts.get(f'I-{field}', 0)
        print(f"      {field:25s}: B={b_count:4d}, I={i_count:4d}, Total={b_count+i_count:4d}")
    
    o_count = label_counts.get('O', 0)
    print(f"\n   'O' (outside) labels: {o_count}")
    
    # Check for imbalance
    print("\n⚖️  LABEL BALANCE:")
    non_o_count = sum(label_counts.values()) - o_count
    o_ratio = o_count / sum(label_counts.values()) * 100
    print(f"   'O' labels: {o_count} ({o_ratio:.1f}%)")
    print(f"   Non-'O' labels: {non_o_count} ({100-o_ratio:.1f}%)")
    
    if o_ratio > 95:
        print(f"   ⚠️  WARNING: Very high 'O' ratio ({o_ratio:.1f}%) - model may struggle to learn field labels")
    elif o_ratio > 90:
        print(f"   ⚠️  CAUTION: High 'O' ratio ({o_ratio:.1f}%) - consider more training data")
    else:
        print(f"   ✅ Good balance")
    
    # Check feature quality
    print("\n🔍 FEATURE ANALYSIS:")
    if X_train:
        sample_features = X_train[0][0] if X_train[0] else {}
        print(f"   Features per word: {len(sample_features)}")
        
        # Check for field-aware features
        field_aware_features = [k for k in sample_features.keys() if k.startswith('target_field_')]
        if field_aware_features:
            print(f"   ✅ Field-aware features found: {len(field_aware_features)}")
            print(f"      Sample: {field_aware_features[:3]}")
        else:
            print(f"   ❌ NO field-aware features found!")
            print(f"      This is a CRITICAL issue - model cannot distinguish fields!")
        
        # Show sample features
        print(f"\n   Sample features (first word):")
        for key, value in list(sample_features.items())[:10]:
            print(f"      {key}: {value}")
    
    # Check for missing fields
    print("\n🔍 MISSING FIELD CHECK:")
    expected_fields = set(template_config.get('fields', {}).keys())
    found_fields = set(field_labels.keys())
    
    missing = expected_fields - found_fields
    if missing:
        print(f"   ⚠️  Missing fields in training data: {missing}")
    else:
        print(f"   ✅ All fields present in training data")
    
    extra = found_fields - expected_fields
    if extra:
        print(f"   ⚠️  Extra fields in training data: {extra}")
    
    print("\n" + "=" * 80)
    print("✅ Diagnosis complete!")
    print("=" * 80)
    
    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Diagnose training data quality')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    args = parser.parse_args()
    
    try:
        success = diagnose_training_data(args.template_id)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Diagnosis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
