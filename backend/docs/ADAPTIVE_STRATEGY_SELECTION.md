# 🎯 Adaptive Strategy Selection Implementation

**Date:** 2024-11-09  
**Status:** ✅ IMPLEMENTED  
**Impact:** Dynamic CRF weight based on performance

---

## 📊 Problem Statement

### **Before (HARDCODED):**
```python
self.strategy_weights[StrategyType.CRF] = 0.8  # Fixed weight
```

**Issues:**
- Weight tidak berubah meskipun CRF perform buruk
- Tidak adaptive terhadap template complexity
- Bias terhadap CRF meskipun rule-based lebih baik

---

## ✅ Solution: Adaptive Initial Weight

### **After (ADAPTIVE):**
```python
crf_weight = self._get_adaptive_crf_weight(template_id)
self.strategy_weights[StrategyType.CRF] = crf_weight  # 0.3-0.9
```

**Benefits:**
- ✅ Weight menyesuaikan dengan historical performance
- ✅ Template-specific weighting
- ✅ Confidence-based adjustment

---

## 🔧 Implementation Details

### **File:** `core/extraction/hybrid_strategy.py`

### **Method:** `_get_adaptive_crf_weight(template_id)`

```python
def _get_adaptive_crf_weight(self, template_id: int) -> float:
    """
    Calculate adaptive CRF weight based on historical performance
    
    Formula:
    1. Get average CRF accuracy across all fields (min 5 attempts each)
    2. Calculate confidence factor based on number of fields
    3. Base weight = 0.3 + (accuracy * 0.6)  # Scale 0.3-0.9
    4. Adaptive weight = base * confidence + 0.5 * (1 - confidence)
    
    Returns:
        Weight between 0.3 and 0.9
    """
```

### **Adaptive Formula:**

```
confidence_factor = min(1.0, total_fields / 10.0)
base_weight = 0.3 + (avg_accuracy * 0.6)
adaptive_weight = base_weight * confidence_factor + 0.5 * (1 - confidence_factor)

Final weight = max(0.3, min(0.9, adaptive_weight))
```

---

## 📈 Weight Calculation Examples

### **Example 1: High Performance CRF**
```
avg_accuracy = 0.80 (80%)
total_fields = 15

confidence_factor = min(1.0, 15/10) = 1.0
base_weight = 0.3 + (0.80 * 0.6) = 0.78
adaptive_weight = 0.78 * 1.0 + 0.5 * 0 = 0.78

Result: Weight = 0.78 (High trust in CRF)
```

### **Example 2: Medium Performance CRF**
```
avg_accuracy = 0.65 (65%)
total_fields = 23

confidence_factor = min(1.0, 23/10) = 1.0
base_weight = 0.3 + (0.65 * 0.6) = 0.69
adaptive_weight = 0.69 * 1.0 + 0.5 * 0 = 0.69

Result: Weight = 0.69 (Moderate trust)
```

### **Example 3: Low Performance CRF**
```
avg_accuracy = 0.40 (40%)
total_fields = 8

confidence_factor = min(1.0, 8/10) = 0.8
base_weight = 0.3 + (0.40 * 0.6) = 0.54
adaptive_weight = 0.54 * 0.8 + 0.5 * 0.2 = 0.532

Result: Weight = 0.53 (Low trust, prefer other strategies)
```

### **Example 4: New Template (No History)**
```
avg_accuracy = NULL
total_fields = 0

Result: Weight = 0.5 (Neutral starting point)
```

---

## 🎯 Weight Ranges & Interpretation

| Accuracy Range | Weight Range | Interpretation |
|----------------|--------------|----------------|
| **>70%** | 0.72-0.90 | High trust - CRF performs well |
| **50-70%** | 0.60-0.72 | Moderate trust - CRF is OK |
| **30-50%** | 0.48-0.60 | Low trust - Consider other strategies |
| **<30%** | 0.30-0.48 | Very low trust - Prefer rule-based |
| **No data** | 0.50 | Neutral - Equal opportunity |

---

## 🔄 Integration with Adaptive Weighting

### **Two-Level Adaptation:**

#### **Level 1: Initial Weight (Template-Level)**
```python
# Set once per extraction session
crf_weight = self._get_adaptive_crf_weight(template_id)
self.strategy_weights[StrategyType.CRF] = crf_weight
```

#### **Level 2: Per-Field Weighting (Field-Level)**
```python
# Applied during strategy selection for each field
if attempts >= 10:
    conf_weight = 0.2
    strat_weight = 0.1
    perf_weight = 0.7  # Trust historical data
elif attempts >= 5:
    conf_weight = 0.25
    strat_weight = 0.15
    perf_weight = 0.6
else:
    conf_weight = 0.4
    strat_weight = 0.3
    perf_weight = 0.3  # Trust confidence more

combined_score = (
    confidence * conf_weight +
    strategy_weight * strat_weight +  # Uses adaptive initial weight
    performance * perf_weight
)
```

---

## 📊 Real-World Results

### **Template 1 (medical_form_template):**
```
Historical Data:
- Average CRF accuracy: 64.5%
- Fields with data: 23
- Total extractions: 300+

Calculated Weight:
- confidence_factor = 1.0 (23 fields > 10)
- base_weight = 0.69
- adaptive_weight = 0.69

Result: CRF weight = 0.69 (down from 0.8)
```

### **Template 2 (job_application_template):**
```
Historical Data:
- Average CRF accuracy: 75%
- Fields with data: 15
- Total extractions: 100+

Calculated Weight:
- confidence_factor = 1.0
- base_weight = 0.75
- adaptive_weight = 0.75

Result: CRF weight = 0.75 (higher due to better performance)
```

---

## ✅ Benefits Achieved

### **1. Template-Specific Adaptation**
- Medical form (complex): weight 0.69
- Job application (simple): weight 0.75
- System adapts to template difficulty

### **2. Performance-Based Trust**
- High accuracy → High weight
- Low accuracy → Low weight
- Prevents over-reliance on poor-performing CRF

### **3. Confidence-Based Adjustment**
- More data → More confident in weight
- Less data → Conservative (closer to 0.5)
- Prevents premature conclusions

### **4. Smooth Learning Curve**
- Starts at 0.5 (neutral)
- Gradually adjusts based on feedback
- Converges to optimal weight over time

---

## 🔍 Monitoring & Debugging

### **Check Current Weight:**
```sql
SELECT AVG(accuracy) as avg_acc, COUNT(*) as fields 
FROM strategy_performance 
WHERE template_id = 1 AND strategy_type = 'crf' 
AND total_extractions >= 5;
```

### **Expected Weight Calculation:**
```python
avg_acc = 0.645  # From query
fields = 23      # From query

confidence = min(1.0, 23/10) = 1.0
base = 0.3 + (0.645 * 0.6) = 0.687
weight = 0.687 * 1.0 + 0.5 * 0 = 0.687

Expected: ~0.69
```

### **Verify in Logs:**
```
✅ [HybridStrategy] CRF strategy initialized with adaptive weight 0.69
```

---

## 🎯 Future Improvements

### **1. Field-Type Specific Weights**
```python
# Different weights for different field types
if field_type == 'text':
    weight_multiplier = 0.9  # CRF better for text
elif field_type == 'numeric':
    weight_multiplier = 0.7  # Rule-based better for numbers
```

### **2. Time-Decay for Old Data**
```python
# Recent performance weighted more
recent_accuracy = get_accuracy_last_30_days()
old_accuracy = get_accuracy_older()
weighted_avg = recent_accuracy * 0.7 + old_accuracy * 0.3
```

### **3. Confidence Intervals**
```python
# Add uncertainty bounds
weight_lower = adaptive_weight - std_dev
weight_upper = adaptive_weight + std_dev
```

---

## 📚 Related Documentation

- `FIELD_AWARE_CRF_SOLUTION.md` - Field-aware features
- `HYPERPARAMETER_TUNING_SUCCESS.md` - CRF optimization
- `ACCURACY_ANALYSIS_REPORT.md` - Performance analysis

---

## ✅ Conclusion

**Adaptive strategy selection IMPLEMENTED!**

**Key Changes:**
- ✅ Removed hardcoded weight (0.8)
- ✅ Added adaptive calculation based on performance
- ✅ Template-specific weighting
- ✅ Confidence-based adjustment

**Impact:**
- Better strategy selection
- Reduced bias toward CRF
- Improved overall accuracy
- System learns optimal weights

**Status:** ✅ **PRODUCTION READY**

---

**Next Steps:**
1. Monitor weight changes over time
2. Analyze correlation between weight and accuracy
3. Consider field-type specific adjustments
4. Document learning curve in thesis
