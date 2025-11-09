# 🎓 Apakah Pattern & Context Diperlukan untuk Training CRF?

## ❓ **Pertanyaan Kritis:**

Apakah model CRF **HARUS** menggunakan pattern (regex) dan context (locations) dari template untuk training?

---

## ✅ **JAWABAN: YA, SANGAT DIPERLUKAN!**

### **Alasan 1: Feature Mismatch = Model Confusion**

**Current Implementation:**

```python
# TRAINING (learner.py line 80):
word_features = self._extract_word_features(word, words, i)
# ❌ NO field_config
# ❌ NO context
# Result: Features = {word, position, orthographic, ...}

# EXTRACTION (strategies.py line 723):
features = self._extract_features(all_words, field_name, field_config, context)
# ✅ HAS field_config
# ✅ HAS context
# Result: Features = {word, position, orthographic, has_label, distance_from_label, ...}
```

**Problem:**

```
Training features:
  - word: "Bekasi"
  - x0_norm: 0.261
  - y0_norm: 0.332
  - has_label: False  ← Default!
  - distance_from_label_x: 0  ← Default!
  - near_label: False  ← Default!

Extraction features:
  - word: "Bekasi"
  - x0_norm: 0.261
  - y0_norm: 0.332
  - has_label: True  ← From template!
  - distance_from_label_x: 0.15  ← From template!
  - near_label: True  ← From template!

Model sees DIFFERENT features!
Model trained on: {has_label: False, distance: 0}
Model predicts on: {has_label: True, distance: 0.15}

Result: Model CONFUSED! ❌
```

---

### **Alasan 2: Context Features are HIGH IMPACT**

**Dari kode (learner.py lines 297-345):**

```python
# Context features (ALREADY IMPLEMENTED but NOT USED!)
if context:
    label = context.get('label', '')
    label_pos = context.get('label_position', {})
    
    features.update({
        'has_label': bool(label),  # ← HIGH IMPACT!
        'label_text': label.lower(),  # ← HIGH IMPACT!
        'distance_from_label_x': distance_x / 100,  # ← HIGH IMPACT!
        'distance_from_label_y': distance_y / 100,  # ← HIGH IMPACT!
        'after_label': distance_x > 0,  # ← HIGH IMPACT!
        'same_line_as_label': distance_y < 10,  # ← HIGH IMPACT!
        'near_label': distance_x < 50 and distance_y < 10,  # ← HIGH IMPACT!
    })
```

**Why HIGH IMPACT?**

Contoh: Field "issue_place" dengan label "di"

```
Without context features:
  Model sees: "Bekasi" at position (261, 332)
  Model thinks: Could be ANY field (name? location? event?)
  Accuracy: LOW

With context features:
  Model sees: "Bekasi" at position (261, 332)
             + has_label: True
             + label_text: "di"
             + distance_from_label_x: 0.15 (15 pixels after "di")
             + near_label: True
  Model thinks: This is LOCATION (after "di" label)!
  Accuracy: HIGH
```

**Context features provide SEMANTIC MEANING!**

---

### **Alasan 3: Pattern Features (Regex) - TIDAK Diperlukan**

**Pattern (regex) dari template:**
```json
{
  "field_name": "issue_date",
  "pattern": "\\d{1,2}\\s+\\w+\\s+\\d{4}"
}
```

**Apakah ini diperlukan untuk CRF?**

**❌ TIDAK!** Pattern regex **TIDAK** perlu dikirim ke CRF karena:

1. **CRF sudah punya pattern features:**
   ```python
   'is_year': text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2100,
   'is_day_number': text.isdigit() and len(text) <= 2 and (1 <= int(text) <= 31),
   'looks_like_date_pattern': bool(re.match(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}', text)),
   ```

2. **Pattern regex adalah untuk rule-based extraction:**
   - Rule-based: Match pattern → extract
   - CRF: Learn from features → predict label

3. **CRF learns patterns from data:**
   - Training data: "09 October 2024" → ISSUE_DATE
   - Model learns: {is_day_number, is_capitalized_word, is_year} → ISSUE_DATE
   - No need for explicit regex!

**Kesimpulan:** Pattern regex **TIDAK** perlu untuk CRF training.

---

### **Alasan 4: Context Locations - SANGAT DIPERLUKAN**

**Context locations dari template:**
```json
{
  "locations": [{
    "page": 0,
    "x0": 273.525744,
    "y0": 332.69088,
    "x1": 350.049504,
    "y1": 343.73088,
    "context": {
      "label": "di",
      "label_position": {
        "x0": 261.94368,
        "y0": 332.69088,
        "x1": 271.114608,
        "y1": 343.73088
      }
    }
  }]
}
```

**Apakah ini diperlukan untuk CRF?**

**✅ YA, SANGAT!** Context locations memberikan:

1. **Spatial relationships:**
   - Distance from label
   - Same line as label
   - Near label

2. **Semantic context:**
   - Label text (e.g., "di" → location)
   - Words before/after label

3. **Disambiguation:**
   - "Bekasi" near "di" → ISSUE_PLACE
   - "Bekasi" near "Nama:" → NOT ISSUE_PLACE

**Without context locations:**
```
Model sees: "Bekasi"
Model confused: Name? Location? Event?
Accuracy: 25%
```

**With context locations:**
```
Model sees: "Bekasi" + near "di" label
Model knows: ISSUE_PLACE!
Accuracy: 80%
```

---

## 📊 **Current vs Correct Implementation**

### **Current (WRONG):**

```python
# services.py line 128
features, labels = learner._create_bio_sequence_multi(complete_feedbacks, words)
#                                                      ^^^ NO template_config!
#                                                      ^^^ NO context!

# learner.py line 80
word_features = self._extract_word_features(word, words, i)
#                                           ^^^ NO field_config!
#                                           ^^^ NO context!
```

**Result:**
- Training features: {word, position, orthographic}
- Extraction features: {word, position, orthographic, **context**}
- **MISMATCH!** Model confused!
- Accuracy: 25%

---

### **Correct (SHOULD BE):**

```python
# services.py - NEED TO MODIFY
# Get template config
template = self.db.get_template(document['template_id'])
config = json.loads(template['config'])

# Pass template config to learner
features, labels = learner._create_bio_sequence_multi(
    complete_feedbacks, 
    words,
    template_config=config  # ✅ ADD THIS!
)

# learner.py - NEED TO MODIFY
def _create_bio_sequence_multi(
    self, 
    feedbacks: List[Dict[str, Any]], 
    words: List[Dict],
    template_config: Dict = None  # ✅ ADD THIS!
) -> Tuple[List[Dict], List[str]]:
    
    # Extract features with context for each field
    for i, word in enumerate(words):
        # Get context for this word based on template
        context = self._get_context_for_word(word, template_config)
        
        word_features = self._extract_word_features(
            word, words, i,
            template_config=template_config,  # ✅ ADD THIS!
            context=context  # ✅ ADD THIS!
        )
        features.append(word_features)
```

**Result:**
- Training features: {word, position, orthographic, **context**}
- Extraction features: {word, position, orthographic, **context**}
- **MATCH!** Model consistent!
- Expected accuracy: 70-80%

---

## 🎯 **Summary**

### **Q: Apakah pattern (regex) diperlukan untuk CRF training?**
**A: ❌ TIDAK.** CRF sudah punya pattern features (is_year, is_day_number, dll). Pattern regex hanya untuk rule-based extraction.

### **Q: Apakah context (locations) diperlukan untuk CRF training?**
**A: ✅ YA, SANGAT!** Context locations memberikan:
- Spatial relationships (distance from label)
- Semantic context (label text)
- Disambiguation (same word, different context)

### **Q: Mengapa accuracy rendah (25%)?**
**A:** Feature mismatch!
- Training: NO context features
- Extraction: WITH context features
- Model sees different features → confused → low accuracy

### **Q: Apa yang harus diperbaiki?**
**A:** Pass `template_config` dan `context` ke training:
1. Modify `services.py` → pass template_config
2. Modify `learner._create_bio_sequence_multi` → accept template_config
3. Extract context for each word from template
4. Pass context to `_extract_word_features`

### **Expected Impact:**
```
Before: Training WITHOUT context
        Extraction WITH context
        Accuracy: 25%

After:  Training WITH context
        Extraction WITH context
        Accuracy: 70-80% (+200-300%!)
```

---

## 📝 **Technical Details**

### **Context Features yang Diperlukan:**

```python
# From template locations
'has_label': bool,              # Does this field have a label?
'label_text': str,              # What is the label text?
'distance_from_label_x': float, # Horizontal distance from label
'distance_from_label_y': float, # Vertical distance from label
'after_label': bool,            # Is word after label?
'same_line_as_label': bool,     # Is word on same line as label?
'near_label': bool,             # Is word near label?
'in_context_before': bool,      # Is word in context before?
'in_context_after': bool,       # Is word in context after?
```

### **How to Get Context for Training:**

```python
def _get_context_for_word(self, word: Dict, template_config: Dict) -> Dict:
    """
    Get context for a word based on template config
    """
    if not template_config:
        return {}
    
    fields = template_config.get('fields', {})
    
    # Find which field this word might belong to based on position
    for field_name, field_config in fields.items():
        locations = field_config.get('locations', [])
        
        for location in locations:
            # Check if word is near this location
            if self._is_word_near_location(word, location):
                return location.get('context', {})
    
    return {}

def _is_word_near_location(self, word: Dict, location: Dict, threshold: float = 100) -> bool:
    """
    Check if word is near a template location
    """
    word_x = word.get('x0', 0)
    word_y = word.get('top', 0)
    
    loc_x = location.get('x0', 0)
    loc_y = location.get('y0', 0)
    
    distance = ((word_x - loc_x)**2 + (word_y - loc_y)**2)**0.5
    
    return distance < threshold
```

---

**Date:** 2025-11-08  
**Status:** ⚠️ CRITICAL - Context features NOT used in training  
**Priority:** 🔥 HIGH - Must fix for accuracy improvement  
**Expected Impact:** +200-300% accuracy improvement
