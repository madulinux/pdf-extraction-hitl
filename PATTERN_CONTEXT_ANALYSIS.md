# 🔍 ANALYSIS: Pattern & Context dalam Training Model

## ❓ **Pertanyaan:**

1. Apakah model CRF belajar dari `pattern` dan `context.locations` di template config?
2. Jika ya, apakah ada verifikasi pattern/context saat ada feedback?
3. Apakah pattern/context perlu disesuaikan saat ada koreksi?

---

## 📊 **JAWABAN: TIDAK! Model CRF TIDAK Belajar dari Pattern/Context**

### **Current Implementation:**

#### **1. Training Process (`learner.py`)**

```python
# Line 78-81: Extract features for training
for i, word in enumerate(words):
    word_features = self._extract_word_features(word, words, i)
    #                                                          ^^^ NO field_config!
    #                                                          ^^^ NO context!
    features.append(word_features)
```

**❌ Problem:** 
- `field_config` dan `context` **TIDAK dikirim** ke `_extract_word_features` saat training!
- Model CRF **HANYA belajar dari**:
  - Lexical features (word form, case, digits)
  - Orthographic features (capitalization, punctuation)
  - Layout features (x, y position)
  - Context features (surrounding words)
  - Date/boundary features (pattern-based, generic)

**✅ Model TIDAK belajar dari:**
- Template pattern (regex)
- Template context locations
- Label keywords dari template
- Spatial relationships dari template

---

#### **2. Extraction Process (`strategies.py`)**

**Rule-Based Strategy:**
```python
# Line 94: Pattern digunakan untuk rule-based extraction
regex_pattern = field_config.get('pattern', r'.+')

# Line 97-110: Context locations digunakan untuk positioning
locations = get_field_locations(field_config)
for location in locations:
    context = location.get('context', {})
    # Extract based on position and pattern
```

**CRF Strategy:**
```python
# Line 700-750: CRF extraction
# Model predicts BIO labels
# NO pattern validation
# NO context location checking
```

---

### **🔥 MASALAH UTAMA:**

**1. Training vs Extraction Mismatch**

```
Training (learner.py):
  Features: word, position, surrounding words
  NO pattern, NO context from template
  
Extraction (strategies.py):
  Rule-based: Uses pattern + context ✅
  CRF-based: Uses ONLY learned features ❌
  
Result: CRF tidak konsisten dengan template!
```

**2. Feedback Tidak Update Template**

```
User corrects:
  Original: "dalam kegiatan Training"
  Corrected: "Training"
  
What happens:
  ✅ Feedback saved to database
  ✅ Model retrained with corrected value
  ❌ Template pattern NOT updated
  ❌ Template context NOT updated
  
Result: Rule-based masih extract "dalam kegiatan Training"!
```

**3. No Pattern/Context Verification**

Saat feedback:
- ❌ Tidak ada check apakah corrected value match pattern
- ❌ Tidak ada update pattern jika tidak match
- ❌ Tidak ada update context locations
- ❌ Tidak ada learning dari spatial relationships

---

## ✅ **SOLUSI YANG DIPERLUKAN:**

### **Solution 1: Add Pattern/Context Features to Training**

**Modify:** `backend/core/learning/learner.py`

```python
def _create_bio_sequence_multi(self, feedbacks: List[Dict[str, Any]], 
                               words: List[Dict],
                               template_config: Dict = None) -> Tuple[List[Dict], List[str]]:
    """
    Create BIO-tagged sequence with template context
    """
    features = []
    labels = ['O'] * len(words)
    
    # Extract features for all words with template context
    for i, word in enumerate(words):
        # ✅ NEW: Pass template config for each field
        field_configs = {}
        if template_config:
            for field_name, field_config in template_config.get('fields', {}).items():
                field_configs[field_name] = field_config
        
        word_features = self._extract_word_features(
            word, words, i,
            template_config=template_config  # ✅ NEW!
        )
        features.append(word_features)
    
    # ... rest of labeling logic
```

**Modify:** `_extract_word_features` to use template context

```python
def _extract_word_features(
    self, 
    word: Dict, 
    all_words: List[Dict], 
    index: int,
    template_config: Dict = None  # ✅ NEW!
) -> Dict[str, Any]:
    """
    Extract features with template context
    """
    features = {
        # ... existing features ...
    }
    
    # ✅ NEW: Add template-based features
    if template_config:
        fields = template_config.get('fields', {})
        
        for field_name, field_config in fields.items():
            # Add pattern matching features
            pattern = field_config.get('pattern', '')
            if pattern:
                import re
                features[f'matches_pattern_{field_name}'] = bool(re.match(pattern, word['text']))
            
            # Add context location features
            locations = field_config.get('locations', [])
            for loc in locations:
                context = loc.get('context', {})
                label = context.get('label', '')
                
                if label:
                    # Distance from label
                    label_pos = context.get('label_position', {})
                    if label_pos:
                        distance = abs(word['x0'] - label_pos.get('x0', 0))
                        features[f'distance_from_{field_name}_label'] = distance / 1000
    
    return features
```

---

### **Solution 2: Template Pattern/Context Adaptation**

**Create:** `backend/core/templates/adapter.py`

```python
class TemplateAdapter:
    """
    Adapts template patterns and contexts based on feedback
    """
    
    def adapt_from_feedback(
        self,
        template_id: int,
        field_name: str,
        original_value: str,
        corrected_value: str,
        extraction_context: Dict
    ):
        """
        Update template pattern/context based on feedback
        
        Args:
            template_id: Template ID
            field_name: Field that was corrected
            original_value: Original extracted value
            corrected_value: User's corrected value
            extraction_context: Context where value was found (x, y, etc.)
        """
        # Load template config
        template = self.db.get_template(template_id)
        config = self._load_config(template['config_path'])
        
        field_config = config['fields'].get(field_name, {})
        
        # 1. Update pattern if needed
        current_pattern = field_config.get('pattern', r'.+')
        if not re.match(current_pattern, corrected_value):
            # Pattern doesn't match corrected value
            # Learn new pattern from corrected value
            new_pattern = self._infer_pattern(corrected_value)
            field_config['pattern'] = new_pattern
            print(f"✅ Updated pattern for {field_name}: {new_pattern}")
        
        # 2. Update context if needed
        locations = field_config.get('locations', [])
        if extraction_context:
            # Check if extraction context matches any location
            matched = False
            for loc in locations:
                if self._is_similar_location(loc, extraction_context):
                    matched = True
                    break
            
            if not matched:
                # Add new location context
                locations.append({
                    'page': extraction_context.get('page', 0),
                    'x0': extraction_context['x0'],
                    'y0': extraction_context['y0'],
                    'x1': extraction_context['x1'],
                    'y1': extraction_context['y1'],
                    'context': extraction_context.get('context', {})
                })
                print(f"✅ Added new location for {field_name}")
        
        # 3. Save updated config
        config['fields'][field_name] = field_config
        self._save_config(template['config_path'], config)
    
    def _infer_pattern(self, value: str) -> str:
        """
        Infer regex pattern from value
        """
        import re
        
        # Date patterns
        if re.match(r'\d{1,2}\s+\w+\s+\d{4}', value):
            return r'\d{1,2}\s+\w+\s+\d{4}'
        
        # Number patterns
        if re.match(r'\d+/\w+/\d+/\d+', value):
            return r'\d+/\w+/\d+/\d+'
        
        # Name patterns (capitalized words)
        if all(word[0].isupper() for word in value.split() if word):
            return r'[A-Z][a-z]+(\s+[A-Z][a-z]+)*'
        
        # Default: any text
        return r'.+'
    
    def _is_similar_location(self, loc1: Dict, loc2: Dict, threshold: float = 20) -> bool:
        """
        Check if two locations are similar (within threshold pixels)
        """
        if loc1.get('page') != loc2.get('page'):
            return False
        
        distance = (
            (loc1['x0'] - loc2['x0'])**2 +
            (loc1['y0'] - loc2['y0'])**2
        )**0.5
        
        return distance < threshold
```

---

### **Solution 3: Integrate Adapter with Feedback Pipeline**

**Modify:** `backend/core/extraction/services.py`

```python
def save_corrections(
    self,
    document_id: int,
    corrections: Dict
) -> Dict[str, Any]:
    """
    Save corrections and adapt template
    """
    # ... existing code ...
    
    # ✅ NEW: Adapt template based on feedback
    from core.templates.adapter import TemplateAdapter
    
    adapter = TemplateAdapter()
    
    for field_name, corrected_value in corrections.items():
        # Get original extraction
        original_value = original_results['extracted_data'].get(field_name, '')
        
        # Get extraction context (where it was found)
        extraction_context = self._get_extraction_context(
            document.file_path,
            field_name,
            original_value
        )
        
        # Adapt template
        adapter.adapt_from_feedback(
            template_id=document.template_id,
            field_name=field_name,
            original_value=original_value,
            corrected_value=corrected_value,
            extraction_context=extraction_context
        )
    
    # ... rest of code ...
```

---

## 📊 **Expected Impact:**

### **Before (Current):**

```
Training:
  Features: word, position, surrounding words only
  NO pattern, NO context from template
  
Extraction:
  Rule-based: Uses pattern ✅
  CRF: Ignores pattern ❌
  
Result: Inconsistent extraction, low accuracy
```

### **After (With Solutions):**

```
Training:
  Features: word, position, surrounding words
           + pattern matching
           + context locations
           + label distances
  
Extraction:
  Rule-based: Uses pattern ✅
  CRF: Uses learned pattern features ✅
  
Template Adaptation:
  Feedback → Update pattern ✅
  Feedback → Update context ✅
  
Result: Consistent extraction, higher accuracy
```

---

## 🎯 **Implementation Priority:**

### **Phase 1: Fix BIO Labeling (DONE ✅)**
- Fixed substring matching
- Correct training labels

### **Phase 2: Add Template Features to Training (HIGH PRIORITY)**
- Pass template_config to training
- Extract pattern/context features
- Train model with template knowledge

### **Phase 3: Template Adaptation (MEDIUM PRIORITY)**
- Create TemplateAdapter class
- Update patterns from feedback
- Update contexts from feedback

### **Phase 4: Verification & Testing (HIGH PRIORITY)**
- Test with adapted templates
- Measure accuracy improvement
- Document adaptation process

---

## 📝 **Summary:**

**Q1: Apakah model belajar dari pattern/context?**
- ❌ **TIDAK!** Model CRF saat ini TIDAK belajar dari pattern dan context di template.
- Model hanya belajar dari lexical, orthographic, dan layout features.

**Q2: Apakah ada verifikasi pattern/context saat feedback?**
- ❌ **TIDAK!** Tidak ada verifikasi atau update pattern/context saat feedback.
- Feedback hanya digunakan untuk retrain model CRF.

**Q3: Apakah pattern/context perlu disesuaikan?**
- ✅ **YA!** Pattern dan context HARUS disesuaikan berdasarkan feedback untuk:
  - Konsistensi antara rule-based dan CRF extraction
  - Meningkatkan akurasi extraction
  - Adaptive learning yang sebenarnya

**Current Status:**
- ✅ BIO labeling fixed
- ❌ Template features NOT used in training
- ❌ Template adaptation NOT implemented

**Next Steps:**
1. Implement template feature extraction in training
2. Create template adapter for pattern/context updates
3. Integrate adapter with feedback pipeline
4. Test and measure improvement

---

**Date:** 2025-11-08
**Status:** ⚠️ CRITICAL ISSUE IDENTIFIED - Template features not used in training
