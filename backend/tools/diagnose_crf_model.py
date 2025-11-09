#!/usr/bin/env python3
"""
CRF Model Diagnostic Tool

Checks what labels the CRF model can predict and compares with expected labels.

Usage:
    python diagnose_crf_model.py --template-id 1
"""

import sys
import os
from pathlib import Path
import json
import joblib

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def diagnose_model(template_id: int):
    """Diagnose CRF model"""
    print("\n" + "=" * 80)
    print(f"  🔬 CRF MODEL DIAGNOSTIC: Template ID {template_id}")
    print("=" * 80 + "\n")
    
    # Check model file
    model_path = f"models/template_{template_id}_model.joblib"
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return
    
    print(f"✅ Model file found: {model_path}")
    print(f"   Size: {os.path.getsize(model_path) / 1024:.2f} KB")
    print(f"   Modified: {os.path.getmtime(model_path)}")
    
    # Load model
    print(f"\n📥 Loading model...")
    try:
        model = joblib.load(model_path)
        print(f"✅ Model loaded successfully")
        print(f"   Type: {type(model)}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Check model labels
    print(f"\n🏷️  MODEL LABELS:")
    if hasattr(model, 'classes_'):
        labels = model.classes_
        print(f"   Total labels: {len(labels)}")
        print(f"   Labels: {sorted(labels)}")
        
        # Group by field
        field_labels = {}
        for label in labels:
            if label == 'O':
                continue
            parts = label.split('-', 1)
            if len(parts) == 2:
                prefix, field = parts
                if field not in field_labels:
                    field_labels[field] = []
                field_labels[field].append(prefix)
        
        print(f"\n📊 Labels by field:")
        for field in sorted(field_labels.keys()):
            prefixes = sorted(field_labels[field])
            print(f"      {field:25s}: {', '.join(prefixes)}")
    else:
        print(f"   ⚠️  Model doesn't have 'classes_' attribute")
    
    # Load template config to compare
    print(f"\n📝 EXPECTED FIELDS (from template config):")
    
    # Find template config
    import sqlite3
    conn = sqlite3.connect('data/app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT config_path FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    
    if not row or not row['config_path']:
        print(f"   ⚠️  Template config not found")
        conn.close()
        return
    
    config_path = row['config_path']
    conn.close()
    
    if not os.path.exists(config_path):
        print(f"   ❌ Config file not found: {config_path}")
        return
    
    with open(config_path, 'r') as f:
        template_config = json.load(f)
    
    expected_fields = sorted(template_config.get('fields', {}).keys())
    print(f"   Total fields: {len(expected_fields)}")
    print(f"   Fields: {expected_fields}")
    
    # Compare
    print(f"\n🔍 COMPARISON:")
    
    if hasattr(model, 'classes_'):
        model_fields = set(field_labels.keys())
        expected_fields_set = set(f.upper() for f in expected_fields)
        
        missing_in_model = expected_fields_set - model_fields
        extra_in_model = model_fields - expected_fields_set
        
        if missing_in_model:
            print(f"\n   ❌ MISSING IN MODEL ({len(missing_in_model)} fields):")
            for field in sorted(missing_in_model):
                print(f"      - {field}")
        
        if extra_in_model:
            print(f"\n   ⚠️  EXTRA IN MODEL ({len(extra_in_model)} fields):")
            for field in sorted(extra_in_model):
                print(f"      - {field}")
        
        if not missing_in_model and not extra_in_model:
            print(f"   ✅ All fields match!")
    
    # Check model state
    print(f"\n🔧 MODEL STATE:")
    if hasattr(model, 'state_features_'):
        print(f"   State features: {len(model.state_features_)}")
    if hasattr(model, 'transition_features_'):
        print(f"   Transition features: {len(model.transition_features_)}")
    
    # Try a simple prediction
    print(f"\n🧪 TEST PREDICTION:")
    try:
        # Create dummy features
        test_features = [{
            'word': 'test',
            'word.lower()': 'test',
            'word.isupper()': False,
            'word.istitle()': True,
            'word.isdigit()': False,
        }]
        
        prediction = model.predict([test_features])
        print(f"   ✅ Model can predict")
        print(f"   Sample prediction: {prediction[0]}")
    except Exception as e:
        print(f"   ❌ Prediction failed: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnose CRF model')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    
    args = parser.parse_args()
    
    try:
        diagnose_model(args.template_id)
    except KeyboardInterrupt:
        print("\n\n❌ Diagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
