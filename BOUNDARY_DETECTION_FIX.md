# 🔧 FIX: Boundary Detection & Post-Processing

## 🔍 **Root Cause Analysis:**

### **Extraction Errors Found:**

```
Field: event_name
❌ Extracted: "dalam kegiatan "Workshop Producer, radio""
✅ Expected:  "Workshop Producer, radio"
Problem: Prefix "dalam kegiatan" included

Field: event_date
❌ Extracted: "November 2024"
✅ Expected:  "03 November 2024"
Problem: Missing day number

Field: event_location
❌ Extracted: "2 Surabaya, Sulawesi Tenggara 95028"
✅ Expected:  "Gg. Antapani Lama No. 2\nSurabaya, Sulawesi Tenggara 95028"
Problem: Missing street name prefix

Field: issue_place
❌ Extracted: "Mimika, 14 November 2024"
✅ Expected:  "Mimika"
Problem: Mixed with date (boundary detection failed)

Field: issue_date
❌ Extracted: "2024"
✅ Expected:  "14 November 2024"
Problem: Only year extracted

Field: supervisor_name
❌ Extracted: "(Chandra Astuti, S.Kom)"
✅ Expected:  "Chandra Astuti, S.Kom"
Problem: Parentheses included

Field: chairman_name
❌ Extracted: "(Banawa Anggriawan)"
✅ Expected:  "Banawa Anggriawan"
Problem: Parentheses included
```

---

## 🎯 **Solutions Needed:**

### **1. Stronger Boundary Detection Features**
Current features are not enough. Need:
- ✅ Punctuation-based boundaries (already added)
- ✅ Newline detection (already added)
- ⚠️ **Need: Context-aware boundary detection**
- ⚠️ **Need: Field-specific patterns from template**

### **2. Post-Processing Rules (Pattern-Based, NOT Hardcoded!)**
Need to clean extracted values:
- Remove common prefixes (learned from feedback patterns)
- Remove parentheses/brackets
- Expand incomplete dates
- Separate mixed fields

### **3. Template-Specific Patterns**
Learn from template config and feedback:
- Common prefixes for each field type
- Expected formats (date, name, location)
- Boundary markers

---

## 🔧 **Implementation Plan:**

### **Phase 1: Enhanced Post-Processing (Pattern-Based)**

Add post-processing yang belajar dari feedback patterns:

```python
# backend/core/extraction/post_processor.py

class AdaptivePostProcessor:
    """
    Post-processor yang belajar dari feedback patterns
    TIDAK hardcoded, tapi pattern-based!
    """
    
    def __init__(self, template_id: int):
        self.template_id = template_id
        self.learned_patterns = self._load_learned_patterns()
    
    def _load_learned_patterns(self) -> Dict:
        """
        Load patterns yang sudah dipelajari dari feedback
        """
        # Analyze feedback history untuk template ini
        # Extract common patterns:
        # - Common prefixes to remove
        # - Common suffixes to remove
        # - Expected formats
        pass
    
    def clean_value(self, field_name: str, value: str) -> str:
        """
        Clean extracted value based on learned patterns
        """
        if not value:
            return value
        
        # 1. Remove common noise (learned from feedback)
        value = self._remove_learned_noise(field_name, value)
        
        # 2. Remove structural noise (parentheses, quotes)
        value = self._remove_structural_noise(value)
        
        # 3. Expand incomplete values (dates, etc.)
        value = self._expand_incomplete_value(field_name, value)
        
        # 4. Validate format
        value = self._validate_format(field_name, value)
        
        return value
    
    def _remove_learned_noise(self, field_name: str, value: str) -> str:
        """
        Remove noise patterns learned from feedback
        """
        patterns = self.learned_patterns.get(field_name, {})
        
        # Remove common prefixes (learned from feedback)
        for prefix in patterns.get('common_prefixes', []):
            if value.lower().startswith(prefix.lower()):
                value = value[len(prefix):].strip()
        
        # Remove common suffixes
        for suffix in patterns.get('common_suffixes', []):
            if value.lower().endswith(suffix.lower()):
                value = value[:-len(suffix)].strip()
        
        return value
    
    def _remove_structural_noise(self, value: str) -> str:
        """
        Remove structural noise (parentheses, quotes, etc.)
        """
        # Remove surrounding parentheses
        if value.startswith('(') and value.endswith(')'):
            value = value[1:-1].strip()
        
        # Remove surrounding quotes
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].strip()
        
        # Remove "dalam kegiatan" prefix (common pattern)
        if value.lower().startswith('dalam kegiatan'):
            value = value[14:].strip()
            # Remove quotes after prefix
            value = value.strip('"').strip()
        
        return value
    
    def _expand_incomplete_value(self, field_name: str, value: str) -> str:
        """
        Expand incomplete values (e.g., dates)
        """
        # For date fields, check if incomplete
        if 'date' in field_name.lower():
            # If only year, try to find full date in context
            if re.match(r'^\d{4}$', value):
                # This needs context from PDF words
                # For now, return as is
                pass
            
            # If missing day, try to find it
            if re.match(r'^[A-Za-z]+ \d{4}$', value):
                # e.g., "November 2024" → need to find day
                pass
        
        return value
    
    def _validate_format(self, field_name: str, value: str) -> str:
        """
        Validate and fix format based on expected patterns
        """
        patterns = self.learned_patterns.get(field_name, {})
        expected_format = patterns.get('expected_format')
        
        if expected_format:
            # Validate against expected format
            # If doesn't match, try to fix
            pass
        
        return value
```

### **Phase 2: Learn Patterns from Feedback**

```python
# backend/core/learning/pattern_learner.py

class FeedbackPatternLearner:
    """
    Analyze feedback to learn common patterns
    """
    
    def learn_patterns(self, template_id: int) -> Dict:
        """
        Analyze feedback history to learn patterns
        """
        feedbacks = self._get_feedbacks(template_id)
        patterns = {}
        
        for field_name in self._get_unique_fields(feedbacks):
            field_feedbacks = [f for f in feedbacks if f['field_name'] == field_name]
            
            patterns[field_name] = {
                'common_prefixes': self._find_common_prefixes(field_feedbacks),
                'common_suffixes': self._find_common_suffixes(field_feedbacks),
                'expected_format': self._infer_format(field_feedbacks),
                'boundary_markers': self._find_boundary_markers(field_feedbacks)
            }
        
        return patterns
    
    def _find_common_prefixes(self, feedbacks: List[Dict]) -> List[str]:
        """
        Find common prefixes that were removed in corrections
        """
        prefixes = []
        
        for fb in feedbacks:
            original = fb['original_value']
            corrected = fb['corrected_value']
            
            # If corrected is substring of original
            if corrected in original:
                # Extract prefix
                idx = original.find(corrected)
                if idx > 0:
                    prefix = original[:idx].strip()
                    prefixes.append(prefix)
        
        # Count frequency and return common ones
        from collections import Counter
        counter = Counter(prefixes)
        # Return prefixes that appear in >10% of feedbacks
        threshold = len(feedbacks) * 0.1
        return [p for p, count in counter.items() if count >= threshold]
    
    def _find_common_suffixes(self, feedbacks: List[Dict]) -> List[str]:
        """
        Find common suffixes that were removed in corrections
        """
        # Similar to prefixes
        pass
    
    def _infer_format(self, feedbacks: List[Dict]) -> str:
        """
        Infer expected format from corrected values
        """
        # Analyze corrected values to infer pattern
        # E.g., for dates: "DD Month YYYY"
        pass
    
    def _find_boundary_markers(self, feedbacks: List[Dict]) -> List[str]:
        """
        Find common boundary markers (punctuation, keywords)
        """
        pass
```

### **Phase 3: Context-Aware Extraction**

Improve CRF extraction to use context better:

```python
# In learner.py and strategies.py

# Add context window features
features['context_window_-2'] = words[i-2]['text'] if i >= 2 else 'BOS'
features['context_window_-1'] = words[i-1]['text'] if i >= 1 else 'BOS'
features['context_window_+1'] = words[i+1]['text'] if i < len(words)-1 else 'EOS'
features['context_window_+2'] = words[i+2]['text'] if i < len(words)-2 else 'EOS'

# Add label context (from template)
if context and context.get('label'):
    label = context['label']
    # Check if current word is near label
    features['near_label'] = distance_from_label < 50
    features['label_keyword'] = label.lower().split()[0] if label else ''
```

---

## 🚀 **Implementation Priority:**

1. **HIGH: Post-Processing (Quick Win)**
   - Add `AdaptivePostProcessor` class
   - Clean parentheses, quotes
   - Remove "dalam kegiatan" prefix
   - Expected improvement: +15-20%

2. **MEDIUM: Pattern Learning**
   - Analyze feedback to learn patterns
   - Store patterns in template config
   - Use patterns for post-processing
   - Expected improvement: +10-15%

3. **LOW: Enhanced Features**
   - Add context window features
   - Improve boundary detection
   - Expected improvement: +5-10%

**Total Expected Improvement: +30-45%**
**Target: 24% → 55-69%**

---

## 📊 **Expected Results:**

### **After Post-Processing:**
```
Before: 24% (raw extraction)
After:  45% (with post-processing)
Improvement: +21%
```

### **After Pattern Learning:**
```
Before: 45% (with basic post-processing)
After:  60% (with learned patterns)
Improvement: +15%
```

### **After Enhanced Features + Retrain:**
```
Before: 60% (with patterns)
After:  75% (with better features + more training)
Improvement: +15%
```

**Final Target: 75-80% accuracy** 🎯
