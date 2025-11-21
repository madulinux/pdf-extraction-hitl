"""
Upload Documents Script
Upload PDF documents to the system with experiment_phase tracking

Usage:
    python upload_documents.py --template-id 1 --folder storage/output/letter_template --experiment-phase baseline
    python upload_documents.py --template-id 1 --folder storage/output/letter_template --experiment-phase adaptive
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_manager import DatabaseManager
from database.repositories.document_repository import DocumentRepository
from database.repositories.template_repository import TemplateRepository
from core.extraction.services import ExtractionService
from core.templates.config_loader import get_config_loader
import argparse
from pathlib import Path
from werkzeug.datastructures import FileStorage
import io


def upload_documents(
    template_id: int,
    folder: str,
    experiment_phase: str = None,
    limit: int = None
):
    """
    Upload PDF documents to the system
    
    Args:
        template_id: Template ID
        folder: Folder containing PDF files
        experiment_phase: Experiment phase ('baseline', 'adaptive', or None)
        limit: Maximum number of documents to upload (None = all)
    """
    db = DatabaseManager()
    doc_repo = DocumentRepository(db)
    template_repo = TemplateRepository(db)
    
    # Get template
    template = template_repo.find_by_id(template_id)
    if not template:
        print(f"❌ Template {template_id} not found")
        return
    
    print("="*70)
    print("📤 UPLOAD DOCUMENTS")
    print("="*70)
    print(f"Template: {template.name} (ID: {template_id})")
    print(f"Folder: {folder}")
    print(f"Experiment Phase: {experiment_phase or 'production'}")
    print()
    
    # Get PDF files
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"❌ Folder not found: {folder}")
        return
    
    pdf_files = sorted(list(folder_path.glob("*.pdf")))
    
    if limit:
        pdf_files = pdf_files[:limit]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {folder}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print()
    
    # Initialize extraction service
    service = ExtractionService(
        document_repo=doc_repo,
        feedback_repo=None,  # Not needed for upload
        template_repo=template_repo,
        training_repo=None,  # Not needed for upload
        upload_folder="uploads",
        model_folder="models",
        feedback_folder="feedback"
    )
    
    # Upload and extract each document
    success_count = 0
    failed_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"  [{i}/{len(pdf_files)}] Processing {pdf_file.name}...", end=" ")
            
            # Read file
            with open(pdf_file, 'rb') as f:
                file_data = f.read()
            
            # Create FileStorage object
            file_storage = FileStorage(
                stream=io.BytesIO(file_data),
                filename=pdf_file.name,
                content_type='application/pdf'
            )
            
            # Extract document
            result = service.extract_document(
                file=file_storage,
                template_id=template_id,
                template_config_path=template.config_path,
                experiment_phase=experiment_phase
            )
            
            print(f"✅ Doc ID: {result['document_id']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            failed_count += 1
    
    # Summary
    print()
    print("="*70)
    print("📊 UPLOAD SUMMARY")
    print("="*70)
    print(f"Total Files: {len(pdf_files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Experiment Phase: {experiment_phase or 'production'}")
    print("="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload PDF documents to the system')
    parser.add_argument('--template-id', type=int, required=True, help='Template ID')
    parser.add_argument('--folder', type=str, required=True, help='Folder containing PDF files')
    parser.add_argument('--experiment-phase', type=str, default=None,
                       help='Experiment phase (baseline, adaptive, or omit for production)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of documents to upload')
    
    args = parser.parse_args()
    
    upload_documents(
        args.template_id,
        args.folder,
        args.experiment_phase,
        args.limit
    )
