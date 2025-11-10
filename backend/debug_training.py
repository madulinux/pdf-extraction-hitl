#!/usr/bin/env python3
"""
Debug script to inspect training data and model predictions
"""

import sys
import pdfplumber
from database.db_manager import DatabaseManager
from core.learning.learner import AdaptiveLearner
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository


def debug_training(template_id: int):
    """Debug training data preparation"""

    print(f"\n{'='*60}")
    print(f"🔍 DEBUG TRAINING DATA FOR TEMPLATE {template_id}")
    print(f"{'='*60}\n")

    # Get feedback
    db = DatabaseManager()
    feedback_repo = FeedbackRepository(db)
    feedback_list = feedback_repo.find_for_training(template_id, unused_only=False)

    print(f"📊 Total feedback records: {len(feedback_list)}")

    # Group by document
    feedback_by_doc = {}
    for feedback in feedback_list:
        doc_id = feedback["document_id"]
        if doc_id not in feedback_by_doc:
            feedback_by_doc[doc_id] = []
        feedback_by_doc[doc_id].append(feedback)

    print(f"📄 Unique documents: {len(feedback_by_doc)}")
    print()

    # Inspect first document
    first_doc_id = list(feedback_by_doc.keys())[0]
    first_feedbacks = feedback_by_doc[first_doc_id]

    print(f"{'='*60}")
    print(f"📄 INSPECTING DOCUMENT {first_doc_id}")
    print(f"{'='*60}\n")

    print(f"Feedbacks for this document: {len(first_feedbacks)}")
    for fb in first_feedbacks:
        print(f"  - {fb['field_name']}: {fb['corrected_value'][:50]}...")
    print()

    # Get document
    document = DocumentRepository(db).find_by_id(first_doc_id)
    if not document:
        print(f"❌ Document {first_doc_id} not found!")
        return

    print(f"PDF path: {document.file_path}")
    print()

    # Extract words
    with pdfplumber.open(document.file_path) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)

    print(f"📝 Total words extracted: {len(words)}")
    print(f"Sample words (first 20):")
    for i, word in enumerate(words[:20]):
        print(f"  {i}: {word['text']}")
    print()

    # Create BIO sequence
    learner = AdaptiveLearner()
    features, labels = learner._create_bio_sequence_multi(first_feedbacks, words)

    print(f"{'='*60}")
    print(f"🏷️  BIO SEQUENCE")
    print(f"{'='*60}\n")

    print(f"Total tokens: {len(labels)}")
    print(f"Label distribution:")

    from collections import Counter

    label_counts = Counter(labels)
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")
    print()

    # Show labeled tokens
    print(f"Labeled tokens (non-O):")
    for i, (word, label) in enumerate(zip(words, labels)):
        if label != "O":
            print(f"  {i}: '{word['text']}' → {label}")
    print()

    # Check if features match
    print(f"{'='*60}")
    print(f"🔍 FEATURE INSPECTION")
    print(f"{'='*60}\n")

    print(f"Total features: {len(features)}")
    print(f"Sample feature keys (first token):")
    if features:
        for key in sorted(features[0].keys())[:15]:
            print(f"  - {key}: {features[0][key]}")
    print()

    # Test prediction
    print(f"{'='*60}")
    print(f"🤖 TEST PREDICTION")
    print(f"{'='*60}\n")

    # Load model
    import joblib
    import os

    model_path = f"models/template_{template_id}_model.joblib"

    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return

    model = joblib.load(model_path)
    print(f"✅ Model loaded: {model_path}")
    print(f"Model classes: {len(model.classes_)} labels")
    print(f"Labels: {model.classes_}")
    print()

    # Predict on training data
    predictions = model.predict([features])[0]

    print(f"Predictions on training data:")
    pred_counts = Counter(predictions)
    for label, count in sorted(pred_counts.items()):
        print(f"  {label}: {count}")
    print()

    # Compare predictions vs ground truth
    print(f"{'='*60}")
    print(f"📊 PREDICTION vs GROUND TRUTH")
    print(f"{'='*60}\n")

    mismatches = 0
    matches = 0

    print(f"Sample comparisons (first 50 tokens):")
    for i in range(min(50, len(labels))):
        pred = predictions[i]
        true = labels[i]
        word_text = words[i]["text"]

        if pred != true:
            mismatches += 1
            if mismatches <= 10:  # Show first 10 mismatches
                print(f"  {i}: '{word_text}' → Pred: {pred}, True: {true} ❌")
        else:
            matches += 1

    print()
    print(
        f"Accuracy on training sample: {matches}/{len(labels)} = {matches/len(labels)*100:.1f}%"
    )
    print()

    if mismatches > matches:
        print("⚠️  WARNING: Model performs poorly even on training data!")
        print("   This suggests:")
        print("   1. Model not trained properly")
        print("   2. Features don't match between training and prediction")
        print("   3. Training data has issues")

    print()


if __name__ == "__main__":
    template_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    debug_training(template_id)
