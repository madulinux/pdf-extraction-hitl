"""
Diagnose why training only used 256 samples instead of expected 771+
"""
from database.db_manager import DatabaseManager
from database.repositories.feedback_repository import FeedbackRepository
from database.repositories.document_repository import DocumentRepository
import json

db = DatabaseManager()
feedback_repo = FeedbackRepository(db)
doc_repo = DocumentRepository(db)

print('🔍 DIAGNOSIS: Why Only 256 Training Samples?')
print('=' * 80)

# 1. Check feedback
feedback_all = feedback_repo.find_for_training(template_id=1, unused_only=False)
feedback_unused = feedback_repo.find_for_training(template_id=1, unused_only=True)

print(f'\n📊 FEEDBACK DATA:')
print(f'   All feedback: {len(feedback_all)} records')
print(f'   Unused only: {len(feedback_unused)} records')

# Group by document
docs_all = {}
for fb in feedback_all:
    doc_id = fb['document_id']
    if doc_id not in docs_all:
        docs_all[doc_id] = []
    docs_all[doc_id].append(fb)

docs_unused = {}
for fb in feedback_unused:
    doc_id = fb['document_id']
    if doc_id not in docs_unused:
        docs_unused[doc_id] = []
    docs_unused[doc_id].append(fb)

print(f'\n📊 DOCUMENTS WITH FEEDBACK:')
print(f'   All feedback: {len(docs_all)} documents')
print(f'   Unused only: {len(docs_unused)} documents')

# 2. Check validated documents
validated_docs = doc_repo.find_validated_documents(template_id=1)
print(f'\n📊 VALIDATED DOCUMENTS:')
print(f'   Total validated: {len(validated_docs)}')

# 3. Simulate training data preparation
print(f'\n🔍 SIMULATING TRAINING DATA PREPARATION:')
print(f'   (This is what happens in retrain_model)')

# Scenario 1: use_all_feedback=True
print(f'\n   Scenario 1: use_all_feedback=TRUE')
print(f'   ├─ Feedback documents: {len(docs_all)}')
print(f'   ├─ Validated documents: {len(validated_docs)}')

# Check which validated docs already have feedback
validated_with_feedback = 0
validated_without_feedback = 0
for doc in validated_docs:
    if doc.id in docs_all:
        validated_with_feedback += 1
    else:
        validated_without_feedback += 1

print(f'   ├─ Validated (already in feedback): {validated_with_feedback}')
print(f'   ├─ Validated (no feedback): {validated_without_feedback}')
print(f'   └─ Expected total: {len(docs_all) + validated_without_feedback} documents')

# Scenario 2: use_all_feedback=False
print(f'\n   Scenario 2: use_all_feedback=FALSE')
print(f'   ├─ Feedback documents: {len(docs_unused)}')
print(f'   ├─ Validated documents: {len(validated_docs)}')
print(f'   └─ Expected total: {len(docs_unused) + validated_without_feedback} documents')

# 4. Check actual training samples
print(f'\n🔍 ACTUAL TRAINING (256 samples):')

# If 256 samples came from documents, how many docs?
# Assuming ~9 fields per doc on average
estimated_docs = 256 / 9
print(f'   256 samples ÷ 9 fields/doc ≈ {estimated_docs:.0f} documents')

# Check if this matches unused only
if abs(len(docs_unused) - estimated_docs) < 5:
    print(f'   ✅ MATCHES unused feedback ({len(docs_unused)} docs)')
    print(f'   → Training used use_all_feedback=FALSE!')
elif abs(len(docs_all) - estimated_docs) < 5:
    print(f'   ✅ MATCHES all feedback ({len(docs_all)} docs)')
    print(f'   → But validated docs not included')
else:
    print(f'   ⚠️  Does not match expected counts')

print(f'\n' + '=' * 80)
print(f'🎯 ROOT CAUSE:')
print(f'=' * 80)

if abs(len(docs_unused) - estimated_docs) < 5:
    print(f'\n❌ PROBLEM: Training used use_all_feedback=FALSE')
    print(f'   Expected: use_all_feedback=TRUE ({len(docs_all)} docs)')
    print(f'   Actual: use_all_feedback=FALSE ({len(docs_unused)} docs)')
    print(f'   Missing: {len(docs_all) - len(docs_unused)} documents')
    print()
    print(f'   WHY:')
    print(f'   - Frontend may have sent wrong parameter')
    print(f'   - Or auto-training was triggered instead of manual')
    print(f'   - Or default parameter used')
    print()
    print(f'   SOLUTION:')
    print(f'   - Verify frontend sends use_all_feedback=true')
    print(f'   - Verify is_incremental=false')
    print(f'   - Check ModelTraining.tsx handleRetrain()')
else:
    print(f'\n⚠️  PROBLEM: Validated documents not included')
    print(f'   Expected: {len(docs_all)} + {validated_without_feedback} = {len(docs_all) + validated_without_feedback} docs')
    print(f'   Actual: ~{estimated_docs:.0f} docs')
    print(f'   Missing: ~{len(docs_all) + validated_without_feedback - estimated_docs:.0f} docs')
    print()
    print(f'   WHY:')
    print(f'   - Validated document processing may be skipped')
    print(f'   - Or confidence threshold too high')
    print(f'   - Check services.py line 100-107')

print(f'\n' + '=' * 80)
print(f'✅ NEXT STEPS:')
print(f'=' * 80)

print(f'\n1. Check frontend parameters:')
print(f'   File: frontend/components/ModelTraining.tsx')
print(f'   Look for: learningAPI.train()')
print(f'   Verify: use_all_feedback=true, is_incremental=false')

print(f'\n2. Test manual training with correct params:')
print(f'   Expected samples: {len(docs_all)} docs × 9 fields ≈ {len(docs_all) * 9} samples')
print(f'   Current samples: 256')
print(f'   Should increase to: ~{len(docs_all) * 9}')

print(f'\n3. If still wrong, check backend:')
print(f'   File: backend/core/learning/services.py')
print(f'   Method: _prepare_training_data()')
print(f'   Verify: use_all_feedback parameter is respected')
