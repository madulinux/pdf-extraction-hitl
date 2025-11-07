"""
Model Service
Business logic for model training and metrics

Separation of Concerns:
- Routes: HTTP handling
- Service: Business logic (THIS FILE)
- Database: Data access
"""
from typing import Dict, Any, Optional, List
import os
import pdfplumber
import json
from .learner import AdaptiveLearner
from .training_utils import (
    split_training_data, 
    validate_training_data_diversity,
    detect_data_leakage,
    get_training_recommendations
)
from database.db_manager import DatabaseManager


class ModelService:
    """Service layer for model operations"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()
    
    def retrain_model(
        self,
        template_id: int,
        use_all_feedback: bool,
        model_folder: str
    ) -> Dict[str, Any]:
        """
        Retrain CRF model using accumulated feedback
        
        Args:
            template_id: Template ID
            use_all_feedback: Whether to use all feedback or only unused
            model_folder: Folder where models are stored
            
        Returns:
            Training results with metrics
        """
        # Get template
        template = self.db.get_template(template_id)
        if not template:
            raise ValueError(f"Template with ID {template_id} not found")
        
        # Get feedback for training (corrected data)
        feedback_list = self.db.get_feedback_for_training(
            template_id=template_id,
            unused_only=not use_all_feedback
        )
        
        # Get high-confidence extractions (validated but not corrected)
        validated_docs = self.db.get_validated_documents(template_id)
        
        if not feedback_list and not validated_docs:
            raise ValueError("No training data available (no feedback or validated documents)")
        
        # Prepare training data
        X_train = []
        y_train = []
        feedback_ids = []
        
        print(f"📊 Training data sources:")
        print(f"   - Feedback (corrected): {len(feedback_list)} records")
        print(f"   - Validated (high-confidence): {len(validated_docs)} documents")
        
        # 1. Add feedback data (user corrections - highest priority)
        # Group feedback by document_id to create complete training samples
        feedback_by_doc = {}
        for feedback in feedback_list:
            doc_id = feedback['document_id']
            if doc_id not in feedback_by_doc:
                feedback_by_doc[doc_id] = []
            feedback_by_doc[doc_id].append(feedback)
        
        print(f"   - Unique documents with feedback: {len(feedback_by_doc)}")
        
        for doc_id, doc_feedbacks in feedback_by_doc.items():
            # Get document
            document = self.db.get_document(doc_id)
            if not document:
                continue
            
            # Extract words from PDF
            with pdfplumber.open(document['file_path']) as pdf:
                words = []
                for page in pdf.pages:
                    page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    words.extend(page_words)
            
            # ✅ FIX: Include ALL fields (corrected + non-corrected) for complete context
            # Get extraction results to include non-corrected fields
            extraction_result = json.loads(document['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            confidence_scores = extraction_result.get('confidence_scores', {})
            
            # Create complete feedback list (corrected + high-confidence non-corrected)
            complete_feedbacks = []
            corrected_fields = set(fb['field_name'] for fb in doc_feedbacks)
            
            # Add corrected fields
            for fb in doc_feedbacks:
                complete_feedbacks.append(fb)
            
            # Add non-corrected fields with high confidence
            for field_name, value in extracted_data.items():
                if field_name not in corrected_fields:
                    confidence = confidence_scores.get(field_name, 0.0)
                    if confidence >= 0.65:
                        complete_feedbacks.append({
                            'field_name': field_name,
                            'corrected_value': value
                        })
            
            print(f"\n📝 [Feedback Training] Document {doc_id}:")
            print(f"   Corrected fields: {len(doc_feedbacks)}")
            print(f"   Non-corrected fields: {len(complete_feedbacks) - len(doc_feedbacks)}")
            print(f"   Total fields: {len(complete_feedbacks)}")
            
            # Create BIO sequence with ALL fields for this document
            learner = AdaptiveLearner()
            features, labels = learner._create_bio_sequence_multi(complete_feedbacks, words)
            
            if features and labels:
                X_train.append(features)
                y_train.append(labels)
                # Mark all feedbacks from this document
                for fb in doc_feedbacks:
                    feedback_ids.append(fb['id'])
        
        # 2. Add high-confidence validated data (no corrections needed)
        # Get all document IDs that have feedback to avoid duplicate training
        docs_with_feedback = set(feedback_by_doc.keys())
        
        print(f"\n📊 Processing {len(validated_docs)} validated documents...")
        print(f"   Documents with feedback: {docs_with_feedback}")
        
        for document in validated_docs:
            doc_id = document['id']
            
            # Parse extraction results
            extraction_result = json.loads(document['extraction_result'])
            extracted_data = extraction_result.get('extracted_data', {})
            confidence_scores = extraction_result.get('confidence_scores', {})
            
            # Extract words from PDF
            with pdfplumber.open(document['file_path']) as pdf:
                words = []
                for page in pdf.pages:
                    page_words = page.extract_words(x_tolerance=3, y_tolerance=3)
                    words.extend(page_words)
            
            # ✅ FIX: Create pseudo-feedbacks for fields NOT in feedback
            # If document has feedback, only train fields that were NOT corrected
            pseudo_feedbacks = []
            
            print(f"\n   📄 Document {doc_id}:")
            print(f"      Has feedback: {doc_id in docs_with_feedback}")
            print(f"      Extracted fields: {list(extracted_data.keys())}")
            print(f"      Confidence scores: {confidence_scores}")
            
            if doc_id in docs_with_feedback:
                # ✅ SKIP: Document already trained from feedback
                # Feedback training (lines 84-135) already includes:
                # - Corrected fields (from feedback.corrected_value)
                # - Non-corrected fields (from extracted_data)
                # To avoid duplicate training, we skip validated training for these docs
                print(f"      ⏭️  Skipping: Already trained from feedback")
                continue
            else:
                # No feedback for this document, train all high-confidence fields
                print(f"      No feedback, checking all fields...")
                for field_name, value in extracted_data.items():
                    confidence = confidence_scores.get(field_name, 0.0)
                    print(f"         Checking {field_name}: conf={confidence:.2f}, threshold=0.65")
                    if confidence >= 0.65:  # ✅ Lower threshold to include more fields
                        pseudo_feedbacks.append({
                            'field_name': field_name,
                            'corrected_value': value
                        })
                        print(f"         ✅ Added {field_name}")
            
            # ✅ Train with ALL fields together (like real feedback)
            if pseudo_feedbacks:
                print(f"\n📝 [Training] Processing validated document {doc_id} with {len(pseudo_feedbacks)} fields:")
                for pf in pseudo_feedbacks:
                    print(f"   - {pf['field_name']}: '{pf['corrected_value'][:50]}...'")
                
                learner = AdaptiveLearner()
                features, labels = learner._create_bio_sequence_multi(
                    pseudo_feedbacks, 
                    words
                )
                
                if features and labels:
                    # Count labeled fields
                    unique_labels = set(labels)
                    field_labels = [l for l in unique_labels if l != 'O']
                    print(f"   ✅ Created training sample with labels: {field_labels}")
                    
                    X_train.append(features)
                    y_train.append(labels)
                else:
                    print(f"   ❌ Failed to create training sample!")
        
        if not X_train:
            raise ValueError("Could not prepare training data")
        
        print(f"\n📊 Training Summary:")
        print(f"   Total training samples: {len(X_train)}")
        print(f"   From feedback: {len(feedback_by_doc)}")
        print(f"   From validated: {len(X_train) - len(feedback_by_doc)}")
        
        # Count unique labels across all training samples
        all_labels = set()
        for labels in y_train:
            all_labels.update(labels)
        all_labels.discard('O')
        print(f"   Unique labels in training data: {sorted(all_labels)}")
        
        # ✅ VALIDATE DATA QUALITY
        print(f"\n🔍 Validating training data quality...")
        diversity_metrics = validate_training_data_diversity(X_train, y_train)
        
        # ✅ SPLIT DATA: Train (80%) / Test (20%)
        print(f"\n📊 Splitting data into train/test sets...")
        X_train_split, X_test_split, y_train_split, y_test_split = split_training_data(
            X_train, y_train,
            test_size=0.2,
            random_state=42
        )
        
        # ✅ CHECK FOR DATA LEAKAGE
        print(f"\n🔍 Checking for data leakage...")
        leakage_results = detect_data_leakage(X_train_split, X_test_split)
        
        # ✅ GET RECOMMENDATIONS
        recommendations = get_training_recommendations(
            num_samples=len(X_train),
            diversity_score=diversity_metrics['diversity_score'],
            has_leakage=leakage_results['leakage_detected']
        )
        
        print(f"\n💡 Training Recommendations:")
        for rec in recommendations:
            print(f"   {rec}")
        
        # Initialize or load existing model
        model_path = os.path.join(model_folder, f"template_{template_id}_model.joblib")
        
        learner = AdaptiveLearner(model_path if os.path.exists(model_path) else None)
        
        # ✅ Train model on TRAINING SET only
        print(f"\n🎓 Training model on {len(X_train_split)} samples...")
        metrics = learner.train(X_train_split, y_train_split)
        
        # ✅ Evaluate on TEST SET (unseen data)
        print(f"\n📊 Evaluating on {len(X_test_split)} test samples...")
        test_metrics = learner.evaluate(X_test_split, y_test_split)
        
        print(f"\n📈 Results Comparison:")
        print(f"   Training Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
        print(f"   Test Accuracy:     {test_metrics.get('accuracy', 0)*100:.2f}%")
        print(f"   Difference:        {abs(metrics.get('accuracy', 0) - test_metrics.get('accuracy', 0))*100:.2f}%")
        
        if abs(metrics.get('accuracy', 0) - test_metrics.get('accuracy', 0)) > 0.1:
            print(f"   ⚠️  WARNING: Large gap between train/test accuracy!")
            print(f"       This indicates overfitting. Model memorized training data.")
        else:
            print(f"   ✅ Good generalization. Model should work on new data.")
        
        # Save model
        learner.save_model(model_path)
        
        # Mark feedback as used
        self.db.mark_feedback_used(feedback_ids)
        
        # Save training history with BOTH train and test metrics
        self.db.create_training_record(
            template_id=template_id,
            model_path=model_path,
            training_samples=len(X_train_split),
            metrics=test_metrics  # ✅ Save TEST metrics (real performance)
        )
        
        return {
            'template_id': template_id,
            'model_path': model_path,
            'training_samples': len(X_train_split),
            'test_samples': len(X_test_split),
            'train_metrics': metrics,
            'test_metrics': test_metrics,  # ✅ Real performance on unseen data
            'diversity_metrics': diversity_metrics,
            'leakage_detected': leakage_results['leakage_detected'],
            'recommendations': recommendations
        }
    
    def get_training_history(self, template_id: int) -> List[Dict]:
        """Get training history for a template"""
        return self.db.get_training_history(template_id)
    
    def get_latest_metrics(self, template_id: int) -> Optional[Dict]:
        """
        Get latest model metrics for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            Latest metrics or None if no history
        """
        history = self.db.get_training_history(template_id)
        
        if not history:
            return None
        
        latest = history[0]  # Most recent training
        
        return {
            'template_id': template_id,
            'metrics': {
                'accuracy': latest['accuracy'],
                'precision': latest['precision_score'],
                'recall': latest['recall_score'],
                'f1': latest['f1_score'],
                'training_samples': latest['training_samples'],
                'trained_at': latest['trained_at']
            }
        }
    
    def get_feedback_statistics(self, template_id: int) -> Dict[str, Any]:
        """
        Get feedback statistics for a template
        
        Args:
            template_id: Template ID
            
        Returns:
            Feedback statistics
        """
        all_feedback = self.db.get_feedback_for_training(template_id, unused_only=False)
        unused_feedback = self.db.get_feedback_for_training(template_id, unused_only=True)
        
        return {
            'template_id': template_id,
            'stats': {
                'total_feedback': len(all_feedback),
                'unused_feedback': len(unused_feedback),
                'used_feedback': len(all_feedback) - len(unused_feedback)
            }
        }
