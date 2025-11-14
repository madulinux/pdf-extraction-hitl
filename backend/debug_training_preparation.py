"""
Debug: Why training only creates 272 samples instead of 3000?
"""
from database.db_manager import DatabaseManager
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.document_repository import DocumentRepository
import json
import pdfplumber
from core.learning.adaptive_learner import AdaptiveLearner

db = DatabaseManager()
feedback_repo = FeedbackRepository(db)
doc_repo = DocumentRepository(db)

print('🔍 DEBUG: Training Data Preparation')
print('=' * 80)

# Get feedback
feedback_list = feedback_repo.find_for_training(template_id=1, unused_only=False)
print(f'\n📊 FEEDBACK:')
print(f'   Total feedback: {len(feedback_list)}')

# Group by document
feedback_by_doc = {}
for fb in feedback_list:
    doc_id = fb['document_id']
    if doc_id not in feedback_by_doc:
        feedback_by_doc[doc_id] = []
    feedback_by_doc[doc_id].append(fb)

print(f'   Documents with feedback: {len(feedback_by_doc)}')

# Process first 5 documents to see what happens
print(f'\n🔍 PROCESSING FIRST 5 DOCUMENTS:')

total_fields_processed = 0
total_features_created = 0

for idx, (doc_id, doc_feedbacks) in enumerate(list(feedback_by_doc.items())[:5], 1):
    print(f'\n📄 Document {idx} (ID: {doc_id}):')
    print(f'   Feedback count: {len(doc_feedbacks)}')
    
    # Get document
    document = doc_repo.find_by_id(doc_id)
    if not document:
        print(f'   ❌ Document not found!')
        continue
    
    # Get extraction result
    try:
        extraction_result = json.loads(document.extraction_result)
        extracted_data = extraction_result.get('extracted_data', {})
        confidence_scores = extraction_result.get('confidence_scores', {})
        
        print(f'   Extracted fields: {len(extracted_data)}')
        
        # Simulate complete_feedbacks creation
        complete_feedbacks = []
        corrected_fields = set(fb['field_name'] for fb in doc_feedbacks)
        
        # Add corrected fields
        for fb in doc_feedbacks:
            complete_feedbacks.append(fb)
        
        # Add non-corrected fields with confidence >= 0.3
        for field_name, value in extracted_data.items():
            if field_name not in corrected_fields:
                confidence = confidence_scores.get(field_name, 0.0)
                if confidence >= 0.3:
                    complete_feedbacks.append({
                        'field_name': field_name,
                        'corrected_value': value
                    })
                    print(f'      + Added {field_name} (conf={confidence:.2f})')
        
        print(f'   Complete feedbacks: {len(complete_feedbacks)} fields')
        total_fields_processed += len(complete_feedbacks)
        
        # Try to create features
        try:
            with pdfplumber.open(document.file_path) as pdf:
                words = []
                for page in pdf.pages:
                    words.extend(page.extract_words(x_tolerance=3, y_tolerance=3))
            
            learner = AdaptiveLearner()
            target_fields = [fb['field_name'] for fb in complete_feedbacks]
            features, labels = learner._create_bio_sequence_multi(
                complete_feedbacks,
                words,
                template_config=None,
                target_fields=target_fields
            )
            
            if features and labels:
                print(f'   ✅ Features created: {len(labels)} labels')
                total_features_created += len(labels)
            else:
                print(f'   ❌ Failed to create features')
        except Exception as e:
            print(f'   ❌ Error creating features: {e}')
    
    except Exception as e:
        print(f'   ❌ Error: {e}')

print(f'\n' + '=' * 80)
print(f'📊 SUMMARY (first 5 docs):')
print(f'=' * 80)

print(f'\n   Total fields processed: {total_fields_processed}')
print(f'   Total features created: {total_features_created}')
print(f'   Average fields/doc: {total_fields_processed/5:.1f}')
print(f'   Average features/doc: {total_features_created/5:.1f}')

print(f'\n   Extrapolation to all {len(feedback_by_doc)} docs:')
print(f'   Expected fields: {(total_fields_processed/5) * len(feedback_by_doc):.0f}')
print(f'   Expected features: {(total_features_created/5) * len(feedback_by_doc):.0f}')

print(f'\n   Actual training samples: 272')
print(f'   Discrepancy: {(total_features_created/5) * len(feedback_by_doc) - 272:.0f}')

if total_features_created < 50:
    print(f'\n❌ PROBLEM: Features not being created properly!')
    print(f'   Possible causes:')
    print(f'   1. _create_bio_sequence_multi() failing')
    print(f'   2. Words extraction failing')
    print(f'   3. Template config missing')
elif (total_features_created/5) * len(feedback_by_doc) < 1000:
    print(f'\n❌ PROBLEM: Not enough fields being included!')
    print(f'   Confidence threshold may still be too high')
    print(f'   Or extracted_data missing fields')
else:
    print(f'\n⚠️  PROBLEM: Training process not using all data')
    print(f'   Data preparation looks OK')
    print(f'   But training only uses 272 samples')
    print(f'   Check train/test split or data filtering')
