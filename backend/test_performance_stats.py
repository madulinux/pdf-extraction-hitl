#!/usr/bin/env python3
"""
Test performance stats specifically
"""
import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from core.learning.metrics import PerformanceMetrics

db = DatabaseManager()
metrics_service = PerformanceMetrics(db)

template_id = 1

print("🔍 Testing performance stats...")

# Get documents
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM documents WHERE template_id = ?", (template_id,))
documents = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f"\n📊 Found {len(documents)} documents")
for doc in documents:
    print(f"   ID {doc['id']}: extraction_time_ms = {doc.get('extraction_time_ms', 'N/A')}")

# Calculate performance stats
print(f"\n🔧 Calculating performance stats...")
performance_stats = metrics_service._calculate_performance_stats(documents)

print(f"\n📊 Performance Stats:")
print(f"   Documents timed: {performance_stats['documents_timed']}")
print(f"   Avg time: {performance_stats['avg_time_ms']} ms")
print(f"   Min time: {performance_stats['min_time_ms']} ms")
print(f"   Max time: {performance_stats['max_time_ms']} ms")
print(f"   Total time: {performance_stats['total_time_sec']} sec")
print(f"   By strategy: {performance_stats['by_strategy']}")
