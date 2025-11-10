#!/usr/bin/env python3
"""
Test new metrics: Ablation Study and Time Trends
"""
import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics
import json

db = DatabaseManager()
metrics_service = PerformanceMetrics(db)

template_id = 1

print("🔍 Testing new metrics...")
print("=" * 80)

# Get all metrics
metrics = metrics_service.get_template_metrics(template_id)

# Test Ablation Study
print("\n📊 ABLATION STUDY")
print("=" * 80)
ablation = metrics.get('ablation_study', {})

if ablation and ablation.get('strategies'):
    print(f"\n✅ Ablation Study Data Available")
    print(f"   Hybrid Accuracy: {ablation['hybrid_accuracy']:.4f} ({ablation['hybrid_accuracy']*100:.2f}%)")
    print(f"   Hybrid Correct: {ablation['hybrid_correct']}/{ablation['hybrid_total']}")
    print(f"   Best Single Strategy: {ablation['best_single_strategy']}")
    print(f"   Best Single Accuracy: {ablation['best_single_accuracy']:.4f} ({ablation['best_single_accuracy']*100:.2f}%)")
    print(f"   Improvement: {ablation['improvement_over_best']:.2f}%")
    
    print(f"\n📈 Strategy Comparison:")
    for i, strategy in enumerate(ablation['strategies'][:5], 1):  # Top 5
        print(f"   {i}. {strategy['strategy']:20s}: {strategy['accuracy']:.4f} ({strategy['accuracy']*100:.2f}%) - {strategy['correct']}/{strategy['total']} (coverage: {strategy['coverage']*100:.1f}%)")
else:
    print("❌ No ablation study data available")

# Test Time Trends
print("\n⏱️  TIME TRENDS")
print("=" * 80)
time_trends = metrics.get('time_trends', {})

if time_trends and time_trends.get('trend_data'):
    print(f"\n✅ Time Trends Data Available")
    print(f"   Total Documents: {time_trends['total_documents']}")
    print(f"   Avg Time (First 10): {time_trends['avg_time_first_10']:.2f} ms")
    print(f"   Avg Time (Last 10): {time_trends['avg_time_last_10']:.2f} ms")
    print(f"   Performance Change: {time_trends['performance_change']:.2f}%")
    
    if time_trends['performance_change'] < -5:
        print(f"   Status: ✅ IMPROVING (getting faster)")
    elif time_trends['performance_change'] > 5:
        print(f"   Status: ⚠️  DEGRADING (getting slower)")
    else:
        print(f"   Status: ✅ STABLE")
    
    print(f"\n📈 Sample Trend Data (first 5 and last 5):")
    trend_data = time_trends['trend_data']
    for point in trend_data[:5]:
        print(f"   Doc #{point['document_number']:3d}: {point['extraction_time_ms']:5.1f} ms (MA: {point['moving_average']:5.1f} ms)")
    if len(trend_data) > 10:
        print(f"   ...")
        for point in trend_data[-5:]:
            print(f"   Doc #{point['document_number']:3d}: {point['extraction_time_ms']:5.1f} ms (MA: {point['moving_average']:5.1f} ms)")
else:
    print("❌ No time trends data available")

print("\n" + "=" * 80)
print("✅ Test completed!")
