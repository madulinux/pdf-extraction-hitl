"""
Comprehensive Diagnostic Tool for Extraction Pipeline

This tool traces the entire pipeline:
1. Extraction → What does the model predict?
2. Correction → What feedback is saved?
3. Training → What data is used for training?
4. Model → What does the model learn?

Usage:
    python tools/diagnostic_trace.py --document-id 230
    python tools/diagnostic_trace.py --full-pipeline
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import argparse
from pathlib import Path
from database.db_manager import DatabaseManager
from core.extraction.extractor import DataExtractor
from core.learning.learner import AdaptiveLearner
import pdfplumber
from database.repositories.template_repository import TemplateRepository
from database.repositories.document_repository import DocumentRepository


def trace_extraction(document_id: int):
    """
    Trace extraction process for a specific document
    """
    print("\n" + "=" * 80)
    print("🔍 PHASE 1: EXTRACTION TRACING")
    print("=" * 80)

    db = DatabaseManager()
    document_repo = DocumentRepository(db)
    doc = document_repo.find_by_id(document_id)

    template_repo = TemplateRepository(db)
    if not doc:
        print(f"❌ Document {document_id} not found!")
        return None

    print(f"\n📄 Document: {doc.filename}")
    print(f"   Template ID: {doc.template_id}")
    print(f"   Status: {doc.status}")
    print(f"   File: {doc.file_path}")

    # Load template config
    template = template_repo.find_by_id(doc.template_id)
    with open(template.config_path, "r") as f:
        config = json.load(f)

    # Check model
    model_path = f"models/template_{doc.template_id}_model.joblib"
    if os.path.exists(model_path):
        print(f"   ✅ Model found: {model_path}")
        model_size = os.path.getsize(model_path) / 1024
        print(f"      Size: {model_size:.2f} KB")
    else:
        print(f"   ❌ Model NOT found: {model_path}")
        model_path = None

    # Extract with detailed logging
    print(f"\n🔍 Running extraction...")
    extractor = DataExtractor(config, model_path)
    results = extractor.extract(doc.file_path)

    print(f"\n📊 Extraction Results:")
    extracted_data = results.get("extracted_data", {})
    confidence_scores = results.get("confidence_scores", {})
    extraction_methods = results.get("extraction_methods", {})

    for field_name in sorted(extracted_data.keys()):
        value = extracted_data[field_name]
        confidence = confidence_scores.get(field_name, 0.0)
        method = extraction_methods.get(field_name, "unknown")

        print(f"\n   Field: {field_name}")
        print(f"      Value: '{value}'")
        print(f"      Confidence: {confidence:.2f}")
        print(f"      Method: {method}")

    return {
        "document_id": document_id,
        "extracted_data": extracted_data,
        "confidence_scores": confidence_scores,
        "extraction_methods": extraction_methods,
    }


def trace_feedback(document_id: int):
    """
    Trace feedback/corrections for a specific document
    """
    print("\n" + "=" * 80)
    print("📝 PHASE 2: FEEDBACK/CORRECTION TRACING")
    print("=" * 80)

    db = DatabaseManager()

    # Get feedback
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT field_name, original_value, corrected_value, used_for_training
        FROM feedback
        WHERE document_id = ?
        ORDER BY field_name
    """,
        (document_id,),
    )

    feedbacks = cursor.fetchall()
    conn.close()

    if not feedbacks:
        print(f"   ⚠️ No feedback found for document {document_id}")
        return None

    print(f"\n📊 Feedback Summary:")
    print(f"   Total corrections: {len(feedbacks)}")

    feedback_data = []
    for fb in feedbacks:
        print(f"\n   Field: {fb['field_name']}")
        print(f"      Original: '{fb['original_value']}'")
        print(f"      Corrected: '{fb['corrected_value']}'")
        print(f"      Used for training: {'✅' if fb['used_for_training'] else '❌'}")

        feedback_data.append(
            {
                "field_name": fb["field_name"],
                "original_value": fb["original_value"],
                "corrected_value": fb["corrected_value"],
                "used_for_training": fb["used_for_training"],
            }
        )

    return feedback_data


def trace_training_data(document_id: int):
    """
    Trace how feedback is converted to training data
    """
    print("\n" + "=" * 80)
    print("🎓 PHASE 3: TRAINING DATA PREPARATION TRACING")
    print("=" * 80)

    db = DatabaseManager()
    document_repo = DocumentRepository(db)
    doc = document_repo.find_by_id(document_id)

    # Get feedback
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT field_name, corrected_value
        FROM feedback
        WHERE document_id = ?
    """,
        (document_id,),
    )

    feedbacks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not feedbacks:
        print(f"   ⚠️ No feedback to convert to training data")
        return None

    # Extract words from PDF
    print(f"\n📄 Extracting words from PDF...")
    with pdfplumber.open(doc.file_path) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)

    print(f"   Total words extracted: {len(words)}")
    print(f"   Sample words: {[w['text'] for w in words[:10]]}")

    # Create BIO sequence
    print(f"\n🏷️ Creating BIO sequence...")
    learner = AdaptiveLearner()
    features, labels = learner._create_bio_sequence_multi(feedbacks, words)

    if not features or not labels:
        print(f"   ❌ Failed to create BIO sequence!")
        return None

    print(f"   ✅ BIO sequence created successfully")
    print(f"   Total tokens: {len(labels)}")

    # Count labels
    from collections import Counter

    label_counts = Counter(labels)

    print(f"\n📊 Label Distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"      {label}: {count}")

    # Show sample BIO sequence
    print(f"\n📝 Sample BIO Sequence (first 30 tokens):")
    for i in range(min(30, len(labels))):
        word_text = words[i]["text"] if i < len(words) else "N/A"
        label = labels[i]
        print(f"      {i:3d}. '{word_text:20s}' → {label}")

    return {
        "features": features,
        "labels": labels,
        "label_counts": dict(label_counts),
        "total_tokens": len(labels),
    }


def trace_model_prediction(document_id: int):
    """
    Trace what the model actually predicts
    """
    print("\n" + "=" * 80)
    print("🤖 PHASE 4: MODEL PREDICTION TRACING")
    print("=" * 80)

    db = DatabaseManager()
    document_repo = DocumentRepository(db)
    doc = document_repo.find_by_id(document_id)

    model_path = f"models/template_{doc.template_id}_model.joblib"

    if not os.path.exists(model_path):
        print(f"   ❌ Model not found: {model_path}")
        return None

    print(f"   ✅ Loading model: {model_path}")

    # Load model directly (sklearn_crfsuite.CRF)
    import joblib

    model = joblib.load(model_path)

    # Extract words
    with pdfplumber.open(doc.file_path) as pdf:
        words = []
        for page in pdf.pages:
            page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
            words.extend(page_words)

    # Extract features using learner
    print(f"\n🔍 Extracting features for {len(words)} words...")
    learner = AdaptiveLearner()
    features = [
        learner._extract_word_features(words[i], words, i) for i in range(len(words))
    ]

    # Predict using loaded model
    print(f"🎯 Running model prediction...")
    predictions = model.predict([features])[0]

    print(f"   Total predictions: {len(predictions)}")

    # Count predictions
    from collections import Counter

    pred_counts = Counter(predictions)

    print(f"\n📊 Prediction Distribution:")
    for label, count in sorted(pred_counts.items()):
        print(f"      {label}: {count}")

    # Show predictions for each field
    print(f"\n📝 Predicted Sequences:")

    current_field = None
    current_tokens = []

    for i, (word, pred) in enumerate(zip(words, predictions)):
        if pred.startswith("B-"):
            # New field starts
            if current_field and current_tokens:
                value = " ".join(current_tokens)
                print(f"      {current_field}: '{value}'")

            current_field = pred[2:]  # Remove 'B-' prefix
            current_tokens = [word["text"]]

        elif pred.startswith("I-"):
            # Continue current field
            if current_field:
                current_tokens.append(word["text"])

        else:
            # 'O' - outside any field
            if current_field and current_tokens:
                value = " ".join(current_tokens)
                print(f"      {current_field}: '{value}'")
                current_field = None
                current_tokens = []

    # Print last field
    if current_field and current_tokens:
        value = " ".join(current_tokens)
        print(f"      {current_field}: '{value}'")

    return {"predictions": predictions, "pred_counts": dict(pred_counts)}


def compare_with_ground_truth(document_id: int):
    """
    Compare extraction results with ground truth
    """
    print("\n" + "=" * 80)
    print("📊 PHASE 5: GROUND TRUTH COMPARISON")
    print("=" * 80)

    db = DatabaseManager()
    document_repo = DocumentRepository(db)
    doc = document_repo.find_by_id(document_id)

    # Find ground truth JSON
    pdf_path = Path(doc.file_path)
    json_path = pdf_path.with_suffix(".json")

    if not json_path.exists():
        print(f"   ⚠️ Ground truth not found: {json_path}")
        return None

    print(f"   ✅ Ground truth found: {json_path}")

    with open(json_path, "r") as f:
        ground_truth = json.load(f)

    # Get extraction results
    extraction_result = json.loads(doc.extraction_result)
    extracted_data = extraction_result.get("extracted_data", {})

    print(f"\n📊 Field-by-Field Comparison:")

    correct = 0
    total = 0

    for field_name in sorted(ground_truth.keys()):
        gt_value = str(ground_truth[field_name]).strip()
        extracted_value = str(extracted_data.get(field_name, "")).strip()

        match = gt_value == extracted_value
        total += 1
        if match:
            correct += 1

        status = "✅" if match else "❌"

        print(f"\n   {status} Field: {field_name}")
        print(f"      Ground Truth: '{gt_value}'")
        print(f"      Extracted:    '{extracted_value}'")

        if not match:
            # Show difference
            print(f"      Difference:")
            if len(gt_value) != len(extracted_value):
                print(f"         Length: {len(gt_value)} vs {len(extracted_value)}")

            # Find first difference
            for i, (c1, c2) in enumerate(zip(gt_value, extracted_value)):
                if c1 != c2:
                    print(f"         First diff at pos {i}: '{c1}' vs '{c2}'")
                    break

    accuracy = correct / total * 100 if total > 0 else 0
    print(f"\n📊 Overall Accuracy: {correct}/{total} = {accuracy:.2f}%")

    return {"correct": correct, "total": total, "accuracy": accuracy}


def full_pipeline_trace(document_id: int):
    """
    Run complete pipeline trace
    """
    print("\n" + "🔬" * 40)
    print("COMPREHENSIVE PIPELINE DIAGNOSTIC")
    print(f"Document ID: {document_id}")
    print("🔬" * 40)

    # Phase 1: Extraction
    extraction_result = trace_extraction(document_id)

    # Phase 2: Feedback
    feedback_result = trace_feedback(document_id)

    # Phase 3: Training Data
    training_result = trace_training_data(document_id)

    # Phase 4: Model Prediction
    model_result = trace_model_prediction(document_id)

    # Phase 5: Ground Truth Comparison
    comparison_result = compare_with_ground_truth(document_id)

    # Summary
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 80)

    if extraction_result:
        print(
            f"\n✅ Extraction: {len(extraction_result['extracted_data'])} fields extracted"
        )

    if feedback_result:
        print(f"✅ Feedback: {len(feedback_result)} corrections saved")

    if training_result:
        print(
            f"✅ Training Data: {training_result['total_tokens']} tokens, {len(training_result['label_counts'])} unique labels"
        )

    if model_result:
        non_o = sum(
            count
            for label, count in model_result["pred_counts"].items()
            if label != "O"
        )
        print(
            f"✅ Model Prediction: {non_o} tokens labeled (out of {sum(model_result['pred_counts'].values())})"
        )

    if comparison_result:
        print(
            f"✅ Accuracy: {comparison_result['accuracy']:.2f}% ({comparison_result['correct']}/{comparison_result['total']})"
        )

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic tool for extraction pipeline"
    )
    parser.add_argument("--document-id", type=int, help="Document ID to trace")
    parser.add_argument("--latest", action="store_true", help="Use latest document")

    args = parser.parse_args()

    if args.latest:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) as max_id FROM documents WHERE template_id = 1")
        result = cursor.fetchone()
        conn.close()
        document_id = result["max_id"]
        print(f"Using latest document: {document_id}")
    elif args.document_id:
        document_id = args.document_id
    else:
        print("❌ Please specify --document-id or --latest")
        return

    full_pipeline_trace(document_id)


if __name__ == "__main__":
    main()
