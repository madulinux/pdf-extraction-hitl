#!/usr/bin/env python3
"""
Test CRF extraction to see if smart stopping logic works
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.extraction.strategies import CRFExtractionStrategy
from core.pdf.extractor import PDFExtractor
import json

# Get latest document
import sqlite3
conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()
cursor.execute("SELECT id, file_path FROM documents ORDER BY id DESC LIMIT 1")
doc_id, pdf_path = cursor.fetchone()
conn.close()

print(f"📄 Testing document {doc_id}: {pdf_path}")
print("=" * 80)

# Extract words
extractor = PDFExtractor()
all_words = extractor.extract_words(pdf_path)
print(f"✅ Extracted {len(all_words)} words from PDF")

# Load model
model_path = "models/template_1_model.joblib"
crf_strategy = CRFExtractionStrategy(model_path=model_path)

# Test fields that usually have problems
test_fields = ['event_location', 'issue_place', 'supervisor_name']

for field_name in test_fields:
    print(f"\n{'='*80}")
    print(f"🔍 Testing field: {field_name}")
    print(f"{'='*80}")
    
    # Dummy field config
    field_config = {
        'field_name': field_name,
        'locations': [{'x': 0, 'y': 0, 'width': 100, 'height': 100}]
    }
    
    result = crf_strategy.extract(pdf_path, field_config, all_words)
    
    if result:
        print(f"✅ Extracted: {result.value}")
        print(f"   Confidence: {result.confidence:.4f}")
        print(f"   Method: {result.method}")
        if 'raw_value' in result.metadata:
            raw = result.metadata['raw_value']
            if raw != result.value:
                print(f"   Raw value: {raw}")
                print(f"   Cleaned: {result.value}")
    else:
        print(f"❌ No extraction")

print(f"\n{'='*80}")
print("✅ Test complete")
