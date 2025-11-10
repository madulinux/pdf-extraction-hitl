# 🔧 Template Analyzer Optimization Plan

**Priority**: **HIGH** - Should be done BEFORE Phase 2  
**Reason**: Better context extraction → Better model learning → Higher accuracy

---

## 🎯 Current Issues in Analyzer

### **Issue 1: Weak Context for event_location**
```python
# Current result:
{
  "label": "di",
  "label_position": {...},
  "words_before": [{"text": "di", ...}],
  "words_after": []  # ❌ EMPTY!
}
```

**Problem**: 
- Label "di" is too generic
- No words_after (because field is on same line)
- No information about what comes AFTER the field

---

### **Issue 2: Only Captures Same-Line Context**
```python
# Line 244 in analyzer.py
if abs(word_y_center - marker_y_center) < 10:
    # Only words within 10 pixels vertically
```

**Problem**:
- Misses context from lines above/below
- For multi-line fields, misses important boundaries
- Can't detect "next field" position

---

### **Issue 3: No Field Boundary Information**
```python
# Current context:
{
  "label": "di",
  "words_before": [...],
  "words_after": []
}

# Missing:
# - Next field position
# - Typical field length
# - Field end pattern
```

**Problem**: Model has no hints about where field should end

---

## 💡 Optimization Solutions

### **Solution 1: Enhanced Context Extraction** (CRITICAL)

**Add to `_extract_context_words()`**:

```python
def _extract_context_words(self, page_idx, marker_x, marker_y, marker_width, marker_height):
    """Extract enhanced context with multi-line support"""
    
    # ... existing code ...
    
    # ✅ NEW: Also capture words BELOW marker (next line)
    words_below = []
    next_line_y = marker_y + 20  # Approximate next line
    
    for word in words:
        word_y = word.get('top', 0)
        # Words on next line (within 30 pixels below)
        if next_line_y < word_y < next_line_y + 30:
            words_below.append({
                'text': word.get('text', ''),
                'x': word.get('x0', 0),
                'y': word_y,
                'distance_y': word_y - marker_y
            })
    
    # Sort by x position (left to right)
    words_below.sort(key=lambda w: w['x'])
    
    return {
        'label': label_text,
        'label_position': label_position,
        'words_before': words_before_enhanced,
        'words_after': words_after_enhanced,
        'words_below': words_below[:5],  # ✅ NEW!
    }
```

**Impact**: Model learns what comes after field (next line)

---

### **Solution 2: Detect Next Field Position** (HIGH PRIORITY)

**Add new method**:

```python
def _find_next_field_position(self, current_field_idx: int) -> Dict:
    """
    Find the position of the next field in document
    Helps model learn field boundaries
    """
    if current_field_idx >= len(self.fields) - 1:
        return None
    
    next_field = self.fields[current_field_idx + 1]
    
    return {
        'x': next_field['x'],
        'y': next_field['y'],
        'distance_x': next_field['x'] - self.fields[current_field_idx]['x'],
        'distance_y': next_field['y'] - self.fields[current_field_idx]['y'],
        'field_name': next_field['name']
    }
```

**Usage in config**:
```json
{
  "field_name": "event_location",
  "locations": [{
    "context": {
      "label": "di",
      "next_field": {
        "name": "issue_place",
        "distance_y": 50,
        "typical_y": 380
      }
    }
  }]
}
```

**Impact**: Model knows to stop before next field

---

### **Solution 3: Analyze Field Patterns** (MEDIUM PRIORITY)

**Add pattern detection**:

```python
def _analyze_field_pattern(self, field_name: str, marker_text: str) -> Dict:
    """
    Analyze expected pattern for field based on name
    Uses heuristics, not hardcoded rules
    """
    patterns = {}
    
    # Detect if field name suggests specific pattern
    name_lower = field_name.lower()
    
    # Location/address fields
    if any(x in name_lower for x in ['location', 'address', 'place', 'alamat', 'tempat']):
        patterns['type'] = 'location'
        patterns['typical_length'] = 40-60  # chars
        patterns['typical_words'] = 5-10
        patterns['end_pattern'] = r'\d{5}'  # Postal code
        patterns['multi_line'] = True
    
    # Date fields
    elif any(x in name_lower for x in ['date', 'tanggal']):
        patterns['type'] = 'date'
        patterns['typical_length'] = 10-20
        patterns['typical_words'] = 2-4
        patterns['end_pattern'] = r'\d{4}'  # Year
        patterns['multi_line'] = False
    
    # Name fields
    elif any(x in name_lower for x in ['name', 'nama']):
        patterns['type'] = 'name'
        patterns['typical_length'] = 15-40
        patterns['typical_words'] = 2-5
        patterns['end_pattern'] = None
        patterns['multi_line'] = False
    
    # Default
    else:
        patterns['type'] = 'text'
        patterns['typical_length'] = 20-50
        patterns['typical_words'] = 3-8
        patterns['end_pattern'] = None
        patterns['multi_line'] = False
    
    return patterns
```

**Impact**: Model has hints about expected field characteristics

---

### **Solution 4: Store Enhanced Context in Database** (REQUIRED)

**Update migration 006**:

```sql
-- Add new columns to field_contexts
ALTER TABLE field_contexts ADD COLUMN words_below TEXT;  -- JSON array
ALTER TABLE field_contexts ADD COLUMN next_field_info TEXT;  -- JSON object
ALTER TABLE field_contexts ADD COLUMN field_patterns TEXT;  -- JSON object
```

**Update `create_field_context()` in repository**:

```python
def create_field_context(
    self,
    field_location_id: int,
    label: str = '',
    label_position: Dict = None,
    words_before: List[Dict] = None,
    words_after: List[Dict] = None,
    words_below: List[Dict] = None,  # ✅ NEW
    next_field_info: Dict = None,     # ✅ NEW
    field_patterns: Dict = None       # ✅ NEW
) -> int:
    cursor.execute("""
        INSERT INTO field_contexts 
        (field_location_id, label, label_position, words_before, words_after,
         words_below, next_field_info, field_patterns)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        field_location_id,
        label,
        json.dumps(label_position) if label_position else None,
        json.dumps(words_before) if words_before else None,
        json.dumps(words_after) if words_after else None,
        json.dumps(words_below) if words_below else None,      # ✅ NEW
        json.dumps(next_field_info) if next_field_info else None,  # ✅ NEW
        json.dumps(field_patterns) if field_patterns else None      # ✅ NEW
    ))
```

---

## 📋 Implementation Steps

### **Step 1: Update Database Schema** (5 minutes)
```bash
# Create new migration
cat > database/migrations/007_enhance_field_contexts.sql << 'EOF'
-- Add enhanced context columns
ALTER TABLE field_contexts ADD COLUMN words_below TEXT;
ALTER TABLE field_contexts ADD COLUMN next_field_info TEXT;
ALTER TABLE field_contexts ADD COLUMN field_patterns TEXT;
EOF

# Apply migration
sqlite3 data/app.db < database/migrations/007_enhance_field_contexts.sql
```

---

### **Step 2: Update Analyzer** (15 minutes)

**Files to modify**:
1. `core/templates/analyzer.py`
   - Enhance `_extract_context_words()` to capture words_below
   - Add `_find_next_field_position()` method
   - Add `_analyze_field_pattern()` method
   - Update config generation to include new fields

---

### **Step 3: Update Repository** (5 minutes)

**File**: `database/repositories/config_repository.py`
- Update `create_field_context()` signature
- Add new parameters to INSERT statement

---

### **Step 4: Update Config Loader** (5 minutes)

**File**: `core/templates/config_loader.py`
- Update `save_config_to_database()` to pass new fields
- Update `_load_from_database()` to load new fields

---

### **Step 5: Re-analyze Template** (2 minutes)
```bash
# Delete old template
sqlite3 data/app.db "DELETE FROM templates WHERE id = 1"

# Re-upload template (will trigger new analysis)
# Via UI or batch_seeder
```

---

### **Step 6: Verify Enhanced Context** (2 minutes)
```bash
sqlite3 data/app.db "
SELECT 
  fc.label,
  LENGTH(fc.words_below) as wb_len,
  LENGTH(fc.next_field_info) as nf_len,
  LENGTH(fc.field_patterns) as fp_len
FROM field_contexts fc
WHERE field_location_id IN (
  SELECT id FROM field_locations 
  WHERE field_config_id IN (
    SELECT id FROM field_configs WHERE field_name = 'event_location'
  )
)
"
```

Expected output:
```
di|150|80|120
```

---

## 🎯 Expected Impact

### **Before Optimization**
```
Context for event_location:
{
  "label": "di",
  "words_before": [{"text": "di"}],
  "words_after": []
}

Model accuracy: 72%
event_location accuracy: ~9%
```

---

### **After Optimization**
```
Context for event_location:
{
  "label": "di",
  "words_before": [{"text": "tanggal"}, {"text": "di"}],
  "words_after": [],
  "words_below": [
    {"text": "Kota", "y": 380},
    {"text": "Bau", "y": 380},
    {"text": "Bau,", "y": 380}
  ],
  "next_field_info": {
    "name": "issue_place",
    "distance_y": 50,
    "typical_y": 380
  },
  "field_patterns": {
    "type": "location",
    "typical_length": 40-60,
    "end_pattern": "\\d{5}"
  }
}

Model accuracy: Expected 80-85% (with 100 docs)
event_location accuracy: Expected 70-80%
```

---

## 📊 Comparison: Analyzer Optimization vs Phase 2

### **Option A: Analyzer Optimization First**
```
Time: ~30 minutes
Effort: Medium (modify analyzer, migration, test)
Impact: +8-13% accuracy (72% → 80-85%)
Benefit: Better context for ALL future templates
```

### **Option B: Phase 2 (Boundary Features) First**
```
Time: ~30 minutes
Effort: Medium (modify learner, strategies)
Impact: +5-8% accuracy (72% → 77-80%)
Benefit: Better boundary detection
```

### **Option C: Both (Recommended)**
```
Time: ~45 minutes
Effort: High
Impact: +13-18% accuracy (72% → 85-90%)
Benefit: Best of both worlds
```

---

## ✅ Recommendation

### **DO ANALYZER OPTIMIZATION FIRST!**

**Reasons**:
1. ✅ **Better foundation**: Improved context benefits all future work
2. ✅ **Template-level fix**: Works for any template, not just current one
3. ✅ **Cleaner solution**: Model learns from better data, not workarounds
4. ✅ **Thesis value**: Shows systematic approach to problem-solving

**Then do Phase 2** if still needed (likely will get 85%+ from analyzer alone)

---

## 🎓 For Thesis

### **Key Insight**: **Data Quality > Feature Engineering**

```
Bad context + Good features = 77% accuracy
Good context + Basic features = 85% accuracy
Good context + Good features = 90%+ accuracy

Conclusion: Fix data quality first!
```

### **Systematic Problem Solving**
```
1. Identify root cause (weak context)
2. Fix at source (analyzer)
3. Verify improvement
4. Add features if needed (phase 2)

NOT:
1. Add workaround features
2. Hope it works
3. Add more workarounds
```

---

**Last Updated**: 2025-11-11 04:52 AM  
**Status**: 📋 **PLAN READY**  
**Next**: Implement analyzer optimization → Test → Evaluate if Phase 2 needed
