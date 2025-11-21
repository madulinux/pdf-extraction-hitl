# Experiment Scripts

Scripts untuk menjalankan eksperimen baseline dan adaptive learning sesuai dengan desain tesis.

## 📁 Struktur

```
experiments/
├── README.md                    # Dokumentasi ini
├── upload_documents.py          # Upload dokumen dengan experiment_phase
├── prepare_ground_truth.py      # Prepare ground truth dari validated docs
├── run_baseline.py              # Evaluasi Fase 1: Baseline
├── run_adaptive.py              # Jalankan Fase 2: Adaptive Learning
├── compare_experiments.py       # Bandingkan baseline vs adaptive
├── generator/                   # Document generator (dari seeder)
│   ├── main.py
│   └── utils/
└── results/                     # Hasil eksperimen
    ├── baseline_template_1.json
    ├── adaptive_template_1.json
    ├── learning_curve_1.json
    ├── comparison_template_1.json
    └── visualization_data_1.json
```

---

## 🚀 Workflow Lengkap

### **FASE 0: Persiapan**

#### 1. Reset Environment

```bash
cd backend

# Set AUTO_TRAINING=False untuk baseline
echo "AUTO_TRAINING=False" > .env

# Hapus model CRF (jika ada)
rm -f models/template_1_model.joblib

# (Optional) Reset database untuk fresh start
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.init_database()"
```

#### 2. Generate Dokumen PDF

```bash
cd experiments/generator

# Generate 25 dokumen per template
python main.py generate-documents --count 25 --template letter_template

# Output: storage/output/letter_template/*.pdf
```

---

### **FASE 1: BASELINE EXPERIMENT**

**Tujuan:** Mengukur performa awal sistem dengan rule-based ONLY (tanpa CRF)

#### Step 1.1: Upload Dokumen Baseline

```bash
cd backend

# Upload 25 dokumen dengan experiment_phase='baseline'
python experiments/upload_documents.py \
  --template-id 1 \
  --folder experiments/generator/storage/output/letter_template \
  --experiment-phase baseline \
  --limit 25

# ✅ Output:
# - 25 dokumen di database dengan experiment_phase='baseline'
# - Ekstraksi menggunakan rule-based ONLY (karena model tidak ada)
```

#### Step 1.2: Prepare Ground Truth

```bash
# Prepare ground truth dari hasil ekstraksi + manual validation
# Ground truth = extraction_result + corrections (jika ada)
python experiments/prepare_ground_truth.py \
  --template-id 1 \
  --experiment-phase baseline

# ✅ Output: data/ground_truth/1.json, 2.json, ..., 25.json
```

**Catatan:** Ground truth bisa dibuat dengan 2 cara:
- **Cara 1:** Manual validation → Koreksi via UI → Export sebagai ground truth
- **Cara 2:** Gunakan JSON generator (ground truth sudah ada dari awal)

#### Step 1.3: Evaluasi Baseline

```bash
# Evaluasi baseline performance
python experiments/run_baseline.py --template-id 1

# ✅ Output: experiments/results/baseline_template_1.json
```

**Hasil Fase 1:**
```json
{
  "phase": "baseline",
  "baseline_accuracy": 0.60,
  "strategy": "rule_based",
  "total_documents": 25,
  "field_accuracy": {...}
}
```

---

### **FASE 2: ADAPTIVE LEARNING EXPERIMENT**

**Tujuan:** Mengukur peningkatan performa dengan incremental learning

#### Step 2.1: Enable Auto-Training

```bash
# Set AUTO_TRAINING=True
echo "AUTO_TRAINING=True" > .env
```

#### Step 2.2: Upload Dokumen Adaptive

```bash
# Upload 25 dokumen yang SAMA dengan experiment_phase='adaptive'
python experiments/upload_documents.py \
  --template-id 1 \
  --folder experiments/generator/storage/output/letter_template \
  --experiment-phase adaptive \
  --limit 25

# ✅ Output:
# - 25 dokumen BARU di database dengan experiment_phase='adaptive'
# - Menggunakan FILE yang SAMA dari baseline
# - Ekstraksi awal masih rule-based (model belum ada)
```

#### Step 2.3: Jalankan Adaptive Learning

```bash
# Simulate feedback bertahap + auto-training + re-ekstraksi
python experiments/run_adaptive.py \
  --template-id 1 \
  --batch-size 5

# Proses:
# Batch 1 (doc 1-5):
#   → Simulate feedback (compare with ground truth)
#   → Trigger auto-training (5 docs threshold)
#   → Train CRF model (v1)
#   → Re-ekstraksi ALL 25 docs dengan hybrid
#   → Evaluasi → A_1 = 65%
#
# Batch 2 (doc 6-10):
#   → Simulate feedback
#   → Auto-training
#   → Retrain CRF (v2)
#   → Re-ekstraksi ALL 25 docs
#   → Evaluasi → A_2 = 70%
#
# ... continue until batch 5 (doc 21-25)
#
# Batch 5:
#   → Simulate feedback
#   → Auto-training
#   → Retrain CRF (v5)
#   → Re-ekstraksi ALL 25 docs
#   → Evaluasi → A_5 = 85%

# ✅ Output:
# - experiments/results/adaptive_template_1.json
# - experiments/results/learning_curve_1.json
```

**Hasil Fase 2:**
```json
{
  "phase": "adaptive",
  "initial_accuracy": 0.60,
  "final_accuracy": 0.85,
  "improvement": 0.25,
  "improvement_percentage": 41.7,
  "total_batches": 5,
  "learning_curve": [
    {"batch": 0, "accuracy": 0.60},
    {"batch": 1, "accuracy": 0.65},
    {"batch": 2, "accuracy": 0.70},
    {"batch": 3, "accuracy": 0.75},
    {"batch": 4, "accuracy": 0.80},
    {"batch": 5, "accuracy": 0.85}
  ]
}
```

---

### **FASE 3: ANALISIS DAN PERBANDINGAN**

```bash
# Bandingkan baseline vs adaptive
python experiments/compare_experiments.py --template-id 1

# ✅ Output:
# - experiments/results/comparison_template_1.json
# - experiments/results/visualization_data_1.json (untuk chart)
```

**Hasil Perbandingan:**
```
📊 EXPERIMENT COMPARISON
======================================================================
📈 ACCURACY COMPARISON
----------------------------------------------------------------------
Baseline (Rule-based):        60.00%
Adaptive Initial:             60.00%
Adaptive Final (Hybrid):      85.00%

Improvement:                  25.00% (+41.7%)

📉 LEARNING CURVE
----------------------------------------------------------------------
Batch      Documents       Accuracy        Improvement    
----------------------------------------------------------------------
0          0               60.00%          +0.00%         
1          5               65.00%          +5.00%         
2          10              70.00%          +10.00%        
3          15              75.00%          +15.00%        
4          20              80.00%          +20.00%        
5          25              85.00%          +25.00%        
```

---

## 📊 Dashboard dengan Filter Phase

Dashboard dapat menampilkan metrics untuk setiap fase:

```bash
# Production (default)
GET /api/v1/learning/performance/1

# Baseline experiment
GET /api/v1/learning/performance/1?phase=baseline

# Adaptive experiment
GET /api/v1/learning/performance/1?phase=adaptive

# All data
GET /api/v1/learning/performance/1?phase=all
```

## Experiment Phases

### Baseline Phase
- `experiment_phase = 'baseline'`
- Ekstraksi menggunakan rule-based ONLY
- Tidak ada CRF model
- Evaluasi menggunakan Ground Truth

### Adaptive Phase
- `experiment_phase = 'adaptive'`
- Ekstraksi menggunakan hybrid (rule + CRF)
- Model dilatih dari feedback
- Evaluasi menggunakan Ground Truth

### Production
- `experiment_phase = NULL`
- Normal production documents
- Default behavior

## Dashboard

Dashboard dapat toggle antara:
- Production: `GET /api/v1/learning/performance/1`
- Baseline: `GET /api/v1/learning/performance/1?phase=baseline`
- Adaptive: `GET /api/v1/learning/performance/1?phase=adaptive`
- All: `GET /api/v1/learning/performance/1?phase=all`
