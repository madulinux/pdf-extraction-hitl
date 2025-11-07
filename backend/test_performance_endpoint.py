#!/usr/bin/env python3
"""
Test performance metrics endpoint
"""
import requests
import json

# Test endpoint
url = "http://localhost:8000/api/v1/learning/performance/1"

# Get token first (if needed)
# For testing, we'll call directly
from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics

db = DatabaseManager()
metrics_service = PerformanceMetrics(db)
metrics = metrics_service.get_template_metrics(1)

print("=" * 60)
print("PERFORMANCE METRICS RESPONSE")
print("=" * 60)
print(json.dumps(metrics, indent=2))
print()

# Check structure
print("=" * 60)
print("STRUCTURE CHECK")
print("=" * 60)
print(f"Has 'overview': {'overview' in metrics}")
print(f"Has 'field_performance': {'field_performance' in metrics}")
print(f"Has 'strategy_distribution': {'strategy_distribution' in metrics}")
print(f"Has 'accuracy_over_time': {'accuracy_over_time' in metrics}")
print(f"Has 'feedback_stats': {'feedback_stats' in metrics}")

if 'overview' in metrics:
    print(f"\nOverview keys: {list(metrics['overview'].keys())}")
    print(f"Has 'total_documents': {'total_documents' in metrics['overview']}")
