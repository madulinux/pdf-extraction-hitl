"""
Adaptive Learning Experiment Script
Simulates incremental learning with feedback and auto-training

Usage:
    python run_adaptive.py --template-id 1 --batch-size 5
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from core.extraction.services import ExtractionService
from core.learning.metrics import PerformanceMetrics
from core.learning.services import ModelService
import json
from datetime import datetime
import argparse
import re


def load_ground_truth(documents, ground_truth_dir="data/ground_truth"):
    """Load ground truth from JSON files"""
    ground_truth = {}
    missing_count = 0

    for doc in documents:
        doc_id = doc["id"]
        gt_path = os.path.join(ground_truth_dir, f"{doc_id}.json")

        if os.path.exists(gt_path):
            with open(gt_path, "r") as f:
                ground_truth[doc_id] = json.load(f)
        else:
            missing_count += 1

    if missing_count > 0:
        print(f"  ⚠️  Warning: {missing_count} documents missing ground truth")

    return ground_truth


def simulate_feedback(doc_id, extraction_result, ground_truth, extraction_service):
    """
    Simulate user feedback by comparing extraction with ground truth
    Uses the same logic as API endpoint for consistency

    Returns:
        Number of corrections made
    """
    corrections = {}
    extracted_data = extraction_result.get("extracted_data", {})

    for field_name, correct_value in ground_truth.items():
        extracted_value = extracted_data.get(field_name, "")

        # ✅ STRICT COMPARISON: Only strip leading/trailing whitespace
        # Do NOT normalize internal spaces - missing spaces are real errors!
        extracted_normalized = str(extracted_value).strip()
        correct_normalized = str(correct_value).strip()

        if extracted_normalized != correct_normalized:
            corrections[field_name] = correct_value

    # Use ExtractionService.save_corrections() - same as API endpoint
    result = extraction_service.save_corrections(
        document_id=doc_id, corrections=corrections
    )
    return result.get("corrections_count", 0)


def evaluate_accuracy(documents, ground_truth):
    """Calculate accuracy for a set of documents"""
    total_fields = 0
    correct_fields = 0

    for doc in documents:
        doc_id = doc["id"]

        if doc_id not in ground_truth:
            continue

        try:
            extraction_result = json.loads(doc["extraction_result"] or "{}")
        except:
            continue

        extracted_data = extraction_result.get("extracted_data", {})
        gt = ground_truth[doc_id]

        for field_name, extracted_value in extracted_data.items():
            total_fields += 1
            gt_value = gt.get(field_name)

            # ✅ STRICT COMPARISON: Only strip leading/trailing whitespace
            extracted_value = str(extracted_value).strip()
            gt_value = str(gt_value).strip()

            if extracted_value == gt_value:
                correct_fields += 1

    return correct_fields / total_fields if total_fields > 0 else 0


def calculate_detailed_metrics(documents, ground_truth):
    """
    Calculate detailed metrics including precision, recall, F1, confidence
    Returns dict with all metrics
    """
    total_fields = 0
    correct_fields = 0
    field_stats = {}
    
    # Metrics for precision/recall/F1
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    # Confidence tracking
    total_confidence = 0
    confidence_count = 0
    
    for doc in documents:
        doc_id = doc["id"]
        
        if doc_id not in ground_truth:
            continue
        
        try:
            extraction_result = json.loads(doc["extraction_result"] or "{}")
        except:
            continue
        
        extracted_data = extraction_result.get("extracted_data", {})
        metadata = extraction_result.get("metadata", {})
        strategies_used = metadata.get("strategies_used", [])
        gt = ground_truth[doc_id]
        
        # Build confidence map
        confidence_map = {}
        for strategy in strategies_used:
            field_name = strategy.get("field_name")
            confidence = strategy.get("confidence", 0)
            if field_name:
                confidence_map[field_name] = confidence
        
        # Get all field names from both extracted and ground truth
        all_field_names = set(extracted_data.keys()) | set(gt.keys())
        
        # Evaluate each field
        for field_name in all_field_names:
            extracted_value = extracted_data.get(field_name, "")
            gt_value = gt.get(field_name, "")
            
            # Normalize empty values
            extracted_value = extracted_value if extracted_value else ""
            gt_value = gt_value if gt_value else ""
            
            total_fields += 1
            
            if field_name not in field_stats:
                field_stats[field_name] = {
                    'total': 0, 'correct': 0, 'tp': 0, 'fp': 0, 'fn': 0,
                    'confidence_sum': 0, 'confidence_count': 0
                }
            
            field_stats[field_name]['total'] += 1
            
            # Track confidence
            if field_name in confidence_map:
                conf = confidence_map[field_name]
                field_stats[field_name]['confidence_sum'] += conf
                field_stats[field_name]['confidence_count'] += 1
                total_confidence += conf
                confidence_count += 1
            
            # Compare with ground truth
            # TP: Extracted correctly (both have value and match)
            # FP: Extracted incorrectly (extracted has value but wrong or gt is empty)
            # FN: Not extracted (extracted is empty but gt has value)
            # TN: Both empty (not counted in extraction metrics)
            
            if extracted_value and gt_value:
                # ✅ STRICT COMPARISON: Only strip leading/trailing whitespace
                extracted_value = str(extracted_value).strip()
                gt_value = str(gt_value).strip()
                # Both have values
                if extracted_value == gt_value:
                    # True Positive: Correct extraction
                    correct_fields += 1
                    field_stats[field_name]['correct'] += 1
                    field_stats[field_name]['tp'] += 1
                    true_positives += 1
                else:
                    # False Positive: Wrong value extracted
                    field_stats[field_name]['fp'] += 1
                    false_positives += 1
            elif extracted_value and not gt_value:
                # False Positive: Extracted but shouldn't (hallucination)
                field_stats[field_name]['fp'] += 1
                false_positives += 1
            elif not extracted_value and gt_value:
                # False Negative: Should extract but didn't (missing)
                field_stats[field_name]['fn'] += 1
                false_negatives += 1
            # else: both empty - True Negative (not counted)
    
    # Calculate overall metrics
    accuracy = correct_fields / total_fields if total_fields > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
    
    # Calculate per-field metrics
    field_accuracy = {}
    for field_name, stats in field_stats.items():
        tp = stats['tp']
        fp = stats['fp']
        fn = stats['fn']
        
        field_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        field_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        field_f1 = 2 * (field_precision * field_recall) / (field_precision + field_recall) if (field_precision + field_recall) > 0 else 0
        field_avg_conf = stats['confidence_sum'] / stats['confidence_count'] if stats['confidence_count'] > 0 else 0
        
        field_accuracy[field_name] = {
            'accuracy': stats['correct'] / stats['total'] if stats['total'] > 0 else 0,
            'total': stats['total'],
            'correct': stats['correct'],
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': field_precision,
            'recall': field_recall,
            'f1_score': field_f1,
            'avg_confidence': field_avg_conf
        }
    
    return {
        'total_fields': total_fields,
        'correct_fields': correct_fields,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'avg_confidence': avg_confidence,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'field_accuracy': field_accuracy
    }


def re_extract_documents(documents, template_id, service):
    """
    Re-extract all documents with current model

    Returns:
        Updated documents
    """
    print("    🔄 Re-extracting documents with updated model...")

    for doc in documents:
        try:
            # Re-extract existing document (updates extraction_result in DB)
            doc_id = doc["id"]
            result = service.re_extract_document(document_id=doc_id)
            # print(f"      ✅ Re-extracted doc {doc_id}")

        except Exception as e:
            print(f"      ❌ Error re-extracting doc {doc['id']}: {str(e)}")

    print("    ✅ Re-extraction complete")


def run_adaptive_experiment(
    template_id: int, batch_size: int = 5, ground_truth_dir: str = "data/ground_truth"
):
    """
    Run adaptive learning experiment

    Args:
        template_id: Template ID
        batch_size: Number of documents per batch (triggers auto-training)
        ground_truth_dir: Directory containing ground truth files
    """
    db = DatabaseManager()

    # Use service layer and repositories
    from database.repositories.template_repository import TemplateRepository
    from database.repositories.document_repository import DocumentRepository
    from database.repositories.feedback_repository import FeedbackRepository
    from database.repositories.training_repository import TrainingRepository

    template_repo = TemplateRepository(db)
    doc_repo = DocumentRepository(db)
    feedback_repo = FeedbackRepository(db)
    training_repo = TrainingRepository(db)

    # Initialize services
    extraction_service = ExtractionService(
        document_repo=doc_repo,
        feedback_repo=feedback_repo,
        template_repo=template_repo,
        training_repo=training_repo,
        upload_folder="uploads",
        model_folder="models",
        feedback_folder="feedback",
    )
    metrics_service = PerformanceMetrics(db)
    model_service = ModelService(
        db_manager=db,
        template_repo=template_repo,
        document_repo=doc_repo,
        feedback_repo=feedback_repo,
        training_repo=training_repo,
    )

    template = template_repo.find_by_id(template_id)
    if not template:
        print(f"❌ Template {template_id} not found")
        return

    print("=" * 70)
    print("🧪 ADAPTIVE LEARNING EXPERIMENT")
    print("=" * 70)
    print(f"Template: {template.name} (ID: {template_id})")
    print(f"Batch Size: {batch_size} documents")
    print()

    # Get documents with experiment_phase='adaptive'
    documents = doc_repo.find_by_template_and_phase(template_id, "adaptive")

    if not documents:
        print(f"❌ No adaptive documents found for template {template_id}")
        print(f"   Upload documents with: --experiment-phase adaptive")
        return

    print(f"📄 Found {len(documents)} adaptive documents")

    # Load ground truth
    print("📁 Loading ground truth...")
    ground_truth = load_ground_truth(documents, ground_truth_dir)

    if not ground_truth:
        print("❌ No ground truth data found")
        return

    print(f"✅ Loaded ground truth for {len(ground_truth)} documents\n")

    # Services already initialized above

    # Calculate baseline accuracy (before any training)
    print("📊 Calculating initial accuracy...")
    initial_accuracy = evaluate_accuracy(documents, ground_truth)
    print(f"   Initial Accuracy: {initial_accuracy:.2%}\n")

    # Learning curve data
    learning_curve = [
        {
            "batch": 0,
            "documents_with_feedback": 0,
            "accuracy": initial_accuracy,
            "timestamp": datetime.now().isoformat(),
        }
    ]

    # Process documents in batches
    total_batches = (len(documents) + batch_size - 1) // batch_size
    total_corrections = 0

    print(f"🔄 Starting incremental learning ({total_batches} batches)...\n")

    for batch_num in range(1, total_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(documents))
        batch_docs = documents[start_idx:end_idx]

        print(
            f"  📦 Batch {batch_num}/{total_batches} (Documents {start_idx+1}-{end_idx})"
        )

        # Simulate feedback for this batch
        batch_corrections = 0
        for doc in batch_docs:
            doc_id = doc["id"]

            if doc_id not in ground_truth:
                continue

            try:
                extraction_result = json.loads(doc["extraction_result"] or "{}")
            except:
                continue

            corrections = simulate_feedback(
                doc_id, extraction_result, ground_truth[doc_id], extraction_service
            )

            batch_corrections += corrections

        total_corrections += batch_corrections
        print(f"    ✅ Simulated {batch_corrections} corrections")

        # Trigger training (force training for experiment)
        print(f"    🎓 Training model with {total_corrections} total corrections...")
        try:
            # Use ModelService (already initialized above)

            # Check if model exists (first training vs retraining)
            model_path = os.path.join("models", f"template_{template_id}_model.joblib")
            is_first_training = not os.path.exists(model_path)

            if is_first_training:
                print(f"    🆕 First training - creating initial model...")
            else:
                print(f"    🔄 Retraining existing model...")

            if is_first_training:
                # Train model
                result = model_service.retrain_model(
                    template_id=template_id,
                    use_all_feedback=True,
                    model_folder="models",
                    is_incremental=False,
                )
            else:
                result = model_service.retrain_model(
                    template_id=template_id,
                    use_all_feedback=False,
                    model_folder="models",
                    is_incremental=True,
                )


            print(f"    ✅ Training complete!")
            print(f"       Samples: {result.get('training_samples', 0)}")
            print(
                f"       Accuracy: {result.get('test_metrics', {}).get('accuracy', 0):.2%}"
            )
            print(f"       Model: {result.get('model_path', 'N/A')}")

        except Exception as e:
            print(f"    ⚠️  Training error: {str(e)}")
            import traceback

            traceback.print_exc()

        # Re-extract all documents with updated model
        re_extract_documents(documents, template_id, extraction_service)

        # Re-load documents to get updated extraction results
        documents = doc_repo.find_by_template_and_phase(template_id, "adaptive")

        # Evaluate accuracy after this batch
        current_accuracy = evaluate_accuracy(documents, ground_truth)
        print(f"    📈 Accuracy after batch {batch_num}: {current_accuracy:.2%}")
        print()

        # Record learning curve
        learning_curve.append(
            {
                "batch": batch_num,
                "documents_with_feedback": end_idx,
                "total_corrections": total_corrections,
                "accuracy": current_accuracy,
                "improvement": current_accuracy - initial_accuracy,
                "timestamp": datetime.now().isoformat(),
            }
        )

    # Final results
    final_accuracy = learning_curve[-1]["accuracy"]
    improvement = final_accuracy - initial_accuracy
    improvement_pct = (
        (improvement / initial_accuracy * 100) if initial_accuracy > 0 else 0
    )
    
    # Calculate detailed metrics for final state
    print("\n🔍 Calculating detailed metrics...")
    final_metrics = calculate_detailed_metrics(documents, ground_truth)

    # Save results
    results = {
        "phase": "adaptive",
        "template_id": template_id,
        "template_name": template.name,
        "total_documents": len(documents),
        "batch_size": batch_size,
        "total_batches": total_batches,
        "total_corrections": total_corrections,
        "initial_accuracy": initial_accuracy,
        "final_accuracy": final_accuracy,
        "improvement": improvement,
        "improvement_percentage": improvement_pct,
        "strategy": "hybrid",
        "metrics": {
            "accuracy": final_metrics['accuracy'],
            "precision": final_metrics['precision'],
            "recall": final_metrics['recall'],
            "f1_score": final_metrics['f1_score'],
            "avg_confidence": final_metrics['avg_confidence'],
            "true_positives": final_metrics['true_positives'],
            "false_positives": final_metrics['false_positives'],
            "false_negatives": final_metrics['false_negatives']
        },
        "field_accuracy": final_metrics['field_accuracy'],
        "learning_curve": learning_curve,
        "timestamp": datetime.now().isoformat(),
    }

    # Create results directory
    os.makedirs("experiments/results", exist_ok=True)

    # Save results
    output_file = f"experiments/results/adaptive_template_{template_id}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Save learning curve separately
    curve_file = f"experiments/results/learning_curve_{template_id}.json"
    with open(curve_file, "w") as f:
        json.dump(learning_curve, f, indent=2)

    # Print final summary
    print("=" * 70)
    print("📊 ADAPTIVE LEARNING RESULTS")
    print("=" * 70)
    print(f"Total Documents: {len(documents)}")
    print(f"Total Batches: {total_batches}")
    print(f"Total Corrections: {total_corrections}")
    print(f"Initial Accuracy: {initial_accuracy:.2%}")
    print(f"Final Accuracy: {final_accuracy:.2%}")
    print(f"Improvement: {improvement:.2%} ({improvement_pct:+.1f}%)")
    print()
    print("📈 Final Metrics:")
    print(f"   Precision: {final_metrics['precision']:.2%}")
    print(f"   Recall: {final_metrics['recall']:.2%}")
    print(f"   F1-Score: {final_metrics['f1_score']:.2%}")
    print(f"   Avg Confidence: {final_metrics['avg_confidence']:.2%}")
    print()
    print(f"💾 Results saved to: {output_file}")
    print(f"📈 Learning curve saved to: {curve_file}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run adaptive learning experiment")
    parser.add_argument("--template-id", type=int, required=True, help="Template ID")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of documents per batch (default: 5)",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        default="data/ground_truth",
        help="Ground truth directory",
    )

    args = parser.parse_args()

    run_adaptive_experiment(args.template_id, args.batch_size, args.ground_truth_dir)
