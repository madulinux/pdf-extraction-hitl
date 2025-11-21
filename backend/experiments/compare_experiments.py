"""
Compare Experiments Script
Compare baseline vs adaptive learning results

Usage:
    python compare_experiments.py --template-id 1
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import argparse
from pathlib import Path
from datetime import datetime


def load_experiment_results(template_id: int):
    """Load baseline and adaptive experiment results"""
    baseline_file = f"experiments/results/baseline_template_{template_id}.json"
    adaptive_file = f"experiments/results/adaptive_template_{template_id}.json"
    
    baseline = None
    adaptive = None
    
    if os.path.exists(baseline_file):
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
    
    if os.path.exists(adaptive_file):
        with open(adaptive_file, 'r') as f:
            adaptive = json.load(f)
    
    return baseline, adaptive


def compare_experiments(template_id: int):
    """Compare baseline and adaptive experiments"""
    print("="*70)
    print("📊 EXPERIMENT COMPARISON")
    print("="*70)
    print(f"Template ID: {template_id}\n")
    
    # Load results
    baseline, adaptive = load_experiment_results(template_id)
    
    if not baseline:
        print("❌ Baseline results not found")
        print(f"   Run: python experiments/run_baseline.py --template-id {template_id}")
        return
    
    if not adaptive:
        print("❌ Adaptive results not found")
        print(f"   Run: python experiments/run_adaptive.py --template-id {template_id}")
        return
    
    # Extract metrics
    baseline_acc = baseline.get('baseline_accuracy', 0)
    adaptive_initial = adaptive.get('initial_accuracy', 0)
    adaptive_final = adaptive.get('final_accuracy', 0)
    
    improvement = adaptive_final - baseline_acc
    improvement_pct = (improvement / baseline_acc * 100) if baseline_acc > 0 else 0
    
    # Print comparison
    print("📈 ACCURACY COMPARISON")
    print("-"*70)
    print(f"Baseline (Rule-based):        {baseline_acc:.2%}")
    print(f"Adaptive Initial:             {adaptive_initial:.2%}")
    print(f"Adaptive Final (Hybrid):      {adaptive_final:.2%}")
    print()
    print(f"Improvement:                  {improvement:.2%} ({improvement_pct:+.1f}%)")
    print()
    
    # Learning curve summary
    if 'learning_curve' in adaptive:
        learning_curve = adaptive['learning_curve']
        print("📉 LEARNING CURVE")
        print("-"*70)
        print(f"{'Batch':<10} {'Documents':<15} {'Accuracy':<15} {'Improvement':<15}")
        print("-"*70)
        
        for point in learning_curve:
            batch = point.get('batch', 0)
            docs = point.get('documents_with_feedback', 0)
            acc = point.get('accuracy', 0)
            imp = point.get('improvement', 0)
            
            print(f"{batch:<10} {docs:<15} {acc:<15.2%} {imp:+<15.2%}")
        print()
    
    # Field-level comparison (if available)
    if 'field_accuracy' in baseline:
        print("📋 FIELD-LEVEL ACCURACY")
        print("-"*70)
        print(f"{'Field Name':<30} {'Baseline':<15} {'Status':<15}")
        print("-"*70)
        
        # Sort by baseline accuracy (worst first)
        field_acc = baseline['field_accuracy']
        sorted_fields = sorted(field_acc.items(), key=lambda x: x[1]['accuracy'])
        
        for field_name, stats in sorted_fields[:10]:  # Top 10 worst
            acc = stats['accuracy']
            total = stats['total']
            correct = stats['correct']
            
            status = "🔴 Low" if acc < 0.5 else "🟡 Medium" if acc < 0.8 else "🟢 Good"
            
            print(f"{field_name:<30} {acc:<15.2%} {status:<15}")
        print()
    
    # Strategy comparison
    print("🎯 STRATEGY COMPARISON")
    print("-"*70)
    print(f"Baseline Strategy:            rule_based")
    print(f"Adaptive Strategy:            hybrid (rule_based + CRF)")
    print(f"Training Sessions:            {adaptive.get('total_batches', 0)}")
    print(f"Total Corrections:            {adaptive.get('total_corrections', 0)}")
    print()
    
    # Save comparison
    comparison = {
        "template_id": template_id,
        "baseline": {
            "accuracy": baseline_acc,
            "strategy": "rule_based",
            "total_documents": baseline.get('total_documents', 0)
        },
        "adaptive": {
            "initial_accuracy": adaptive_initial,
            "final_accuracy": adaptive_final,
            "strategy": "hybrid",
            "total_documents": adaptive.get('total_documents', 0),
            "total_batches": adaptive.get('total_batches', 0),
            "total_corrections": adaptive.get('total_corrections', 0)
        },
        "improvement": {
            "absolute": improvement,
            "percentage": improvement_pct
        },
        "timestamp": datetime.now().isoformat()
    }
    
    output_file = f"experiments/results/comparison_template_{template_id}.json"
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print("="*70)
    print(f"💾 Comparison saved to: {output_file}")
    print("="*70)
    
    # Generate visualization data
    generate_visualization_data(template_id, baseline, adaptive)


def generate_visualization_data(template_id: int, baseline: dict, adaptive: dict):
    """Generate data for visualization (for thesis charts)"""
    
    # Learning curve data for plotting
    if 'learning_curve' in adaptive:
        curve_data = {
            "x": [point['batch'] for point in adaptive['learning_curve']],
            "y": [point['accuracy'] * 100 for point in adaptive['learning_curve']],
            "baseline": baseline.get('baseline_accuracy', 0) * 100,
            "labels": {
                "x": "Training Batch",
                "y": "Accuracy (%)",
                "title": f"Learning Curve - Template {template_id}"
            }
        }
        
        output_file = f"experiments/results/visualization_data_{template_id}.json"
        with open(output_file, 'w') as f:
            json.dump(curve_data, f, indent=2)
        
        print(f"📊 Visualization data saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare baseline and adaptive experiments')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    
    args = parser.parse_args()
    
    compare_experiments(args.template_id)
