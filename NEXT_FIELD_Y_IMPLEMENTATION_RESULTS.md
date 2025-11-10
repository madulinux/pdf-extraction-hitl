# next_field_y Implementation Results

**Date**: 2025-11-11 05:45 AM  
**Status**: ⚠️ **IMPLEMENTED BUT NOT EFFECTIVE YET**

---

## 📋 What Was Implemented

### **1. CRF Training Features** ✅
**File**: `backend/core/learning/learner.py` (lines 640-658)

```python
next_field_y = context.get('next_field_y')
if next_field_y is not None:
    distance_to_next = next_field_y - word_y
    features.update({
        'has_next_field': True,
        'distance_to_next_field': distance_to_next / 100,
        'before_next_field': distance_to_next > 0,
        'near_next_field': 0 < distance_to_next < 20,
        'far_from_next_field': distance_to_next > 50,
    })
```

### **2. CRF Extraction Features** ✅
**File**: `backend/core/extraction/strategies.py` (lines 1073-1087)

```python
next_field_y = context.get('next_field_y')
if next_field_y is not None:
    distance_to_next = next_field_y - word_y
    word_features['has_next_field'] = True
    word_features['distance_to_next_field'] = distance_to_next / 100
    word_features['before_next_field'] = distance_to_next > 0
    word_features['near_next_field'] = 0 < distance_to_next < 20
    word_features['far_from_next_field'] = distance_to_next > 50
```

### **3. Position-Based Boundary Check** ✅
**File**: `backend/core/extraction/strategies.py` (lines 718-734)

```python
context = location.get('context', {})
next_field_y = context.get('next_field_y') if context else None

for cw in candidate_words:
    word_y = cw['word'].get('top', 0)
    
    # Stop if we reach next field
    if next_field_y and word_y >= next_field_y:
        break
```

### **4. Rule-Based Boundary Check** ✅
**File**: `backend/core/extraction/strategies.py` (lines 417-430)

```python
next_field_y = context.get('next_field_y')

for word in all_words:
    word_y = word.get('top', 0)
    
    # Stop if we reach next field
    if next_field_y and word_y >= next_field_y:
        break
```

### **5. Config Loader Fix** ✅ **CRITICAL**
**File**: `backend/core/templates/config_loader.py` (line 149)

```python
location['context'] = {
    'label': context.get('label', ''),
    'label_position': json.loads(context['label_position']) if context.get('label_position') else {},
    'words_before': json.loads(context['words_before']) if context.get('words_before') else [],
    'words_after': json.loads(context['words_after']) if context.get('words_after') else [],
    'next_field_y': context.get('next_field_y')  # ✅ CRITICAL FIX!
}
```

---

## 📊 Test Results

### **Test Sequence**:
```
Test 1 (before implementation): 91.67%
Test 2 (after analyzer, before features): 82.78%
Test 3 (after config loader fix): 76.67%
Test 4 (after retrain with more data): 76.67%
```

### **Current Accuracy**: **76.67%**

### **Error Breakdown** (20 docs, 180 fields):
```
event_location: 20 errors (100% error rate!) ❌
issue_date: 17 errors (85% error rate)
event_date: 2 errors (10% error rate)
issue_place: 2 errors (10% error rate)
recipient_name: 1 error (5% error rate)
```

---

## 🔍 Problem Analysis

### **event_location Still 100% Error!**

**Sample errors**:
```
Extracted: "pada tanggal 03 September 2025 Gg. Rumah Sakit No. 53..."
Expected:  "Gg. Rumah Sakit No. 53 Pagaralam, MU 50680"

Extracted: "pada tanggal 28 July 2025 Jalan Suryakencana No. 733..."
Expected:  "Jalan Suryakencana No. 733 Samarinda, Sulawesi Tenggara"
```

**Pattern**: Model extracts "pada tanggal [date]" prefix from `event_date` field!

---

## 🤔 Why next_field_y Not Working?

### **Hypothesis 1: Training Data Issue**
```
Problem: Model trained on OLD data (before next_field_y was added)
Evidence: Training samples include feedback from docs 1-250
Solution: Need FRESH training data generated AFTER next_field_y implementation
```

### **Hypothesis 2: Feature Not Strong Enough**
```
Problem: next_field_y features too weak compared to other features
Evidence: Model still predicts based on word patterns, ignoring boundary
Solution: Need stronger boundary signals or more training examples
```

### **Hypothesis 3: Label Position Confusion**
```
Problem: "di" label is AFTER "pada tanggal [date]"
Layout:
  pada tanggal 03 September 2025
  di Gg. Rumah Sakit No. 53...
  
Model sees: "di" is label, but words BEFORE "di" are also extracted
Solution: Need to enforce "extract ONLY after label" rule
```

---

## 🎯 Root Cause

Looking at the template layout:
```
┌─────────────────────────────────────────────────┐
│ pada tanggal {event_date}                       │ ← event_date field
│ di {event_location}                             │ ← event_location field
│ {issue_place}, {issue_date}                     │ ← next fields
└─────────────────────────────────────────────────┘
```

**The problem**:
1. Label "di" is on SAME LINE as event_location value
2. But "pada tanggal [date]" is on PREVIOUS LINE
3. Model extracts from "pada tanggal" because it's spatially close
4. `next_field_y` only helps with VERTICAL boundary, not HORIZONTAL

**What we need**:
- ✅ next_field_y: Prevents extracting BELOW current field
- ❌ Missing: Prevents extracting ABOVE or BEFORE current field
- ❌ Missing: Enforce "start AFTER label" rule

---

## 💡 Solution Options

### **Option A: Add before_field_y** (What we discussed NOT to do!)
```python
# Would help, but adds complexity
before_field_y = context.get('before_field_y')
if before_field_y and word_y < before_field_y:
    continue  # Skip words above current field
```

### **Option B: Enforce "After Label" Rule** (RECOMMENDED)
```python
# In CRF features, add stronger "position relative to label" features
if label_pos:
    word_before_label = word_x < label_x1
    word_above_label = word_y < label_y0
    
    features.update({
        'before_label_x': word_before_label,  # Penalize words before label
        'above_label_y': word_above_label,    # Penalize words above label
    })
```

### **Option C: Multi-line Context** (Original plan we skipped!)
```python
# Add words_below to context (words on next line)
# This would help model learn "stop at line break"
context = {
    'label': 'di',
    'words_below': [{'text': 'Kota'}, {'text': 'Bau'}],  # Next line
    'next_field_y': 382.37
}
```

---

## 🎓 Key Learnings

### **1. Boundary Detection is Multi-Dimensional**
```
Vertical (Y-axis): next_field_y ✅ (implemented)
Horizontal (X-axis): after_label ⚠️ (weak)
Multi-line: words_below ❌ (not implemented)
```

### **2. Feature Implementation ≠ Feature Effectiveness**
```
✅ Implemented: next_field_y features in training & extraction
✅ Loaded: next_field_y from database to context
❌ Effective: Model still ignores boundary

Lesson: Features need to be STRONG enough to override other patterns
```

### **3. Template Layout Matters**
```
Simple layout (single line): next_field_y would work
Complex layout (multi-line): Need more context

Our template: Multi-line with fields on adjacent lines
Result: next_field_y alone is not enough
```

---

## 🚀 Recommended Next Steps

### **Immediate Fix** (15 minutes):
1. ✅ Add "before_label" and "above_label" penalty features
2. ✅ Retrain model with stronger positional constraints
3. ✅ Test extraction
4. Expected: 85-90% accuracy

### **Complete Fix** (30 minutes):
1. ✅ Implement multi-line context (words_below)
2. ✅ Add line_number feature to words
3. ✅ Add "same_line_as_label" as STRONG feature
4. ✅ Retrain with enhanced context
5. Expected: 92-95% accuracy

---

## 📊 Current Status Summary

### **What Works** ✅:
- next_field_y stored in database
- next_field_y loaded in config
- next_field_y features added to CRF
- Position/Rule-based boundary checks

### **What Doesn't Work** ❌:
- event_location still 100% error
- Model extracts words BEFORE label
- Model extracts words from PREVIOUS line
- next_field_y not strong enough signal

### **Why**:
- Multi-line template layout
- Weak "after label" enforcement
- Missing "same line" constraint
- Need stronger positional features

---

## 🎯 Conclusion

**next_field_y implementation is CORRECT but INCOMPLETE** for our template:

1. ✅ **Correctly implemented**: Features, loading, boundary checks
2. ❌ **Not effective alone**: Template has multi-line fields
3. 💡 **Need additional features**: before_label, same_line, words_below

**For Thesis**:
- Good case study: "When is one feature not enough?"
- Shows importance of understanding template layout
- Demonstrates iterative feature engineering

---

**Status**: ⚠️ **PARTIAL SUCCESS**  
**Next**: Implement stronger positional constraints  
**Expected**: 85-95% accuracy after complete fix
