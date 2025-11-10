#!/usr/bin/env python3
"""
Retrain CRF model with improved sequence matching
"""

from database.db_manager import DatabaseManager
from core.learning.services import ModelService

def main():
    print("🔄 Retraining CRF model with sequence-based matching...")
    print("=" * 70)
    
    db = DatabaseManager()
    model_service = ModelService(db)
    
    # Train with all feedback
    result = model_service.retrain_model(
        template_id=1,
        model_folder='models',
        use_all_feedback=True
    )
    
    print("\n" + "=" * 70)
    print("📊 TRAINING RESULTS:")
    print("=" * 70)
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if 'metrics' in result:
        metrics = result['metrics']
        print(f"\n📈 Metrics:")
        print(f"  - Test Accuracy: {metrics.get('test_accuracy', 0) * 100:.2f}%")
        print(f"  - Training Samples: {metrics.get('training_samples', 0)}")
        print(f"  - Test Samples: {metrics.get('test_samples', 0)}")
        
        if 'field_metrics' in metrics:
            print(f"\n📊 Per-Field Metrics:")
            for field, field_metrics in metrics['field_metrics'].items():
                print(f"  - {field}: {field_metrics.get('f1', 0) * 100:.1f}% F1")
    
    print("\n✅ Retraining complete!")
    print("\n💡 Now test with: python batch_seeder.py --template certificate_template --generate --count 5")

if __name__ == '__main__':
    main()
