#!/usr/bin/env python3
"""
Test table extraction with detailed logging
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.extraction.rule_based_strategy import RuleBasedExtractionStrategy
from core.extraction.hybrid_strategy import HybridExtractionStrategy
from database.db_manager import DatabaseManager
from database.repositories.template_repository import TemplateRepository

def main():
    # Find latest mixed_template document
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.id, d.file_path, d.filename
        FROM documents d
        WHERE d.template_id = 2
        ORDER BY d.created_at DESC
        LIMIT 1
    """)
    
    doc = cursor.fetchone()
    if not doc:
        print("❌ No documents found for mixed_template")
        return
    
    doc_id, pdf_path, filename = doc
    print(f"\n📄 Testing document: {filename}")
    print(f"   Path: {pdf_path}")
    print(f"   ID: {doc_id}")
    
    # Get template config
    template_repo = TemplateRepository(db)
    template = template_repo.get_by_id(2)
    
    if not template:
        print("❌ Template not found")
        return
    
    print(f"\n📋 Template: {template['name']}")
    print(f"   Fields: {len(template['fields'])}")
    
    # Test table fields
    table_fields = [f for f in template['fields'] if '_finding_' in f['field_name'] or '_recomendation_' in f['field_name']]
    
    print(f"\n🔍 Testing {len(table_fields)} table fields:")
    
    # Initialize strategy
    strategy = RuleBasedExtractionStrategy()
    
    # Extract words from PDF
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
    
    print(f"   Total words extracted: {len(words)}")
    
    # Test each table field
    for field in table_fields[:3]:  # Test first 3
        field_name = field['field_name']
        print(f"\n{'='*60}")
        print(f"Testing: {field_name}")
        print(f"{'='*60}")
        
        # Check if looks like table field
        is_table = strategy._looks_like_table_field(field_name)
        print(f"  looks_like_table_field: {is_table}")
        
        # Try table extraction
        result = strategy._try_table_extraction(pdf_path, field, words)
        
        if result:
            print(f"  ✅ SUCCESS!")
            print(f"     Value: {result.value[:100]}")
            print(f"     Confidence: {result.confidence}")
            print(f"     Method: {result.method}")
            print(f"     Metadata: {result.metadata}")
        else:
            print(f"  ❌ FAILED - returned None")
    
    conn.close()

if __name__ == '__main__':
    main()
