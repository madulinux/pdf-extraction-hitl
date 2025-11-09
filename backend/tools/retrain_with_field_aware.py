#!/usr/bin/env python3
"""
Retrain CRF Model with Field-Aware Features

This script triggers retraining with the new field-aware features implementation.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from core.learning.services import ModelService


def retrain_model(template_id: int):
    """Retrain model with field-aware features"""
    print("\n" + "=" * 80)
    print(f"  🔄 RETRAINING MODEL WITH FIELD-AWARE FEATURES")
    print("=" * 80 + "\n")
    
    db = DatabaseManager()
    model_service = ModelService(db)
    
    print(f"📊 Template ID: {template_id}")
    print(f"🎯 Using ALL feedback for training")
    print(f"✨ Field-aware features: ENABLED\n")
    
    try:
        result = model_service.retrain_model(
            template_id=template_id,
            use_all_feedback=True,
            model_folder='models',
            is_incremental=False,  # Full retrain with new features
            force_validation=False
        )
        
        print("\n" + "=" * 80)
        print("  ✅ RETRAINING COMPLETED")
        print("=" * 80 + "\n")
        
        print(f"📈 Training Results:")
        print(f"   Samples: {result.get('training_samples', 0)}")
        print(f"   Accuracy: {result.get('accuracy', 0):.2%}")
        print(f"   Precision: {result.get('precision', 0):.2%}")
        print(f"   Recall: {result.get('recall', 0):.2%}")
        print(f"   F1 Score: {result.get('f1_score', 0):.2%}")
        
        print(f"\n💾 Model saved to: {result.get('model_path', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Retraining failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrain model with field-aware features')
    parser.add_argument('--template-id', type=int, default=1, help='Template ID (default: 1)')
    
    args = parser.parse_args()
    
    try:
        success = retrain_model(args.template_id)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Retraining cancelled by user")
        sys.exit(1)
