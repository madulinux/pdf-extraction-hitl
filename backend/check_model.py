#!/usr/bin/env python3
"""
Script to check CRF model status and debug issues
"""
import os
import sys
import joblib
from pathlib import Path
from database.repositories.feedback_repository import FeedbackRepository


def check_model_status(template_id: int = 1):
    """Check CRF model status for a template"""

    print("=" * 60)
    print("🔍 CRF MODEL STATUS CHECK")
    print("=" * 60)

    # Check model folder
    model_folder = Path(__file__).parent / "models"
    print(f"\n📁 Model folder: {model_folder}")
    print(f"   Exists: {'✅' if model_folder.exists() else '❌'}")

    if model_folder.exists():
        models = list(model_folder.glob("*.joblib"))
        print(f"   Models found: {len(models)}")
        for model_file in models:
            size_kb = model_file.stat().st_size / 1024
            print(f"   - {model_file.name} ({size_kb:.1f} KB)")

    # Check specific template model
    model_path = model_folder / f"template_{template_id}_model.joblib"
    print(f"\n🎯 Template {template_id} model: {model_path}")
    print(f"   Exists: {'✅' if model_path.exists() else '❌'}")

    if not model_path.exists():
        print("\n❌ Model file not found!")
        print("   To train model:")
        print(f"   curl -X POST http://localhost:8000/api/v1/learning/train \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(
            f'     -d \'{{"template_id": {template_id}, "use_all_feedback": false}}\''
        )
        return False

    # Try to load model
    print(f"\n🔄 Loading model...")
    try:
        model = joblib.load(model_path)
        print(f"   ✅ Model loaded successfully!")
        print(f"   Type: {type(model)}")
        print(f"   Module: {model.__class__.__module__}")

        # Check if it's a CRF model
        if hasattr(model, "classes_"):
            print(f"\n📊 Model info:")
            print(f"   Classes: {len(model.classes_)} labels")
            print(f"   Labels: {model.classes_[:10]}...")  # First 10 labels

            # Group labels by field
            field_labels = {}
            for label in model.classes_:
                if label != "O":
                    # Extract field name from B-FIELD or I-FIELD
                    parts = label.split("-", 1)
                    if len(parts) == 2:
                        prefix, field = parts
                        if field not in field_labels:
                            field_labels[field] = []
                        field_labels[field].append(label)

            print(f"\n🏷️  Fields in model:")
            for field, labels in sorted(field_labels.items()):
                print(f"   - {field}: {labels}")

        return True

    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_feedback_data(template_id: int = 1):
    """Check feedback data for training"""
    print(f"\n" + "=" * 60)
    print("📊 FEEDBACK DATA CHECK")
    print("=" * 60)

    try:
        from database.db_manager import DatabaseManager

        db = DatabaseManager()
        feedback_repo = FeedbackRepository(db)
        # Get feedback for template
        feedback = feedback_repo.find_for_training(template_id, unused_only=False)

        print(f"\n📝 Feedback records for template {template_id}:")
        print(f"   Total: {len(feedback)}")

        if feedback:
            # Group by field
            field_counts = {}
            for fb in feedback:
                field = fb["field_name"]
                field_counts[field] = field_counts.get(field, 0) + 1

            print(f"\n🏷️  Feedback by field:")
            for field, count in sorted(field_counts.items()):
                print(f"   - {field}: {count} records")

            # Show sample
            print(f"\n📄 Sample feedback:")
            for fb in feedback[:3]:
                print(f"   - Field: {fb['field_name']}")
                print(f"     Original: {fb.get('original_value', 'N/A')}")
                print(f"     Corrected: {fb['corrected_value']}")
                print(
                    f"     Used for training: {'✅' if fb['used_for_training'] else '❌'}"
                )
                print()
        else:
            print("   ❌ No feedback data found!")
            print("   To create feedback:")
            print("   1. Extract a document")
            print("   2. Validate and correct the results")
            print("   3. Submit corrections")

    except Exception as e:
        print(f"   ❌ Error checking feedback: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main function"""
    template_id = 1

    if len(sys.argv) > 1:
        try:
            template_id = int(sys.argv[1])
        except ValueError:
            print(f"Invalid template_id: {sys.argv[1]}")
            sys.exit(1)

    print(f"\n🎯 Checking template ID: {template_id}\n")

    # Check model
    model_ok = check_model_status(template_id)

    # Check feedback data
    check_feedback_data(template_id)

    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)

    if model_ok:
        print("✅ Model is ready to use!")
        print("\n🎯 Next steps:")
        print("   1. Restart backend: python app.py")
        print("   2. Extract a document")
        print("   3. Check logs for CRF usage")
    else:
        print("❌ Model not ready!")
        print("\n🎯 Next steps:")
        print("   1. Ensure you have feedback data (validate documents)")
        print("   2. Train model via API or UI")
        print("   3. Run this script again to verify")

    print("\n")


if __name__ == "__main__":
    main()
