#!/usr/bin/env python3
"""
Simple test for table extraction
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.extraction.table_extractor import AdaptiveTableExtractor

def main():
    # Test with latest document (document 71)
    pdf_path = "/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend/uploads/20251114_183553_2025-11-14_183551_592099_0.pdf"
    
    print(f"\n🔍 Testing if table extraction works for document 71...")
    print(f"   This document showed WRONG extraction in database:")
    print(f"   - area_finding_1: got '899892063' (area code) instead of finding text")
    print(f"   - area_recomendation_1: got '899892063' (area code) instead of recommendation text")
    
    print(f"\n📄 Testing: {Path(pdf_path).name}")
    print("="*60)
    
    # Create extractor
    extractor = AdaptiveTableExtractor()
    
    # Extract tables
    print("\n🔍 Extracting tables...")
    tables = extractor.extract_tables(pdf_path, page_number=0)
    
    print(f"   Found {len(tables)} tables")
    
    if not tables:
        print("   ❌ NO TABLES FOUND!")
        return
    
    # Show table structure
    for i, table in enumerate(tables):
        print(f"\n📊 Table {i+1}:")
        print(f"   Rows: {len(table)}")
        print(f"   Columns: {len(table[0]) if table else 0}")
        
        # Show first 5 rows
        for j, row in enumerate(table[:5]):
            print(f"   Row {j}: {row}")
    
    # Test finding fields
    test_fields = [
        'area_finding_1',
        'area_finding_2',
        'area_recomendation_1',
        'area_id_1'
    ]
    
    print(f"\n🔍 Testing field extraction:")
    print("="*60)
    
    for field_name in test_fields:
        print(f"\n{field_name}:")
        
        field_config = {'field_name': field_name}
        result = extractor.find_field_in_tables(tables, field_name, field_config, [])
        
        if result:
            value, confidence, metadata = result
            print(f"  ✅ Found: {value[:100]}")
            print(f"     Confidence: {confidence}")
            print(f"     Metadata: {metadata}")
        else:
            print(f"  ❌ Not found")

if __name__ == '__main__':
    main()
