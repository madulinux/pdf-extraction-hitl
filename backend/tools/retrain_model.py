#!/usr/bin/env python3
"""
Quick script to retrain model with context features
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from core.learning.services import ModelService

def main():
    print("="*80)
    print("🎓 RETRAINING MODEL WITH CONTEXT FEATURES")
    print("="*80)
    
    # Initialize services
    db = DatabaseManager()
    model_service = ModelService(db)
    
    # Retrain template 1
    template_id = 1
    print(f"\n📊 Retraining template {template_id}...")
    print(f"   This will use ALL feedback (including previously used)")
    
    try:
        result = model_service.retrain_model(
            template_id=template_id,
            use_all_feedback=True,  # Use all feedback
            model_folder='models'
        )
        
        print("\n" + "="*80)
        print("✅ TRAINING COMPLETE!")
        print("="*80)
        print(f"\n📊 Results:")
        print(f"   Training samples: {result.get('training_samples', 0)}")
        print(f"   Test samples: {result.get('test_samples', 0)}")
        print(f"   Accuracy: {result.get('accuracy', 0)*100:.2f}%")
        print(f"   Precision: {result.get('precision', 0)*100:.2f}%")
        print(f"   Recall: {result.get('recall', 0)*100:.2f}%")
        print(f"   F1-score: {result.get('f1_score', 0)*100:.2f}%")
        print(f"\n   Model saved to: {result.get('model_path', 'N/A')}")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
