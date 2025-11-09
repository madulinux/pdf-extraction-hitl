# 📋 Strategy Types Standardization

**Last Updated:** 2024-11-09  
**Status:** ✅ Fully Standardized & Normalized

---

## 🎯 Standard Strategy Types

Sistem menggunakan **3 strategy types** yang telah distandarisasi sesuai dengan `StrategyType` enum:

```python
class StrategyType(Enum):
    """Enumeration of available extraction strategies"""
    RULE_BASED = "rule_based"
    POSITION_BASED = "position_based"
    CRF = "crf"
```

---

## ✅ Correct Strategy Types

| Strategy Type | Value | Description |
|---------------|-------|-------------|
| **Rule-based** | `rule_based` | Pattern matching dengan regex dan label detection |
| **Position-based** | `position_based` | Ekstraksi berdasarkan koordinat (x, y) |
| **CRF** | `crf` | Conditional Random Fields (ML model) |

---

## ❌ DEPRECATED Strategy Types (DO NOT USE)

Berikut adalah strategy types yang **TIDAK BOLEH** digunakan lagi:

| ❌ Old Value | ✅ Correct Value | Status |
|-------------|-----------------|--------|
| `rule-based` | `rule_based` | ❌ Deprecated (hyphen) |
| `rule-based-label` | `rule_based` | ❌ Deprecated (variant) |
| `position-based` | `position_based` | ❌ Deprecated (hyphen) |
| `crf-model` | `crf` | ❌ Deprecated (variant) |

---

## 🔧 Fixed Files

### 1. `/core/extraction/strategies.py`

**Fixed Locations:**

#### Line 242 - Rule-based Label Extraction
```python
# ❌ BEFORE
method='rule-based-label',

# ✅ AFTER
method='rule_based',  # ✅ Standard enum value
```

#### Line 320 - Rule-based Regex Extraction
```python
# ❌ BEFORE
method='rule-based',

# ✅ AFTER
method='rule_based',  # ✅ Standard enum value
```

#### Line 585 - Position-based Extraction
```python
# ❌ BEFORE
method='position-based',

# ✅ AFTER
method='position_based',  # ✅ Standard enum value
```

#### Line 760 - CRF Model Extraction
```python
# ❌ BEFORE
method='crf-model',

# ✅ AFTER
method='crf',  # ✅ Standard enum value
```

---

### 2. `/core/extraction/hybrid_strategy.py`

**Added Normalization:**

#### StrategyType.normalize() - Static Method
```python
@staticmethod
def normalize(method: str) -> str:
    """
    Normalize strategy type to standard enum value
    
    Handles legacy/variant naming:
    - 'crf-model' → 'crf'
    - 'rule-based' → 'rule_based'
    - 'rule-based-label' → 'rule_based'
    - 'position-based' → 'position_based'
    """
    if 'crf' in method.lower():
        return StrategyType.CRF.value
    if 'rule' in method.lower():
        return StrategyType.RULE_BASED.value
    if 'position' in method.lower():
        return StrategyType.POSITION_BASED.value
    return StrategyType.RULE_BASED.value
```

#### _update_strategy_performance() - Normalization Applied
```python
def _update_strategy_performance(self, ...):
    # ✅ NORMALIZE strategy type before saving
    normalized_method = StrategyType.normalize(method)
    
    # Save to database with normalized value
    perf_repo.update_performance(
        strategy_type=normalized_method,  # ✅ Always normalized
        ...
    )
```

---

### 3. `/tools/migrate_strategy_types.py`

**Migration Script for Existing Data:**

```bash
# Dry run (preview changes)
python tools/migrate_strategy_types.py --dry-run

# Actual migration
python tools/migrate_strategy_types.py
```

This script:
- ✅ Normalizes all existing `strategy_type` values in database
- ✅ Merges duplicate records (e.g., 'crf' + 'crf-model' → 'crf')
- ✅ Preserves all performance metrics
- ✅ Safe rollback with dry-run mode

---

## 📊 Impact Analysis

### Before Standardization

Data yang tersimpan di database/feedback memiliki **4 strategy types berbeda**:
- `rule_based` ✅
- `rule-based-label` ❌
- `position_based` ✅
- `crf-model` ❌

### After Standardization

Semua data baru akan menggunakan **3 strategy types standar**:
- `rule_based` ✅
- `position_based` ✅
- `crf` ✅

---

## 🔄 Migration Strategy

### For Old Data (Already Stored)

File `populate_strategy_performance.py` sudah menangani konversi:

```python
# ✅ UNIFY: Treat 'crf-model' same as 'crf'
if strategy_type == 'crf-model':
    strategy_type = 'crf'

# ✅ UNIFY: Treat 'rule-based-label' same as 'rule_based'
if strategy_type == 'rule-based-label':
    strategy_type = 'rule_based'
```

### For New Data (Going Forward)

Semua ekstraksi baru akan otomatis menggunakan strategy types yang standar.

---

## 🎯 Best Practices

### 1. **Always Use Enum Values**

```python
from core.extraction.hybrid_strategy import StrategyType

# ✅ CORRECT
strategy = StrategyType.RULE_BASED.value  # "rule_based"
strategy = StrategyType.POSITION_BASED.value  # "position_based"
strategy = StrategyType.CRF.value  # "crf"

# ❌ WRONG
strategy = "rule-based"
strategy = "crf-model"
```

### 2. **Validate Strategy Types**

```python
def validate_strategy_type(strategy: str) -> bool:
    """Validate if strategy type is one of the standard types"""
    valid_strategies = {s.value for s in StrategyType}
    return strategy in valid_strategies

# Usage
if not validate_strategy_type(method):
    raise ValueError(f"Invalid strategy type: {method}")
```

### 3. **Database Queries**

```python
# ✅ CORRECT - Query with standard values
results = db.query(
    "SELECT * FROM strategy_performance WHERE strategy_type = ?",
    (StrategyType.CRF.value,)
)

# ❌ WRONG - Using deprecated values
results = db.query(
    "SELECT * FROM strategy_performance WHERE strategy_type = ?",
    ("crf-model",)  # Will not find any results!
)
```

---

## 📈 Performance Tracking

### Strategy Performance Table Schema

```sql
CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY,
    template_id INTEGER,
    field_name TEXT,
    strategy_type TEXT,  -- Must be: 'rule_based', 'position_based', or 'crf'
    total_extractions INTEGER,
    correct_extractions INTEGER,
    accuracy REAL,
    ...
);
```

### Valid Queries

```sql
-- ✅ Get CRF performance
SELECT * FROM strategy_performance 
WHERE strategy_type = 'crf';

-- ✅ Get rule-based performance
SELECT * FROM strategy_performance 
WHERE strategy_type = 'rule_based';

-- ✅ Get position-based performance
SELECT * FROM strategy_performance 
WHERE strategy_type = 'position_based';

-- ❌ WRONG - Will return empty
SELECT * FROM strategy_performance 
WHERE strategy_type = 'crf-model';
```

---

## 🧪 Testing

### Unit Test Example

```python
def test_strategy_type_standardization():
    """Test that all strategies use standard enum values"""
    
    # Test rule-based
    result = rule_based_strategy.extract(field_name, config)
    assert result.method == StrategyType.RULE_BASED.value
    assert result.method == "rule_based"
    
    # Test position-based
    result = position_strategy.extract(field_name, config)
    assert result.method == StrategyType.POSITION_BASED.value
    assert result.method == "position_based"
    
    # Test CRF
    result = crf_strategy.extract(field_name, config)
    assert result.method == StrategyType.CRF.value
    assert result.method == "crf"
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Using Hyphens Instead of Underscores

```python
# ❌ WRONG
method = "rule-based"
method = "position-based"

# ✅ CORRECT
method = "rule_based"
method = "position_based"
```

### ❌ Mistake 2: Using Variant Names

```python
# ❌ WRONG
method = "crf-model"
method = "rule-based-label"

# ✅ CORRECT
method = "crf"
method = "rule_based"
```

### ❌ Mistake 3: Hardcoding Strings

```python
# ❌ WRONG
if strategy == "crf-model":
    ...

# ✅ CORRECT
if strategy == StrategyType.CRF.value:
    ...
```

---

## 📝 Checklist for Developers

When working with strategy types:

- [ ] Import `StrategyType` enum from `hybrid_strategy.py`
- [ ] Use enum values: `.value` property
- [ ] Never use hyphens (`-`), always use underscores (`_`)
- [ ] Never create new strategy type variants
- [ ] Validate strategy types before database operations
- [ ] Update tests if adding new strategy types
- [ ] Document any changes to strategy types

---

## 🔗 Related Files

- `/core/extraction/hybrid_strategy.py` - StrategyType enum definition
- `/core/extraction/strategies.py` - Strategy implementations
- `/database/repositories/strategy_performance_repository.py` - Performance tracking
- `/tools/populate_strategy_performance.py` - Data migration script

---

## 📞 Support

If you encounter strategy type issues:

1. Check this documentation
2. Verify enum values in `hybrid_strategy.py`
3. Check database for inconsistent values
4. Run migration script if needed

---

**Remember:** Consistency is key! Always use the standard enum values. 🎯
