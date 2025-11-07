"""
Extraction Service
Business logic for document extraction
"""
from typing import Dict, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from .repositories import DocumentRepository, FeedbackRepository
from .extractor import DataExtractor
from shared.exceptions import NotFoundError, ValidationError


class ExtractionService:
    """Service layer for extraction operations"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        feedback_repo: FeedbackRepository,
        upload_folder: str,
        model_folder: str,
        feedback_folder: str
    ):
        self.document_repo = document_repo
        self.feedback_repo = feedback_repo
        self.upload_folder = upload_folder
        self.model_folder = model_folder
        self.feedback_folder = feedback_folder
    
    def extract_document(
        self,
        file: FileStorage,
        template_id: int,
        template_config_path: str
    ) -> Dict[str, Any]:
        """
        Extract data from filled PDF document
        
        Args:
            file: Uploaded PDF file
            template_id: Template ID to use
            template_config_path: Path to template configuration
            
        Returns:
            Extraction results with document info
        """
        # Load template config
        import json
        with open(template_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Save uploaded document
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, filename)
        file.save(filepath)
        
        # Create document record
        document_id = self.document_repo.create(
            template_id=template_id,
            filename=filename,
            file_path=filepath
        )
        
        # Check if model exists for this template
        model_path = os.path.join(self.model_folder, f"template_{template_id}_model.joblib")
        # print(f"🔍 [ExtractionService] Checking model: {model_path}")
        if not os.path.exists(model_path):
            # print(f"❌ [ExtractionService] Model NOT found: {model_path}")
            model_path = None
        # else:

            # print(f"✅ [ExtractionService] Model found: {model_path}")
        
        # Extract data
        # print(f"🔍 [ExtractionService] Creating DataExtractor with model_path: {model_path}")
        extractor = DataExtractor(config, model_path)
        results = extractor.extract(filepath)
        
        # Update document with results
        self.document_repo.update_extraction(
            document_id=document_id,
            extraction_result=json.dumps(results),
            status='extracted'
        )
        
        return {
            'document_id': document_id,
            'results': results,
            'template_id': template_id,
            'filename': filename
        }
    
    def save_corrections(
        self,
        document_id: int,
        corrections: Dict
    ) -> Dict[str, Any]:
        """
        Save user corrections as feedback and trigger adaptive learning
        
        Args:
            document_id: Document ID
            corrections: Corrections dictionary
            
        Returns:
            Feedback info
        """
        # Get document
        document = self.document_repo.find_by_id(document_id)
        if not document:
            raise NotFoundError(f"Document with ID {document_id} not found")
        
        # Load original extraction results
        original_results = json.loads(document.extraction_result)
        
        # Save feedback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        feedback_filename = f"feedback_{document_id}_{timestamp}.json"
        feedback_path = os.path.join(self.feedback_folder, feedback_filename)
        
        feedback_data = {
            'document_id': document_id,
            'template_id': document.template_id,
            'original_results': original_results,
            'corrections': corrections,
            'timestamp': timestamp
        }
        
        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2)
        
        # Store feedback in database (one record per corrected field)
        # Uses UPSERT: updates existing feedback or creates new
        extracted_data = original_results.get('extracted_data', {})
        confidence_scores = original_results.get('confidence_scores', {})
        
        feedback_ids = self.feedback_repo.upsert(
            document_id=document_id,
            corrections=corrections,
            original_data=extracted_data,      # ✅ Pass original values
            confidence_scores=confidence_scores,  # ✅ Pass confidence scores
            feedback_path=feedback_path
        )
        
        # ✅ KEEP original extraction_result unchanged in documents table
        # Corrected values are stored in feedback table
        # This preserves the original extraction for comparison and metrics
        
        # Note: To get validated data, query:
        # 1. Get extraction_result from documents table (original)
        # 2. Get corrections from feedback table
        # 3. Merge: use corrected_value if exists, else use original
        
        # Optional: Update metadata to mark as validated
        updated_results = original_results.copy()
        if 'metadata' not in updated_results:
            updated_results['metadata'] = {}
        updated_results['metadata']['validated'] = True
        updated_results['metadata']['validated_at'] = timestamp
        updated_results['metadata']['corrections_count'] = len(corrections)
        
        # Save metadata update (but keep extracted_data unchanged)
        self.document_repo.update_extraction_result(document_id, updated_results)
        
        # Update document status
        self.document_repo.update_status(document_id, 'validated')
        
        # 🎯 ADAPTIVE LEARNING: Learn from feedback
        # This improves future extractions for this template
        try:
            # Load template config
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            template = db.get_template(document.template_id)
            
            if template and template['config_path']:
                with open(template['config_path'], 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Check if model exists
                model_path = os.path.join(self.model_folder, f"template_{document.template_id}_model.joblib")
                if not os.path.exists(model_path):
                    model_path = None
                
                # Create extractor and learn from feedback
                extractor = DataExtractor(config, model_path)
                extractor.learn_from_feedback(original_results, corrections)
                
                print(f"✅ Adaptive learning completed for template {document.template_id}")
        except Exception as e:
            print(f"⚠️ Adaptive learning failed: {e}")
            # Don't fail the whole operation if learning fails
        
        return {
            'feedback_ids': feedback_ids,  # List of feedback IDs (one per field)
            'document_id': document_id,
            'corrections_count': len(corrections)
        }
    
    def get_all_documents(self):
        """Get all documents"""
        documents = self.document_repo.find_all()
        return [doc.to_dict() for doc in documents]
    
    def get_document_by_id(self, document_id: int) -> Dict:
        """
        Get document by ID with parsed results and feedback history
        
        Args:
            document_id: Document ID
            
        Returns:
            Document data with feedback history or None if not found
        """
        document = self.document_repo.find_by_id(document_id)
        
        if not document:
            return None
        
        result = document.to_dict()
        
        # Parse extraction results if available
        if document.extraction_result:
            result['extraction_result'] = json.loads(document.extraction_result)
        
        # Get feedback history for this document
        feedback_history = self.feedback_repo.find_by_document_id(document_id)
        result['feedback_history'] = feedback_history
        
        return result
