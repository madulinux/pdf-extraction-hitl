"""
Test extraction with new scoring logic
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

from database.db_manager import DatabaseManager
from core.extraction.services import ExtractionService
import json

db = DatabaseManager()
service = ExtractionService(db)

# Test with document 119
pdf_path = "/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend/uploads/20251108_190458_2025-11-08_120443_259262_18.pdf"
template_id = 1

print("🔍 Testing extraction with database-driven strategy selection...")
print(f"PDF: {pdf_path}")
print(f"Template ID: {template_id}\n")

result = service.extract_document(pdf_path, template_id)

print("\n📊 EXTRACTION RESULTS:")
print("=" * 70)

# Show strategies used
if 'metadata' in result and 'strategies_used' in result['metadata']:
    print("\n🎯 Strategies Selected:")
    for strategy in result['metadata']['strategies_used']:
        field = strategy['field']
        method = strategy['method']
        conf = strategy['confidence']
        
        # Get DB performance for this field
        cursor = db.execute("""
            SELECT strategy_type, ROUND(accuracy * 100, 2) as acc_pct
            FROM strategy_performance
            WHERE template_id = ? AND field_name = ?
            ORDER BY accuracy DESC
        """, (template_id, field))
        
        perf_data = cursor.fetchall()
        perf_str = ", ".join([f"{p['strategy_type']}:{p['acc_pct']}%" for p in perf_data])
        
        print(f"  {field:20s}: {method:15s} (conf: {conf:.3f}) | DB perf: [{perf_str}]")

# Show extracted values
print("\n📝 Extracted Values:")
for field, value in result['extracted_data'].items():
    print(f"  {field:20s}: {value}")

print("\n" + "=" * 70)
