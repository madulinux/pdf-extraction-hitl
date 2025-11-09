# 🔧 Strategy Selection Critical Fixes

**Date:** 2024-11-09  
**Status:** ⚠️ IN PROGRESS  
**Priority:** 🔴 CRITICAL

---

## 🐛 **BUGS IDENTIFIED:**

### **Bug #1: Missing `all_strategies_attempted` for Single Strategy**

**Problem:**
```json
{
  "field_name": "nama",
  "method": "rule_based",
  "confidence": 0.82
  // ❌ NO all_strategies_attempted!
}
```

**Root Cause:**
```python
# Line 495-497 in hybrid_strategy.py
if len(valid_results) == 1:
    return valid_results[0][1]  # ❌ Returns directly without metadata
```

**Impact:**
- Cannot track which strategies were attempted
- Cannot update performance for non-selected strategies
- Breaks adaptive learning loop

**Fix Required:**
```python
if len(valid_results) == 1:
    strategy_type, field_value = valid_results[0]
    
    # ✅ ADD: all_strategies_attempted metadata
    field_value.metadata['all_strategies_attempted'] = {
        st.value: {
            'success': fv is not None,
            'confidence': fv.confidence if fv else 0.0,
            'value': fv.value if fv else None
        }
        for st, fv in strategy_results.items()
    }
    field_value.metadata['selected_by'] = 'single_valid_strategy'
    
    return field_value
```

---

### **Bug #2: CRF Returns None Without Detailed Logging**

**Problem:**
```
Field: kerja_alasan
- Training data: 108 corrections (all wrong, multi-line text)
- Model labels: ['B-KERJA_ALASAN', 'I-KERJA_ALASAN'] ✅
- CRF result: None ❌
- Log: "⚠️ CRF: No tokens found" (not helpful!)
```

**Root Cause:**
```python
# Line 773 in strategies.py
if not extracted_tokens:
    self.logger.debug(f"⚠️ CRF: No tokens found for '{field_name}'")
    return None  # ❌ No details WHY!
```

**Possible Causes:**
1. Model predicts wrong labels (e.g., `I-KERJA_ALASAN` without `B-KERJA_ALASAN`)
2. Confidence too low (filtered out)
3. Multi-line text not properly tokenized
4. Field-aware features not working

**Fix Required:**
```python
if not extracted_tokens:
    # ✅ DETAILED LOGGING
    print(f"⚠️ [CRF] No tokens found for '{field_name}'")
    print(f"   Looking for: {target_label}, {inside_label}")
    print(f"   Total predictions: {len(predictions)}")
    print(f"   Unique labels predicted: {set(predictions)}")
    
    # Count related predictions
    target_count = sum(1 for p in predictions if field_name.upper() in p)
    if target_count > 0:
        print(f"   ⚠️ Model predicted {target_count} tokens with '{field_name.upper()}' but none matched B-/I- pattern!")
        print(f"   Predictions sample: {[p for p in predictions if field_name.upper() in p][:10]}")
    else:
        print(f"   ℹ️ Model did not predict any tokens for this field")
    
    return None
```

---

### **Bug #3: Inconsistent Strategy Calling**

**Problem:**
Some fields show:
```json
{
  "all_strategies_attempted": {
    "crf": {...},
    "rule_based": {...}
  }
}
```

Others show:
```json
{
  // ❌ Only rule_based, no CRF attempt recorded
}
```

**Expected Behavior:**
- **ALL strategies should ALWAYS be attempted** (if available)
- **ALL attempts should be recorded** (even if None)
- **Performance tracking requires ALL attempts**

**Verification Needed:**
```python
# Check if CRF is always called
def _extract_field_with_strategies(...):
    results = {}
    
    # Always try rule-based ✅
    results[StrategyType.RULE_BASED] = ...
    
    # Always try CRF if available ✅
    if self.crf_strategy:
        results[StrategyType.CRF] = ...  # Even if None!
    
    return results  # Should contain ALL strategies
```

---

## 🔍 **INVESTIGATION STEPS:**

### **Step 1: Verify CRF is Always Called**

```bash
# Check extraction logs
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/backend
python3 -c "
from core.extraction.services import ExtractionService
from core.database.manager import DatabaseManager

db = DatabaseManager('data/app.db')
service = ExtractionService(db)

# Extract a document and check logs
result = service.extract_document('path/to/pdf', template_id=1)
print(result['metadata']['strategies_used'])
"
```

### **Step 2: Debug CRF Predictions for `kerja_alasan`**

```python
# tools/debug_crf_predictions.py
import joblib
import pdfplumber
from core.learning.learner import AdaptiveLearner

# Load model
model = joblib.load('models/template_1_model.joblib')

# Extract words from a test document
with pdfplumber.open('path/to/test.pdf') as pdf:
    words = []
    for page in pdf.pages:
        words.extend(page.extract_words())

# Extract features
learner = AdaptiveLearner()
features = learner._extract_word_features(
    words[0], words, 0,
    context={},
    target_field='kerja_alasan'  # ✅ Field-aware!
)

# Add field-aware feature to ALL words
for i, word in enumerate(words):
    word_features = learner._extract_word_features(word, words, i)
    word_features['target_field_kerja_alasan'] = True

# Predict
predictions = model.predict([word_features for word in words])[0]

# Analyze predictions
print(f"Total words: {len(words)}")
print(f"Predictions: {set(predictions)}")
print(f"KERJA_ALASAN predictions: {[p for p in predictions if 'KERJA_ALASAN' in p]}")

# Check for pattern issues
b_count = sum(1 for p in predictions if p == 'B-KERJA_ALASAN')
i_count = sum(1 for p in predictions if p == 'I-KERJA_ALASAN')
print(f"B-KERJA_ALASAN: {b_count}, I-KERJA_ALASAN: {i_count}")

if i_count > 0 and b_count == 0:
    print("⚠️ PROBLEM: Model predicts I- without B-!")
    print("   This violates BIO tagging rules!")
```

### **Step 3: Check Training Data Quality**

```sql
-- Check kerja_alasan feedback
SELECT 
    COUNT(*) as total,
    AVG(LENGTH(corrected_value)) as avg_length,
    MAX(LENGTH(corrected_value)) as max_length,
    SUM(CASE WHEN corrected_value LIKE '%\n%' THEN 1 ELSE 0 END) as multi_line_count
FROM feedback
WHERE field_name = 'kerja_alasan';

-- Sample values
SELECT corrected_value 
FROM feedback 
WHERE field_name = 'kerja_alasan' 
LIMIT 5;
```

---

## ✅ **FIXES TO APPLY:**

### **Fix #1: Add all_strategies_attempted for Single Strategy**

**File:** `core/extraction/hybrid_strategy.py`  
**Line:** 495-497

```python
if len(valid_results) == 1:
    strategy_type, field_value = valid_results[0]
    self.logger.info(f"  ✅ Only one valid strategy: {strategy_type.value}")
    
    # ✅ FIX: Add all_strategies_attempted even for single strategy
    field_value.metadata['all_strategies_attempted'] = {
        st.value: {
            'success': fv is not None,
            'confidence': fv.confidence if fv else 0.0,
            'value': fv.value if fv else None
        }
        for st, fv in strategy_results.items()
    }
    field_value.metadata['selected_by'] = 'single_valid_strategy'
    
    return field_value
```

### **Fix #2: Add Detailed CRF Logging**

**File:** `core/extraction/strategies.py`  
**Line:** 772-774

```python
if not extracted_tokens:
    # ✅ DETAILED LOGGING: Why CRF returned None
    print(f"⚠️ [CRF] No tokens found for '{field_name}'")
    print(f"   Looking for: {target_label}, {inside_label}")
    print(f"   Total predictions: {len(predictions)}")
    print(f"   Unique labels predicted: {set(predictions)}")
    
    # Count how many times target field was predicted
    target_count = sum(1 for p in predictions if field_name.upper() in p)
    if target_count > 0:
        print(f"   ⚠️ Model predicted {target_count} tokens with '{field_name.upper()}' but none matched B-/I- pattern!")
        # Show sample predictions
        related_preds = [(i, p) for i, p in enumerate(predictions) if field_name.upper() in p]
        print(f"   Sample: {related_preds[:10]}")
    else:
        print(f"   ℹ️ Model did not predict any tokens for this field")
    
    self.logger.debug(f"⚠️ CRF: No tokens found for '{field_name}' (predicted {target_count} related tokens)")
    return None
```

---

## 🎯 **EXPECTED OUTCOMES:**

After fixes:

1. **All fields will have `all_strategies_attempted`** ✅
2. **CRF failures will have detailed logs** ✅
3. **Can identify root cause of CRF None returns** ✅
4. **Performance tracking will be complete** ✅

---

## 📊 **TESTING PLAN:**

```bash
# 1. Apply fixes
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/backend

# 2. Test with new documents
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/tools/seeder
python batch_seeder.py --template job_application_template --generate --count 3

# 3. Check extraction results
python3 -c "
import sqlite3
conn = sqlite3.connect('../backend/data/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT * FROM documents ORDER BY id DESC LIMIT 1')
doc = cursor.fetchone()
print(f'Document ID: {doc[\"id\"]}')
print(f'Extraction result: {doc[\"extraction_result\"]}')
"

# 4. Verify all_strategies_attempted is present for ALL fields
# 5. Check CRF logs for kerja_alasan
```

---

## 🚨 **CRITICAL NEXT STEPS:**

1. ✅ Apply Fix #1 (all_strategies_attempted)
2. ✅ Apply Fix #2 (CRF logging)
3. 🔄 Test with 5 new documents
4. 🔄 Analyze CRF predictions for kerja_alasan
5. 🔄 If still None, investigate:
   - BIO tagging violations
   - Multi-line tokenization
   - Field-aware features during inference

---

**Status:** Awaiting user confirmation to proceed with fixes.
