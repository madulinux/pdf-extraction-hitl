"""
Test script for detailed evaluation metrics (Precision, Recall, F1-Score)
"""
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics

def test_detailed_metrics():
    """Test the new detailed metrics calculation"""
    
    # Initialize
    db = DatabaseManager()
    metrics_service = PerformanceMetrics(db)
    
    # Get metrics for template 1 (certificate_template)
    template_id = 1
    print(f"\n{'='*70}")
    print(f"Testing Detailed Metrics for Template ID: {template_id}")
    print(f"{'='*70}\n")
    
    metrics = metrics_service.get_template_metrics(template_id)
    
    # Test field_metrics_detailed
    print("="*70)
    print("📊 DETAILED EVALUATION METRICS (Precision, Recall, F1-Score)")
    print("="*70)
    
    detailed_metrics = metrics.get('field_metrics_detailed', {})
    
    if not detailed_metrics:
        print("❌ No detailed metrics found!")
        return
    
    print(f"\nTotal fields: {len(detailed_metrics)}\n")
    
    # Print table header
    print(f"{'Field Name':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'TP':<6} {'FP':<6} {'FN':<6} {'Support':<8}")
    print("-" * 100)
    
    # Sort by F1-Score
    sorted_fields = sorted(
        detailed_metrics.items(),
        key=lambda x: x[1]['f1_score'],
        reverse=True
    )
    
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    
    for field_name, stats in sorted_fields:
        precision = stats['precision'] * 100
        recall = stats['recall'] * 100
        f1_score = stats['f1_score'] * 100
        
        total_precision += stats['precision']
        total_recall += stats['recall']
        total_f1 += stats['f1_score']
        
        # Color coding
        if f1_score >= 90:
            status = "✅"
        elif f1_score >= 70:
            status = "⚠️"
        else:
            status = "❌"
        
        print(f"{field_name:<20} {precision:>6.1f}%     {recall:>6.1f}%     {f1_score:>6.1f}%     "
              f"{stats['tp']:<6} {stats['fp']:<6} {stats['fn']:<6} {stats['support']:<8} {status}")
    
    # Calculate averages
    num_fields = len(detailed_metrics)
    avg_precision = (total_precision / num_fields) * 100
    avg_recall = (total_recall / num_fields) * 100
    avg_f1 = (total_f1 / num_fields) * 100
    
    print("-" * 100)
    print(f"{'AVERAGE':<20} {avg_precision:>6.1f}%     {avg_recall:>6.1f}%     {avg_f1:>6.1f}%")
    print("=" * 100)
    
    # Interpretation
    print("\n" + "="*70)
    print("📈 INTERPRETATION")
    print("="*70)
    
    # Find best and worst performing fields
    best_field = sorted_fields[0]
    worst_field = sorted_fields[-1]
    
    print(f"\n✅ Best Performing Field:")
    print(f"   {best_field[0]}: F1-Score = {best_field[1]['f1_score']*100:.1f}%")
    print(f"   Precision: {best_field[1]['precision']*100:.1f}%, Recall: {best_field[1]['recall']*100:.1f}%")
    
    print(f"\n❌ Worst Performing Field:")
    print(f"   {worst_field[0]}: F1-Score = {worst_field[1]['f1_score']*100:.1f}%")
    print(f"   Precision: {worst_field[1]['precision']*100:.1f}%, Recall: {worst_field[1]['recall']*100:.1f}%")
    
    # Identify fields needing improvement
    print(f"\n⚠️  Fields Needing Improvement (F1 < 70%):")
    needs_improvement = [
        (name, stats) for name, stats in sorted_fields 
        if stats['f1_score'] < 0.7
    ]
    
    if needs_improvement:
        for name, stats in needs_improvement:
            print(f"   - {name}: F1={stats['f1_score']*100:.1f}% "
                  f"(Precision={stats['precision']*100:.1f}%, Recall={stats['recall']*100:.1f}%)")
            
            # Diagnose the issue
            if stats['precision'] < 0.7 and stats['recall'] >= 0.7:
                print(f"     → Issue: Too many False Positives (FP={stats['fp']})")
                print(f"     → Solution: Improve extraction accuracy, reduce noise")
            elif stats['recall'] < 0.7 and stats['precision'] >= 0.7:
                print(f"     → Issue: Too many False Negatives (FN={stats['fn']})")
                print(f"     → Solution: Improve field detection, reduce missing extractions")
            else:
                print(f"     → Issue: Both Precision and Recall need improvement")
                print(f"     → Solution: Review extraction strategy and feature engineering")
    else:
        print("   ✅ All fields performing well!")
    
    # Compare with simple accuracy
    print("\n" + "="*70)
    print("🔍 COMPARISON: Detailed Metrics vs Simple Accuracy")
    print("="*70)
    
    field_performance = metrics.get('field_performance', {})
    
    print(f"\n{'Field Name':<20} {'Accuracy':<12} {'F1-Score':<12} {'Difference':<12}")
    print("-" * 60)
    
    for field_name in sorted_fields[:5]:  # Top 5 fields
        name = field_name[0]
        f1 = detailed_metrics[name]['f1_score'] * 100
        accuracy = field_performance.get(name, {}).get('accuracy', 0) * 100
        diff = f1 - accuracy
        
        print(f"{name:<20} {accuracy:>6.1f}%     {f1:>6.1f}%     {diff:>+6.1f}%")
    
    print("\n" + "="*70)
    print("✅ Detailed metrics test completed!")
    print("="*70)
    
    # Test performance stats (extraction time)
    print("\n" + "="*70)
    print("⏱️  EXTRACTION TIME STATISTICS")
    print("="*70)
    
    performance_stats = metrics.get('performance_stats', {})
    
    if performance_stats and performance_stats.get('documents_timed', 0) > 0:
        print(f"\n📊 Overall Statistics:")
        print(f"   Documents Timed: {performance_stats['documents_timed']}")
        print(f"   Average Time: {performance_stats['avg_time_ms']:.2f} ms ({performance_stats['avg_time_ms']/1000:.2f}s)")
        print(f"   Min Time: {performance_stats['min_time_ms']} ms")
        print(f"   Max Time: {performance_stats['max_time_ms']} ms")
        print(f"   Total Time: {performance_stats['total_time_sec']:.2f} seconds")
        
        # Per-strategy stats
        by_strategy = performance_stats.get('by_strategy', {})
        if by_strategy:
            print(f"\n📊 Time by Strategy:")
            for strategy, stats in by_strategy.items():
                print(f"   {strategy}:")
                print(f"      Avg: {stats['avg_time_ms']:.2f} ms")
                print(f"      Min: {stats['min_time_ms']} ms")
                print(f"      Max: {stats['max_time_ms']} ms")
                print(f"      Count: {stats['count']} documents")
    else:
        print("\n⚠️  No extraction time data available (old documents)")
        print("   Extraction time tracking was just added.")
        print("   New extractions will include timing data.")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    test_detailed_metrics()
