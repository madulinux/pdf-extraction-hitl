#!/usr/bin/env python3
"""
Test extraction to debug error
"""
import sys
sys.path.insert(0, '.')

from database.db_manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
from database.repositories.feedback_repository import FeedbackRepository
from core.extraction.services import ExtractionService
import traceback

try:
    print("🔧 Initializing services...")
    db = DatabaseManager()
    doc_repo = DocumentRepository(db)
    feedback_repo = FeedbackRepository(db)
    
    extraction_service = ExtractionService(
        document_repo=doc_repo,
        feedback_repo=feedback_repo,
        upload_folder='uploads',
        model_folder='models',
        feedback_folder='feedback'
    )
    
    print("✅ Services initialized successfully")
    
    # Try to get template
    from database.repositories.template_repository import TemplateRepository
    template_repo = TemplateRepository(db)
    
    template = template_repo.find_by_id(1)
    print(f"\n📋 Template: {template}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n🔍 Traceback:")
    traceback.print_exc()
