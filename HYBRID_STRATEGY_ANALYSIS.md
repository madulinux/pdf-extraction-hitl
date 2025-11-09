# 🔍 Analisis: Mengapa CRF Tidak Dipilih untuk Beberapa Field?

## 📊 **Document 298 - Extraction Results**

### **Fields yang TIDAK menggunakan CRF:**

1. **event_date**
   - CRF: `'02 February 2025'` (confidence: **0.5092**)
   - Position-based: `'February 2025'` (confidence: **0.6920**)
   - **Chosen:** Position-based ✅

2. **issue_place**
   - CRF: `'Nagekeo, 15 February 2025'` (confidence: **0.8265**)
   - Rule-based: (confidence: **0.6700**)
   - **Chosen:** Rule-based ❌ **UNEXPECTED!**

3. **issue_date**
   - CRF: (Tidak ada hasil / confidence rendah)
   - Position-based: `'February 2025'` (confidence: **0.6920**)
   - **Chosen:** Position-based ✅

---

## 🧮 **Hybrid Scoring Formula**

```python
combined_score = (
    field_value.confidence * 0.4 +    # 40% confidence
    strategy_weight * 0.3 +            # 30% strategy weight
    performance_score * 0.3            # 30% historical performance
)
```

### **Strategy Weights:**
```
CRF:            0.8  (User baru ubah dari 0.7)
Rule-based:     0.5  (default)
Position-based: 0.5  (default)
```

### **Historical Performance:**
```
Tidak ada table strategy_performance
→ Semua strategy menggunakan default: 0.5
```

---

## 📊 **Scoring Analysis**

### **Case 1: event_date** ✅ Correct Decision

**CRF:**
```
Confidence:  0.5092 × 0.4 = 0.2037
Weight:      0.8    × 0.3 = 0.2400
Performance: 0.5    × 0.3 = 0.1500
────────────────────────────────
TOTAL:       0.5937
```

**Position-based:**
```
Confidence:  0.6920 × 0.4 = 0.2768
Weight:      0.5    × 0.3 = 0.1500
Performance: 0.5    × 0.3 = 0.1500
────────────────────────────────
TOTAL:       0.5768
```

**Winner:** CRF (0.5937 > 0.5768) ✅

**BUT:** Ada override logic!
```python
# Line 423-434: Override if confidence difference > 0.1
if result.confidence > best_result.confidence + 0.1:
    # Use the one with higher confidence
```

Position-based confidence (0.6920) > CRF confidence (0.5092) + 0.1 = 0.6092
→ **Override triggered!** Position-based dipilih! ✅

**Conclusion:** Sistem bekerja dengan benar. CRF confidence terlalu rendah.

---

### **Case 2: issue_place** ❌ UNEXPECTED!

**CRF:**
```
Confidence:  0.8265 × 0.4 = 0.3306
Weight:      0.8    × 0.3 = 0.2400
Performance: 0.5    × 0.3 = 0.1500
────────────────────────────────
TOTAL:       0.7206
```

**Rule-based:**
```
Confidence:  0.6700 × 0.4 = 0.2680
Weight:      0.5    × 0.3 = 0.1500
Performance: 0.5    × 0.3 = 0.1500
────────────────────────────────
TOTAL:       0.5680
```

**Expected Winner:** CRF (0.7206 > 0.5680) ✅

**BUT:** Hybrid chose Rule-based! ❌

**Possible Reasons:**

1. **Historical performance tinggi untuk rule-based?**
   - Jika rule-based punya accuracy 0.9 dari historical data:
   ```
   Rule-based score = 0.2680 + 0.1500 + (0.9 × 0.3) = 0.6880
   CRF score = 0.7206
   ```
   - CRF masih menang! Bukan ini.

2. **Bug di hybrid strategy?**
   - Mungkin ada logic error
   - Atau CRF result tidak masuk ke scoring

3. **Post-processor mengubah hasil?**
   - Post-processor bisa mengubah value dan confidence
   - Tapi seharusnya tidak mengubah method

---

### **Case 3: issue_date** ✅ Correct Decision

**CRF:**
```
Tidak ada hasil atau confidence sangat rendah
```

**Position-based:**
```
Confidence:  0.6920 × 0.4 = 0.2768
Weight:      0.5    × 0.3 = 0.1500
Performance: 0.5    × 0.3 = 0.1500
────────────────────────────────
TOTAL:       0.5768
```

**Winner:** Position-based (CRF tidak ada hasil) ✅

**Conclusion:** Sistem bekerja dengan benar.

---

## 🔍 **Root Cause Analysis**

### **Problem 1: CRF Confidence Rendah untuk Date Fields**

**event_date:**
- CRF: 0.5092 (terlalu rendah!)
- Expected: >0.7

**Why?**
1. Model mungkin belum belajar date patterns dengan baik
2. Training data untuk dates mungkin kurang
3. Date features mungkin kurang kuat

**Solution:**
- Add more date-specific features
- Increase training data for dates
- Improve date pattern recognition

---

### **Problem 2: issue_place - CRF Tidak Dipilih Meski Confidence Tinggi**

**issue_place:**
- CRF: 0.8265 (TINGGI!)
- Rule-based: 0.6700 (lebih rendah)
- **Chosen:** Rule-based ❌

**Possible Causes:**

**A. Historical Performance Bias**
- Jika rule-based punya historical accuracy sangat tinggi
- Bisa override CRF meski confidence lebih rendah

**B. Bug di Hybrid Strategy**
- Mungkin ada logic error di `_combine_strategy_results`
- Perlu debug lebih lanjut

**C. Extraction Order Issue**
- Mungkin CRF result tidak masuk ke scoring
- Atau ter-filter sebelum scoring

---

## 💡 **Recommendations**

### **1. Increase CRF Weight (DONE ✅)**

User sudah ubah dari 0.7 → 0.8:
```python
self.strategy_weights[StrategyType.CRF] = 0.8
```

**Impact:**
- CRF score naik ~0.03
- Masih belum cukup untuk date fields dengan confidence rendah

---

### **2. Fix CRF Confidence untuk Date Fields**

**Option A: Improve Date Features**
```python
# Add more date-specific features
features['is_month_name'] = word in ['January', 'February', ...]
features['is_year'] = word.isdigit() and len(word) == 4
features['date_pattern'] = re.match(r'\d{1,2}', word) is not None
```

**Option B: Increase Training Data**
- Generate more documents with varied date formats
- Ensure feedback includes date corrections

**Option C: Post-process Date Confidence**
- If extracted value matches date pattern, boost confidence
```python
if is_date_field and matches_date_pattern(value):
    confidence = min(confidence * 1.2, 1.0)
```

---

### **3. Debug issue_place Case**

**Add detailed logging:**
```python
# In _combine_strategy_results
for strategy_type, field_value in valid_results:
    print(f"  {strategy_type.value}:")
    print(f"    Confidence: {field_value.confidence:.4f}")
    print(f"    Weight: {strategy_weight:.4f}")
    print(f"    Performance: {performance_score:.4f}")
    print(f"    Combined: {combined_score:.4f}")
```

**Check:**
1. Apakah CRF result masuk ke `valid_results`?
2. Apakah scoring calculation benar?
3. Apakah ada override logic yang triggered?

---

### **4. Adjust Scoring Formula**

**Current:**
```
40% confidence + 30% weight + 30% performance
```

**Proposed:**
```
50% confidence + 35% weight + 15% performance
```

**Rationale:**
- Confidence should matter more (actual extraction quality)
- Weight reflects our trust in strategy (CRF = 0.8)
- Performance is historical, less relevant for current extraction

**Impact:**
- CRF dengan confidence tinggi akan lebih sering dipilih
- Historical bias berkurang

---

### **5. Remove Override Logic (Optional)**

**Current override:**
```python
if result.confidence > best_result.confidence + 0.1:
    # Override to higher confidence
```

**Issue:**
- Bisa override CRF yang sudah menang di scoring
- Mengabaikan strategy weight dan performance

**Proposed:**
- Remove override logic
- Trust the scoring formula
- Atau adjust threshold dari 0.1 → 0.2

---

## 🎯 **Immediate Actions**

### **Priority 1: Debug issue_place Case** 🔴

**Why:** CRF punya confidence 0.8265 tapi tidak dipilih!

**Action:**
1. Add logging di `_combine_strategy_results`
2. Trace document 298 extraction dengan logging
3. Identify exact reason

**Expected Time:** 15 minutes

---

### **Priority 2: Improve Date Confidence** 🟡

**Why:** CRF confidence untuk dates terlalu rendah (0.51)

**Action:**
1. Add date-specific features
2. Or boost confidence for date patterns
3. Retrain model

**Expected Time:** 30 minutes

---

### **Priority 3: Adjust Scoring Formula** 🟢

**Why:** Confidence should matter more than historical performance

**Action:**
1. Change to 50% confidence, 35% weight, 15% performance
2. Test on 10 documents
3. Compare results

**Expected Time:** 20 minutes

---

## 📊 **Expected Impact**

**After fixes:**

```
Current accuracy: 86.67%

After Priority 1 (fix issue_place bug): +2-3% → 88-89%
After Priority 2 (improve date conf):   +3-5% → 91-94%
After Priority 3 (adjust formula):      +1-2% → 92-96%

Target: 90-95% accuracy ✅
```

---

## 🔍 **Next Steps**

1. ✅ User sudah increase CRF weight (0.7 → 0.8)
2. ⏳ Debug issue_place case dengan logging
3. ⏳ Improve CRF confidence untuk date fields
4. ⏳ Consider adjusting scoring formula
5. ⏳ Test dan verify improvements

---

**Date:** 2025-11-08  
**Status:** Analysis Complete - Awaiting fixes  
**Priority:** Debug issue_place case first (unexpected behavior)
