#!/usr/bin/env python3
"""
Test full extraction flow to debug why table extraction doesn't work in production
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

from database.db_manager import DatabaseManager
from database.repositories.template_repository import TemplateRepository
from core.extraction.hybrid_strategy import HybridExtractionStrategy

def main():
    # Test with document 71
    pdf_path = "/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend/uploads/20251114_183553_2025-11-14_183551_592099_0.pdf"
    
    print(f"\n🔍 TESTING FULL EXTRACTION FLOW (like production)")
    print("="*60)
    print(f"Document: {Path(pdf_path).name}")
    print(f"Expected: area_finding_1 = 'Defense value require.'")
    print(f"Database showed: area_finding_1 = '899892063' (WRONG!)")
    print()
    
    # Get template config
    db = DatabaseManager()
    template_repo = TemplateRepository(db)
    template = template_repo.find_by_id(2)
    
    if not template:
        print("❌ Template not found")
        return
    
    print(f"📋 Template: {template.name}")
    print(f"   Fields: {len(template.fields) if hasattr(template, 'fields') else 'unknown'}")
    
    # Create hybrid strategy (like production)
    hybrid_strategy = HybridExtractionStrategy(db=db)
    
    # Extract all fields
    print(f"\n🚀 Starting extraction...")
    result = hybrid_strategy.extract_all_fields(
        pdf_path=pdf_path,
        template_config=template,
        model_path=f"models/template_{template.id}_model.joblib"
    )
    
    # Check table fields
    table_fields = ['area_finding_1', 'area_finding_2', 'area_recomendation_1', 'area_id_1']
    
    print(f"\n📊 RESULTS:")
    print("="*60)
    
    for field_name in table_fields:
        if field_name in result['extracted_data']:
            value = result['extracted_data'][field_name]
            confidence = result['confidence_scores'].get(field_name, 0)
            method = result.get('extraction_methods', {}).get(field_name, 'unknown')
            
            # Check if correct
            is_correct = False
            if field_name == 'area_finding_1':
                is_correct = 'Defense' in value or 'require' in value
            elif field_name == 'area_finding_2':
                is_correct = 'Mouth' in value or 'expect' in value
            elif field_name == 'area_recomendation_1':
                is_correct = 'Nice' in value or 'relate' in value
            elif field_name == 'area_id_1':
                is_correct = '899892063' in value
            
            status = "✅ CORRECT" if is_correct else "❌ WRONG"
            
            print(f"\n{field_name}: {status}")
            print(f"  Value: {value[:100]}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Method: {method}")
        else:
            print(f"\n{field_name}: ❌ NOT FOUND")

if __name__ == '__main__':
    main()
