"""
Baseline Experiment Script
Evaluates baseline performance from existing extraction results

Usage:
    python run_baseline.py --template-id 1
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from core.extraction.services import ExtractionService
from core.learning.metrics import PerformanceMetrics
import json
from datetime import datetime
import argparse
import re


def load_ground_truth(documents, ground_truth_dir="data/ground_truth"):
    """Load ground truth from JSON files"""
    ground_truth = {}
    missing_count = 0
    
    for doc in documents:
        doc_id = doc['id']
        gt_path = os.path.join(ground_truth_dir, f"{doc_id}.json")
        
        if os.path.exists(gt_path):
            with open(gt_path, 'r') as f:
                ground_truth[doc_id] = json.load(f)
        else:
            missing_count += 1
            print(f"  ⚠️  Ground truth not found for document {doc_id}")
    
    if missing_count > 0:
        print(f"\n⚠️  Warning: {missing_count} documents missing ground truth")
        print(f"   Run: python prepare_ground_truth.py --template-id <id> first\n")
    
    return ground_truth


def evaluate_baseline(template_id: int, ground_truth_dir: str = "data/ground_truth"):
    """
    Evaluate baseline performance for a template
    
    Args:
        template_id: Template ID
        ground_truth_dir: Directory containing ground truth JSON files
    
    Returns:
        Evaluation results
    """
    db = DatabaseManager()
    
    # Use service layer instead of direct repository access
    from database.repositories.document_repository import DocumentRepository
    from database.repositories.template_repository import TemplateRepository
    
    doc_repo = DocumentRepository(db)
    template_repo = TemplateRepository(db)
    metrics_service = PerformanceMetrics(db)
    
    # Get template info
    template = template_repo.find_by_id(template_id)
    if not template:
        print(f"❌ Template {template_id} not found")
        return None
    
    print("="*70)
    print("📊 BASELINE EXPERIMENT EVALUATION")
    print("="*70)
    print(f"Template: {template.name} (ID: {template_id})")
    
    # Get documents with experiment_phase='baseline'
    documents = doc_repo.find_by_template_and_phase(template_id, 'baseline')
    
    if not documents:
        print(f"\n❌ No baseline documents found for template {template_id}")
        print(f"   Documents must have experiment_phase='baseline'")
        print(f"   Upload documents with: experiment_phase='baseline' parameter")
        return None
    
    print(f"Total Documents: {len(documents)}")
    print()
    
    # Load ground truth
    print("📁 Loading ground truth...")
    ground_truth = load_ground_truth(documents, ground_truth_dir)
    
    if not ground_truth:
        print("❌ No ground truth data found")
        return None
    
    print(f"✅ Loaded ground truth for {len(ground_truth)} documents\n")
    
    # Evaluate
    print("🔍 Evaluating baseline performance...")
    total_fields = 0
    correct_fields = 0
    field_stats = {}  # Per-field statistics
    
    # Metrics for precision/recall/F1
    true_positives = 0  # Correct extractions
    false_positives = 0  # Wrong extractions
    false_negatives = 0  # Missing extractions
    
    # Confidence tracking
    total_confidence = 0
    confidence_count = 0
    
    for doc in documents:
        doc_id = doc['id']
        
        # Skip if no ground truth
        if doc_id not in ground_truth:
            continue
        
        # Parse extraction result
        try:
            extraction_result = json.loads(doc['extraction_result'] or '{}')
        except:
            print(f"  ⚠️  Failed to parse extraction_result for document {doc_id}")
            continue
        
        extracted_data = extraction_result.get('extracted_data', {})
        metadata = extraction_result.get('metadata', {})
        strategies_used = metadata.get('strategies_used', [])
        gt = ground_truth[doc_id]
        
        # Build confidence map from strategies_used
        confidence_map = {}
        for strategy in strategies_used:
            field_name = strategy.get('field_name')
            confidence = strategy.get('confidence', 0)
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
            
            # Initialize field stats
            if field_name not in field_stats:
                field_stats[field_name] = {'total': 0, 'correct': 0, 'tp': 0, 'fp': 0, 'fn': 0, 'confidence_sum': 0, 'confidence_count': 0}
            
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
                extracted_value = re.sub(r"\s+", " ", str(extracted_value).strip())
                gt_value = re.sub(r"\s+", " ", str(gt_value).strip())
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
    
    # Calculate overall accuracy
    baseline_accuracy = correct_fields / total_fields if total_fields > 0 else 0
    
    # Calculate overall precision, recall, F1
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Calculate average confidence
    avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
    
    # Calculate per-field accuracy and metrics
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
    
    # Save results
    results = {
        "phase": "baseline",
        "template_id": template_id,
        "template_name": template.name,
        "total_documents": len(documents),
        "total_fields": total_fields,
        "correct_fields": correct_fields,
        "baseline_accuracy": baseline_accuracy,
        "strategy": "rule_based",
        "metrics": {
            "accuracy": baseline_accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "avg_confidence": avg_confidence,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        },
        "field_accuracy": field_accuracy,
        "timestamp": datetime.now().isoformat()
    }
    
    # Create results directory
    os.makedirs("experiments/results", exist_ok=True)
    
    # Save to JSON
    output_file = f"experiments/results/baseline_template_{template_id}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print results
    print("\n" + "="*70)
    print("📊 BASELINE RESULTS")
    print("="*70)
    print(f"Total Documents: {len(documents)}")
    print(f"Total Fields: {total_fields}")
    print(f"Correct Fields: {correct_fields}")
    print(f"Baseline Accuracy: {baseline_accuracy:.2%}")
    print()
    print("📈 Metrics:")
    print(f"   Precision: {precision:.2%}")
    print(f"   Recall: {recall:.2%}")
    print(f"   F1-Score: {f1_score:.2%}")
    print(f"   Avg Confidence: {avg_confidence:.2%}")
    print()
    
    # Print top 5 worst performing fields
    sorted_fields = sorted(
        field_accuracy.items(), 
        key=lambda x: x[1]['accuracy']
    )[:5]
    
    if sorted_fields:
        print("🔻 Worst Performing Fields:")
        for field_name, stats in sorted_fields:
            print(f"   {field_name}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})")
    
    print()
    print("="*70)
    print(f"💾 Results saved to: {output_file}")
    print("="*70)
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run baseline experiment evaluation')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    parser.add_argument('--ground-truth-dir', type=str, default='data/ground_truth', 
                       help='Ground truth directory')
    
    args = parser.parse_args()
    
    evaluate_baseline(args.template_id, args.ground_truth_dir)
