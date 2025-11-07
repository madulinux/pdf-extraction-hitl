"""
Comparison: Exact Match vs Fuzzy Match Evaluation
Demonstrates the importance of using appropriate evaluation metrics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline_evaluation import BaselineEvaluator
import pandas as pd
import matplotlib.pyplot as plt

def compare_evaluation_methods():
    """Compare exact match vs fuzzy match evaluation"""
    
    print("\n" + "="*70)
    print("📊 COMPARISON: Exact Match vs Fuzzy Match Evaluation")
    print("="*70)
    
    # 1. Exact Match (threshold = 1.0 = 100% match required)
    print("\n🔍 Running Exact Match Evaluation...")
    evaluator_exact = BaselineEvaluator(template_id=1, similarity_threshold=1.0)
    results_exact = evaluator_exact.evaluate_overall_performance()
    per_field_exact = evaluator_exact.evaluate_per_field_performance()
    
    # 2. Fuzzy Match (threshold = 0.8 = 80% similarity)
    print("\n🔍 Running Fuzzy Match Evaluation (80% threshold)...")
    evaluator_fuzzy = BaselineEvaluator(template_id=1, similarity_threshold=0.8)
    results_fuzzy = evaluator_fuzzy.evaluate_overall_performance()
    per_field_fuzzy = evaluator_fuzzy.evaluate_per_field_performance()
    
    # 3. Comparison Summary
    print("\n" + "="*70)
    print("📈 COMPARISON SUMMARY")
    print("="*70)
    
    comparison_data = {
        'Metric': ['Accuracy', 'Avg Similarity', 'F1-Score'],
        'Exact Match (100%)': [
            f"{results_exact['accuracy']:.2%}",
            f"{results_exact['avg_similarity']:.2%}",
            f"{results_exact['f1_score']:.2%}"
        ],
        'Fuzzy Match (80%)': [
            f"{results_fuzzy['accuracy']:.2%}",
            f"{results_fuzzy['avg_similarity']:.2%}",
            f"{results_fuzzy['f1_score']:.2%}"
        ],
        'Improvement': [
            f"+{(results_fuzzy['accuracy'] - results_exact['accuracy']):.2%}",
            f"+{(results_fuzzy['avg_similarity'] - results_exact['avg_similarity']):.2%}",
            f"+{(results_fuzzy['f1_score'] - results_exact['f1_score']):.2%}"
        ]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    print("\n" + df_comparison.to_string(index=False))
    
    # 4. Per-Field Comparison
    print("\n" + "="*70)
    print("📊 PER-FIELD COMPARISON")
    print("="*70)
    
    # Merge per-field results
    per_field_exact['accuracy_exact'] = per_field_exact['accuracy']
    per_field_fuzzy['accuracy_fuzzy'] = per_field_fuzzy['accuracy']
    
    merged = per_field_exact[['field_name', 'accuracy_exact']].merge(
        per_field_fuzzy[['field_name', 'accuracy_fuzzy', 'avg_similarity']],
        on='field_name'
    )
    merged['improvement'] = merged['accuracy_fuzzy'] - merged['accuracy_exact']
    merged = merged.sort_values('improvement', ascending=False)
    
    print("\n" + merged.to_string(index=False))
    
    # 5. Visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Overall Metrics Comparison
    metrics = ['Accuracy', 'F1-Score']
    exact_values = [results_exact['accuracy'], results_exact['f1_score']]
    fuzzy_values = [results_fuzzy['accuracy'], results_fuzzy['f1_score']]
    
    x = range(len(metrics))
    width = 0.35
    
    ax1.bar([i - width/2 for i in x], exact_values, width, label='Exact Match', alpha=0.8, color='coral')
    ax1.bar([i + width/2 for i in x], fuzzy_values, width, label='Fuzzy Match (80%)', alpha=0.8, color='steelblue')
    
    ax1.set_xlabel('Metrics', fontsize=12)
    ax1.set_ylabel('Score', fontsize=12)
    ax1.set_title('Overall Performance: Exact vs Fuzzy Match', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_ylim([0, 1.0])
    
    # Add value labels
    for i, (exact, fuzzy) in enumerate(zip(exact_values, fuzzy_values)):
        ax1.text(i - width/2, exact + 0.02, f'{exact:.1%}', ha='center', va='bottom', fontsize=10)
        ax1.text(i + width/2, fuzzy + 0.02, f'{fuzzy:.1%}', ha='center', va='bottom', fontsize=10)
    
    # Plot 2: Per-Field Accuracy Comparison
    fields = merged['field_name'].tolist()
    exact_acc = merged['accuracy_exact'].tolist()
    fuzzy_acc = merged['accuracy_fuzzy'].tolist()
    
    y = range(len(fields))
    
    ax2.barh([i - width/2 for i in y], exact_acc, width, label='Exact Match', alpha=0.8, color='coral')
    ax2.barh([i + width/2 for i in y], fuzzy_acc, width, label='Fuzzy Match (80%)', alpha=0.8, color='steelblue')
    
    ax2.set_ylabel('Field Name', fontsize=12)
    ax2.set_xlabel('Accuracy', fontsize=12)
    ax2.set_title('Per-Field Accuracy: Exact vs Fuzzy Match', fontsize=14, fontweight='bold')
    ax2.set_yticks(y)
    ax2.set_yticklabels(fields, fontsize=9)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim([0, 1.0])
    
    plt.tight_layout()
    
    output_file = 'evaluation/results/exact_vs_fuzzy_comparison.png'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n💾 Comparison plot saved to: {output_file}")
    
    plt.close()
    
    # 6. Key Insights
    print("\n" + "="*70)
    print("💡 KEY INSIGHTS")
    print("="*70)
    
    print("\n1. **Overall Improvement:**")
    print(f"   - Accuracy improved by {(results_fuzzy['accuracy'] - results_exact['accuracy']):.1%}")
    print(f"   - This reflects more realistic evaluation of partial extractions")
    
    print("\n2. **Fields with Biggest Improvement:**")
    top_improved = merged.nlargest(3, 'improvement')
    for _, row in top_improved.iterrows():
        print(f"   - {row['field_name']}: {row['accuracy_exact']:.1%} → {row['accuracy_fuzzy']:.1%} (+{row['improvement']:.1%})")
    
    print("\n3. **Average Similarity Score:**")
    print(f"   - {results_fuzzy['avg_similarity']:.1%} - indicates partial extractions are common")
    print(f"   - Fields with low accuracy but high similarity need better extraction rules")
    
    print("\n4. **Recommendation for BAB 4:**")
    print("   - Use fuzzy matching (80% threshold) as primary metric")
    print("   - Report both accuracy and avg similarity for complete picture")
    print("   - Discuss trade-offs between exact and fuzzy matching")
    print("   - Highlight that partial extractions still provide value")
    
    print("\n" + "="*70)
    print("✅ COMPARISON COMPLETE")
    print("="*70)

if __name__ == '__main__':
    compare_evaluation_methods()
