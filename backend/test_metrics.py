#!/usr/bin/env python3
"""
Test performance metrics with updated strategy performance
"""

from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics
import json

db = DatabaseManager()
metrics_service = PerformanceMetrics(db)

# Get metrics for template 1 (certificate_template)
print("📊 Getting metrics for template 1...")
metrics = metrics_service.get_template_metrics(template_id=1)

# Print overview
print("\n" + "="*70)
print("📈 OVERVIEW")
print("="*70)
overview = metrics['overview']
print(f"Total Documents: {overview['total_documents']}")
print(f"Validated Documents: {overview['validated_documents']}")
print(f"Total Corrections: {overview['total_corrections']}")
print(f"Overall Accuracy: {overview['overall_accuracy']*100:.2f}%")
print(f"Validation Rate: {overview['validation_rate']*100:.2f}%")

# Print strategy performance
print("\n" + "="*70)
print("🎯 STRATEGY PERFORMANCE (from database)")
print("="*70)
strategy_perf = metrics['strategy_performance']
for strategy, stats in strategy_perf.items():
    print(f"\n{strategy.upper()}:")
    print(f"  Overall Accuracy: {stats['overall_accuracy']*100:.2f}%")
    print(f"  Total Attempts: {stats['total_attempts']}")
    print(f"  Total Correct: {stats['total_correct']}")
    print(f"  Fields tracked: {len(stats['fields'])}")
    
    # Show top 3 fields by accuracy
    sorted_fields = sorted(
        stats['fields'].items(),
        key=lambda x: x[1]['accuracy'],
        reverse=True
    )[:3]
    
    if sorted_fields:
        print(f"  Top fields:")
        for field, field_stats in sorted_fields:
            print(f"    - {field}: {field_stats['accuracy']*100:.2f}% ({field_stats['correct']}/{field_stats['total']})")

# Print field performance
print("\n" + "="*70)
print("📋 FIELD PERFORMANCE")
print("="*70)
field_perf = metrics['field_performance']
sorted_fields = sorted(
    field_perf.items(),
    key=lambda x: x[1]['accuracy']
)

for field, stats in sorted_fields[:5]:  # Show worst 5 fields
    print(f"{field}:")
    print(f"  Accuracy: {stats['accuracy']*100:.2f}%")
    print(f"  Total: {stats['total_extractions']}")
    print(f"  Corrections: {stats['corrections']}")
    print(f"  Avg Confidence: {stats['avg_confidence']:.2f}")

# Print strategy distribution
print("\n" + "="*70)
print("📊 STRATEGY DISTRIBUTION (selected strategies)")
print("="*70)
strategy_dist = metrics['strategy_distribution']
total_selections = sum(strategy_dist.values())
for strategy, count in sorted(strategy_dist.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_selections * 100) if total_selections > 0 else 0
    print(f"{strategy}: {count} ({percentage:.1f}%)")

# Test new metrics
print("\n" + "="*70)
print("📈 LEARNING PROGRESS")
print("="*70)
learning = metrics.get('learning_progress', {})
print(f"Total Batches: {learning.get('total_batches', 0)}")
print(f"First Batch Accuracy: {learning.get('first_batch_accuracy', 0):.1%}")
print(f"Last Batch Accuracy: {learning.get('last_batch_accuracy', 0):.1%}")
print(f"Improvement Rate: {learning.get('improvement_rate', 0):.2f}%")

batches = learning.get('batches', [])
if batches:
    print(f"\nShowing first 3 and last 3 batches:")
    for batch in batches[:3]:
        print(f"  Batch {batch['batch_number']}: {batch['accuracy']:.1%} (docs {batch['start_doc']}-{batch['end_doc']})")
    if len(batches) > 6:
        print("  ...")
    for batch in batches[-3:]:
        print(f"  Batch {batch['batch_number']}: {batch['accuracy']:.1%} (docs {batch['start_doc']}-{batch['end_doc']})")

print("\n" + "="*70)
print("📊 CONFIDENCE TRENDS")
print("="*70)
confidence = metrics.get('confidence_trends', {})
print(f"Overall Avg Confidence: {confidence.get('avg_confidence', 0):.1%}")

by_strategy = confidence.get('by_strategy', {})
if by_strategy:
    print("\nBy Strategy:")
    for strategy, stats in by_strategy.items():
        print(f"  {strategy.upper()}:")
        print(f"    Avg: {stats['avg_confidence']:.1%}")
        print(f"    Range: {stats['min_confidence']:.1%} - {stats['max_confidence']:.1%}")
        print(f"    Samples: {stats['sample_count']}")

print("\n" + "="*70)
print("🔍 ERROR PATTERNS")
print("="*70)
errors = metrics.get('error_patterns', {})
print(f"Total Unique Error Types: {errors.get('total_unique_errors', 0)}")

problematic = errors.get('most_problematic_fields', [])
if problematic:
    print("\nMost Problematic Fields:")
    for field in problematic[:5]:
        print(f"\n  {field['field_name']}: {field['error_count']} errors")
        for example in field['examples'][:2]:
            print(f"    Original: {example['original']}")
            print(f"    Corrected: {example['corrected']}")

print("\n" + "="*70)
print("✅ Metrics test completed!")
print("="*70)
