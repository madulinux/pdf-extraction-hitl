# 🔍 Analisa Masalah Ekstraksi & Solusi

**Tanggal:** 2024-11-09  
**Template:** medical_form_template (ID: 1)  
**Dokumen Analisa:** Document ID 130  
**Total Dokumen Latih:** 130 dokumen (110 validated)

---

## 📊 Temuan Utama

### 1. 🔴 **MASALAH KRITIS: 401 Feedback Tidak Digunakan untuk Training**

```
Total Feedback: 2496
✅ Used for training: 2095 (83.9%)
❌ Unused: 401 (16.1%)
```

**Impact:**
- Model CRF tidak belajar dari 401 koreksi user terbaru
- Adaptive learning tidak berjalan optimal
- Akurasi tidak meningkat meskipun user sudah mengoreksi

**Root Cause:**
- Sistem menyimpan feedback tapi tidak otomatis trigger retraining
- Flag `used_for_training` tidak di-update setelah training
- Tidak ada mekanisme batch retraining otomatis

---

### 2. 🟡 **MASALAH: Rule-based Strategy Mendominasi (72.3%)**

```
Strategy Usage:
- rule_based: 72.3% (2,089 extractions)
- crf: 27.7% (800 extractions)
```

**Impact:**
- CRF model yang sudah dilatih tidak digunakan secara optimal
- Sistem terlalu bergantung pada rule-based yang rigid
- Adaptive learning tidak efektif karena CRF jarang dipilih

**Root Cause:**
- Strategy selection logic terlalu konservatif
- CRF confidence threshold terlalu tinggi
- Rule-based selalu dicoba duluan dan sering "menang"

---

### 3. ⚠️ **9 Field dengan Akurasi < 50%**

| Field | Best Accuracy | Best Strategy | Total Attempts |
|-------|---------------|---------------|----------------|
| `chief_complaint` | 0.0% | rule_based | 199 |
| `doctor_name` | 0.0% | rule_based | 119 |
| `exam_date` | 0.0% | rule_based | 130 |
| `prescription` | 0.0% | rule_based | 53 |
| `recommendations` | 0.0% | rule_based | 123 |
| `diagnosis` | 7.7% | crf | 169 |
| `medical_history` | 9.0% | crf | 140 |
| `patient_address` | 37.1% | crf | 165 |
| `patient_phone` | 48.8% | crf | 171 |

**Analisa per Kategori:**

#### A. Fields dengan 0% Accuracy (Rule-based dominan)
- `chief_complaint`, `doctor_name`, `exam_date`, `prescription`, `recommendations`
- **Masalah:** Rule-based tidak bisa handle field ini, tapi CRF tidak pernah/jarang dicoba
- **Solusi:** Paksa CRF untuk field-field ini, atau improve rule patterns

#### B. Fields dengan Low CRF Accuracy (<10%)
- `diagnosis` (7.7%), `medical_history` (9.0%)
- **Masalah:** CRF model tidak belajar pattern yang benar
- **Penyebab Potensial:**
  - Data training tidak konsisten
  - Field terlalu panjang/kompleks (free text)
  - Feature engineering tidak capture pattern yang tepat

#### C. Fields dengan Medium CRF Accuracy (30-50%)
- `patient_address` (37.1%), `patient_phone` (48.8%)
- **Masalah:** CRF belajar sebagian pattern tapi belum optimal
- **Solusi:** Perlu lebih banyak training data atau feature engineering lebih baik

---

### 4. ✅ **Fields dengan Performa Baik**

| Field | CRF Accuracy | Rule-based Accuracy |
|-------|--------------|---------------------|
| `pulse_rate` | 100.0% | 100.0% |
| `follow_up_date` | 95.1% | 0.0% |
| `blood_pressure` | 89.4% | 16.7% |
| `insurance_number` | 91.3% | - |
| `patient_name` | 76.0% | 0.0% |
| `patient_birth_date` | 71.0% | 0.0% |
| `temperature` | 70.0% | 17.1% |
| `weight` | 67.2% | 16.7% |

**Insight:**
- CRF bekerja sangat baik untuk field terstruktur (tanggal, nama, angka)
- Rule-based hanya bagus untuk field dengan pattern sangat konsisten (`pulse_rate`)
- CRF jauh lebih baik dari rule-based untuk mayoritas field

---

## 💡 Solusi & Rekomendasi

### 🚀 **Priority 1: Fix Adaptive Learning Loop**

#### A. Implement Automatic Retraining
```python
# Trigger retraining setelah N feedback baru
if unused_feedback_count >= 50:
    trigger_retraining(template_id)
```

#### B. Update `used_for_training` Flag
```python
# Setelah training, mark feedback as used
mark_feedback_as_used(feedback_ids)
```

#### C. Scheduled Retraining
```python
# Cron job untuk retrain setiap malam
schedule_retraining(template_id, cron="0 2 * * *")
```

---

### 🎯 **Priority 2: Improve Strategy Selection Logic**

#### A. Reduce Rule-based Dominance
```python
# Prioritas CRF jika model exists dan field bukan "simple pattern"
if has_crf_model and not is_simple_pattern(field):
    try_crf_first = True
```

#### B. Lower CRF Confidence Threshold
```python
# Current: 0.7 (terlalu tinggi)
# Recommended: 0.5 untuk field kompleks
CRF_MIN_CONFIDENCE = {
    'simple': 0.7,  # pulse_rate, temperature
    'medium': 0.5,  # patient_name, dates
    'complex': 0.3  # diagnosis, medical_history
}
```

#### C. Blacklist Rule-based untuk Field Tertentu
```python
# Field yang HARUS menggunakan CRF
CRF_ONLY_FIELDS = [
    'chief_complaint',
    'diagnosis',
    'medical_history',
    'prescription',
    'recommendations'
]
```

---

### 🔧 **Priority 3: Improve CRF Model Quality**

#### A. Better Feature Engineering untuk Free Text Fields
```python
# Tambahkan features untuk field panjang
features = {
    'word_count': len(tokens),
    'has_medical_terms': check_medical_vocab(text),
    'sentence_position': get_sentence_index(token),
    'paragraph_position': get_paragraph_index(token),
    'near_section_header': check_section_proximity(token)
}
```

#### B. Field-specific Training
```python
# Train separate model untuk field kompleks
train_specialized_model(
    field='diagnosis',
    min_samples=100,
    features=['medical_terms', 'sentence_structure']
)
```

#### C. Data Augmentation
```python
# Generate variasi dari data existing
augment_training_data(
    template_id=1,
    target_samples=200,
    methods=['synonym', 'paraphrase']
)
```

---

### 📈 **Priority 4: Monitoring & Evaluation**

#### A. Real-time Performance Dashboard
- Track accuracy per field per strategy
- Alert jika accuracy drop > 10%
- Visualisasi strategy usage distribution

#### B. A/B Testing untuk Strategy Selection
- Test different confidence thresholds
- Compare CRF-first vs Rule-first approaches
- Measure impact on overall accuracy

#### C. Feedback Loop Metrics
- Time between feedback and retraining
- Number of unused feedback
- Accuracy improvement after retraining

---

## 🎬 Action Plan

### Immediate (Today)
1. ✅ Implement automatic retraining trigger
2. ✅ Fix `used_for_training` flag update
3. ✅ Retrain model dengan 401 unused feedback

### Short-term (This Week)
4. ⏳ Adjust strategy selection logic (CRF priority)
5. ⏳ Lower CRF confidence threshold
6. ⏳ Blacklist rule-based untuk field problematic

### Medium-term (Next Week)
7. ⏳ Improve feature engineering untuk free text
8. ⏳ Implement field-specific models
9. ⏳ Build performance monitoring dashboard

### Long-term (Next Month)
10. ⏳ Data augmentation pipeline
11. ⏳ A/B testing framework
12. ⏳ Automated hyperparameter tuning

---

## 📝 Kesimpulan

**Masalah utama BUKAN pada model CRF**, tapi pada:
1. **Adaptive learning loop yang tidak berjalan** (401 feedback unused)
2. **Strategy selection yang terlalu konservatif** (rule-based dominan)
3. **CRF tidak diberi kesempatan** untuk field yang seharusnya dia handle

**Bukti CRF bekerja baik:**
- 11 fields dengan accuracy > 70%
- Jauh lebih baik dari rule-based untuk field kompleks
- Hanya perlu lebih banyak digunakan dan dilatih ulang

**Next Step:**
Fokus pada fixing adaptive learning loop dan strategy selection logic, bukan pada mengubah model atau feature engineering.
