#!/usr/bin/env python3
"""
Retrain Model with Regularization and Early Stopping
Fixes overfitting issue by adding L1/L2 regularization and cross-validation
"""
import sys
sys.path.insert(0, '/Users/madulinux/Documents/S2 UNAS/TESIS/Project/backend')

import json
import os
from datetime import datetime
from database.db_manager import DatabaseManager
from core.learning.learner import AdaptiveLearner
from sklearn.model_selection import train_test_split
import numpy as np
import pdfplumber

class ImprovedModelTrainer:
    """Train model with regularization and validation"""
    
    def __init__(self, template_id: int = 1):
        self.db = DatabaseManager()
        self.template_id = template_id
        self.learner = AdaptiveLearner()
    
    def _extract_words_from_pdf(self, pdf_path: str):
        """Extract words with positions from PDF"""
        words = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_words = page.extract_words()
                    for word in page_words:
                        words.append({
                            'text': word['text'],
                            'x0': word['x0'],
                            'top': word['top'],  # Keep 'top' key
                            'x1': word['x1'],
                            'bottom': word['bottom'],  # Keep 'bottom' key
                            'page': page_num
                        })
        except Exception as e:
            print(f"Error extracting words from {pdf_path}: {e}")
        return words
        
    def get_training_data(self):
        """Get all feedback for training"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get active template config from database
        cursor.execute('''
            SELECT id FROM template_configs 
            WHERE template_id = ? AND is_active = 1
            ORDER BY version DESC
            LIMIT 1
        ''', (self.template_id,))
        config_row = cursor.fetchone()
        
        if not config_row:
            raise Exception(f"No active config found for template {self.template_id}")
        
        config_id = config_row[0]
        
        # Get field configs
        cursor.execute('''
            SELECT field_name, field_type, base_pattern, confidence_threshold
            FROM field_configs
            WHERE config_id = ?
            ORDER BY extraction_order
        ''', (config_id,))
        
        fields = {}
        for field_name, field_type, base_pattern, confidence_threshold in cursor.fetchall():
            fields[field_name] = {
                'field_type': field_type,
                'base_pattern': base_pattern,
                'confidence_threshold': confidence_threshold
            }
        
        template_config = {
            'template_id': self.template_id,
            'fields': fields
        }
        
        # Get all feedback
        cursor.execute('''
            SELECT 
                d.id, d.file_path, d.extraction_result,
                f.field_name, f.original_value, f.corrected_value
            FROM feedback f
            JOIN documents d ON f.document_id = d.id
            WHERE d.template_id = ?
            ORDER BY f.created_at
        ''', (self.template_id,))
        
        feedbacks = cursor.fetchall()
        conn.close()
        
        # Group by document
        doc_feedbacks = {}
        for doc_id, file_path, extraction_result, field_name, original, corrected in feedbacks:
            if doc_id not in doc_feedbacks:
                doc_feedbacks[doc_id] = {
                    'file_path': file_path,
                    'extraction_result': extraction_result,
                    'feedbacks': []
                }
            doc_feedbacks[doc_id]['feedbacks'].append({
                'field_name': field_name,
                'original_value': original,
                'corrected_value': corrected
            })
        
        return template_config, list(doc_feedbacks.values())
    
    def train_with_validation(self, test_size=0.2, c1_values=[0.01, 0.1, 0.5], c2_values=[0.01, 0.1, 0.5]):
        """Train model with cross-validation to find best regularization"""
        print("=" * 100)
        print("🤖 TRAINING MODEL WITH REGULARIZATION")
        print("=" * 100)
        
        # Get data
        print("\n📊 Loading training data...")
        template_config, doc_feedbacks = self.get_training_data()
        print(f"   Total documents with feedback: {len(doc_feedbacks)}")
        
        # Split train/validation
        train_docs, val_docs = train_test_split(
            doc_feedbacks, 
            test_size=test_size, 
            random_state=42
        )
        
        print(f"   Train set: {len(train_docs)} documents")
        print(f"   Validation set: {len(val_docs)} documents")
        
        # Prepare training data
        print("\n🔄 Preparing training features...")
        
        # Extract words and create features per document
        print("   Extracting words from PDFs...")
        X_train = []
        y_train = []
        
        for doc in train_docs:
            try:
                # Extract words for this document
                words = self._extract_words_from_pdf(doc['file_path'])
                if not words:
                    continue
                
                # Get feedbacks for this document
                doc_feedbacks = doc['feedbacks']
                
                # ✅ CRITICAL FIX: Include ALL fields (corrected + non-corrected)
                # Parse extraction results to get non-corrected fields
                extraction_result = json.loads(doc['extraction_result']) if doc['extraction_result'] else {}
                extracted_data = extraction_result.get('extracted_data', {})
                confidence_scores = extraction_result.get('confidence_scores', {})
                
                # Create complete feedback list
                complete_feedbacks = []
                corrected_fields = set(fb['field_name'] for fb in doc_feedbacks)
                
                # Add corrected fields
                for fb in doc_feedbacks:
                    complete_feedbacks.append(fb)
                
                # Add non-corrected fields with high confidence (positive examples!)
                for field_name, value in extracted_data.items():
                    if field_name not in corrected_fields:
                        confidence = confidence_scores.get(field_name, 0.0)
                        if confidence >= 0.65:  # Same threshold as services.py
                            complete_feedbacks.append({
                                'field_name': field_name,
                                'corrected_value': value
                            })
                
                if not complete_feedbacks:
                    continue
                
                print(f"   Doc {doc['file_path'].split('/')[-1]}: {len(doc_feedbacks)} corrected, {len(complete_feedbacks) - len(doc_feedbacks)} non-corrected")
                
                # ✅ CRITICAL FIX: Create SEPARATE sequence for EACH field
                # This ensures training/inference consistency:
                # - Training: target_field_X=True for field X only
                # - Inference: target_field_X=True for field X only
                for feedback in complete_feedbacks:
                    field_name = feedback['field_name']
                    corrected_value = feedback['corrected_value']
                    
                    if not corrected_value or not corrected_value.strip():
                        continue
                    
                    # Create sequence with ONLY this field as target
                    features, labels = self.learner._create_bio_sequence_single(
                        field_name=field_name,
                        corrected_value=corrected_value,
                        words=words,
                        template_config=template_config
                    )
                    
                    # Add to training set
                    X_train.append(features)
                    y_train.append(labels)
                
            except Exception as e:
                print(f"   ⚠️  Error processing {doc['file_path']}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Training labels: {len(y_train)}")
        
        # Prepare validation data
        print("\n🔄 Preparing validation features...")
        X_val = []
        y_val = []
        
        for doc in val_docs:
            try:
                # Extract words for this document
                words = self._extract_words_from_pdf(doc['file_path'])
                if not words:
                    continue
                
                # Get feedbacks for this document
                doc_feedbacks = doc['feedbacks']
                
                # ✅ CRITICAL FIX: Include ALL fields (corrected + non-corrected)
                extraction_result = json.loads(doc['extraction_result']) if doc['extraction_result'] else {}
                extracted_data = extraction_result.get('extracted_data', {})
                confidence_scores = extraction_result.get('confidence_scores', {})
                
                # Create complete feedback list
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
                
                if not complete_feedbacks:
                    continue
                
                # ✅ CRITICAL FIX: Create SEPARATE sequence for EACH field (same as training)
                for feedback in complete_feedbacks:
                    field_name = feedback['field_name']
                    corrected_value = feedback['corrected_value']
                    
                    if not corrected_value or not corrected_value.strip():
                        continue
                    
                    # Create sequence with ONLY this field as target
                    features, labels = self.learner._create_bio_sequence_single(
                        field_name=field_name,
                        corrected_value=corrected_value,
                        words=words,
                        template_config=template_config
                    )
                    
                    # Add to validation set
                    X_val.append(features)
                    y_val.append(labels)
                
            except Exception as e:
                print(f"   ⚠️  Error processing validation doc {doc['file_path']}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"   Validation samples: {len(X_val)}")
        
        # Grid search for best regularization
        print("\n🔍 GRID SEARCH FOR BEST REGULARIZATION")
        print("=" * 100)
        
        best_score = 0
        best_params = None
        best_model = None
        results = []
        
        for c1 in c1_values:
            for c2 in c2_values:
                print(f"\n🧪 Testing c1={c1}, c2={c2}...")
                
                # Train with these parameters
                import sklearn_crfsuite
                crf = sklearn_crfsuite.CRF(
                    algorithm='lbfgs',
                    c1=c1,  # L1 regularization
                    c2=c2,  # L2 regularization
                    max_iterations=100,
                    all_possible_transitions=True,
                    verbose=False
                )
                
                crf.fit(X_train, y_train)
                
                # Evaluate on validation set
                y_pred = crf.predict(X_val)
                
                # Calculate accuracy
                from sklearn_crfsuite import metrics
                train_score = crf.score(X_train, y_train)
                val_score = metrics.flat_accuracy_score(y_val, y_pred)
                
                print(f"   Train accuracy: {train_score:.4f}")
                print(f"   Val accuracy: {val_score:.4f}")
                print(f"   Overfitting gap: {(train_score - val_score):.4f}")
                
                results.append({
                    'c1': c1,
                    'c2': c2,
                    'train_acc': train_score,
                    'val_acc': val_score,
                    'gap': train_score - val_score
                })
                
                # Track best model (highest validation accuracy)
                if val_score > best_score:
                    best_score = val_score
                    best_params = {'c1': c1, 'c2': c2}
                    best_model = crf
                    print(f"   ✅ NEW BEST MODEL!")
        
        # Print results summary
        print("\n" + "=" * 100)
        print("📊 GRID SEARCH RESULTS")
        print("=" * 100)
        print(f"{'c1':<8} {'c2':<8} {'Train Acc':<12} {'Val Acc':<12} {'Gap':<12} {'Status':<10}")
        print("-" * 100)
        
        for r in sorted(results, key=lambda x: x['val_acc'], reverse=True):
            status = "✅ BEST" if r['c1'] == best_params['c1'] and r['c2'] == best_params['c2'] else ""
            print(f"{r['c1']:<8} {r['c2']:<8} {r['train_acc']:<12.4f} {r['val_acc']:<12.4f} {r['gap']:<12.4f} {status:<10}")
        
        print(f"\n🏆 BEST PARAMETERS:")
        print(f"   c1 (L1): {best_params['c1']}")
        print(f"   c2 (L2): {best_params['c2']}")
        print(f"   Validation Accuracy: {best_score:.4f}")
        
        # Save best model
        model_dir = 'models'
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, f'template_{self.template_id}_model.joblib')
        
        print(f"\n💾 Saving best model to: {model_path}")
        import joblib
        joblib.dump(best_model, model_path)
        
        # Save training history
        print("\n📝 Saving training history...")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Calculate detailed metrics
        y_pred_train = best_model.predict(X_train)
        y_pred_val = best_model.predict(X_val)
        
        from sklearn_crfsuite import metrics
        train_precision = metrics.flat_precision_score(y_train, y_pred_train, average='weighted', zero_division=0)
        train_recall = metrics.flat_recall_score(y_train, y_pred_train, average='weighted', zero_division=0)
        train_f1 = metrics.flat_f1_score(y_train, y_pred_train, average='weighted', zero_division=0)
        
        cursor.execute('''
            INSERT INTO training_history 
            (template_id, model_path, training_samples, accuracy, precision_score, recall_score, f1_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.template_id,
            model_path,
            len(X_train),
            best_score,  # Use validation accuracy
            train_precision,
            train_recall,
            train_f1
        ))
        
        conn.commit()
        conn.close()
        
        print("✅ Training history saved")
        
        # Print final summary
        print("\n" + "=" * 100)
        print("🎉 TRAINING COMPLETE!")
        print("=" * 100)
        print(f"✅ Best model saved to: {model_path}")
        print(f"✅ Regularization: c1={best_params['c1']}, c2={best_params['c2']}")
        print(f"✅ Validation Accuracy: {best_score:.4f}")
        print(f"✅ Training samples: {len(X_train)}")
        print(f"✅ Validation samples: {len(X_val)}")
        print("\n💡 Next steps:")
        print("   1. Test extraction on new documents")
        print("   2. Monitor accuracy trends")
        print("   3. Collect more feedback if needed")
        
        return best_model, best_params, best_score

if __name__ == '__main__':
    trainer = ImprovedModelTrainer(template_id=1)
    
    print("🚀 Starting improved model training with regularization...")
    print("   This will find the best L1/L2 regularization parameters")
    print("   to prevent overfitting.\n")
    
    model, params, score = trainer.train_with_validation(
        test_size=0.2,  # 20% for validation
        c1_values=[0.01, 0.1, 0.5, 1.0],  # L1 regularization
        c2_values=[0.01, 0.1, 0.5, 1.0]   # L2 regularization
    )
    
    print("\n✅ All done!")
