# 🚀 Quick Start: Evaluation Scripts

## ✅ Status: Scripts Fixed & Ready

Kedua evaluation scripts sudah diperbaiki dan siap digunakan:
- ✅ `backend/evaluation/baseline_evaluation.py`
- ✅ `backend/evaluation/adaptive_learning_evaluation.py`

---

## ⚠️ Current Issue: No Data Available

Scripts berjalan tanpa error, tetapi **tidak ada data untuk dievaluasi**:

```
❌ No validated documents found!
❌ No documents with feedback found!
```

### Penyebab:
Database Anda saat ini tidak memiliki:
1. Documents dengan `status='validated'`
2. Documents dengan feedback (corrections)

---

## 🔧 Solusi: Populate Data

### Option 1: Gunakan Data yang Sudah Ada (Recommended)

Jika Anda sudah punya 25 dokumen yang sudah diekstrak dan divalidasi, update status mereka:

```sql
-- Check current documents
SELECT id, filename, status FROM documents WHERE template_id = 1;

-- Update status to 'validated' for documents that have been verified
UPDATE documents 
SET status = 'validated', 
    validated_at = CURRENT_TIMESTAMP
WHERE template_id = 1 
  AND extraction_result IS NOT NULL;
```

**Cara menjalankan SQL:**
```bash
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/backend
sqlite3 data/app.db

# Paste SQL commands above
# Exit: .exit
```

### Option 2: Extract & Validate New Documents

1. **Upload & Extract Documents:**
   - Start backend: `cd backend && python app.py`
   - Start frontend: `cd frontend && npm run dev`
   - Upload 25 dokumen via UI
   - Extract semua dokumen

2. **Validate & Correct:**
   - Review extraction results
   - Submit corrections untuk beberapa dokumen (minimal 5-10)
   - Validate dokumen yang sudah benar

3. **Run Evaluation:**
   ```bash
   python backend/evaluation/baseline_evaluation.py
   python backend/evaluation/adaptive_learning_evaluation.py
   ```

---

## 📊 Expected Output (When Data Available)

### Baseline Evaluation:
```
📊 BASELINE EVALUATION - Overall Performance
✅ Found 25 validated documents

📈 Overall Metrics:
   Total Documents: 25
   Total Fields Evaluated: 225
   Accuracy:  0.9815 (98.15%)
   Precision: 0.9732 (97.32%)
   Recall:    0.9866 (98.66%)
   F1-Score:  0.9796 (97.96%)

📈 Per-Field Metrics:
field_name           total  correct  incorrect  accuracy  precision  recall  f1_score
certificate_number      25       25          0      1.00       1.00    1.00      1.00
recipient_name          25       24          1      0.96       0.96    0.96      0.96
...
```

### Adaptive Learning Evaluation:
```
📊 ADAPTIVE LEARNING EVALUATION - Incremental Learning
✅ Found 25 documents with feedback

📈 Learning Curve Summary:
iteration  num_training_docs  num_test_docs  accuracy  f1_score  improvement
        1                  5              5      0.75      0.73         0.00
        2                 10              5      0.85      0.83         0.10
        3                 15              5      0.92      0.90         0.07
        4                 20              5      0.96      0.94         0.04
        5                 25              0      0.98      0.96         0.02

✅ Model converged at:
   Iteration: 5
   Training Documents: 25
   Accuracy: 0.98 (98%)
```

---

## 📁 Output Files

Setelah evaluation berhasil, Anda akan mendapatkan:

```
backend/evaluation/results/
├── baseline_evaluation_summary.json
├── per_field_metrics.csv
├── confusion_matrix.png
├── learning_curve.csv
├── learning_curve.png
├── training_mode_comparison.csv
├── training_mode_comparison.png
└── adaptive_learning_evaluation_summary.json
```

---

## 🎯 Next Steps for BAB 4

### 1. Populate Data (This Week)
- [ ] Validate existing documents OR
- [ ] Extract & validate 25 new documents
- [ ] Submit corrections for 5-10 documents

### 2. Run Evaluations (Week 1)
```bash
# Baseline evaluation
python backend/evaluation/baseline_evaluation.py

# Adaptive learning evaluation
python backend/evaluation/adaptive_learning_evaluation.py
```

### 3. Analyze Results (Week 1-2)
- [ ] Review generated metrics
- [ ] Analyze per-field performance
- [ ] Study learning curves
- [ ] Identify patterns & insights

### 4. Write BAB 4 (Week 2-4)
- [ ] Section 4.1: Dokumentasi Implementasi
- [ ] Section 4.2: Evaluasi Sistem (use evaluation results)
- [ ] Section 4.3: Comparative Analysis
- [ ] Section 4.4: Discussion
- [ ] Section 4.5: Validation Against Research Questions

---

## 🐛 Troubleshooting

### Issue: "No validated documents found"
**Solution:**
```sql
-- Check documents
SELECT id, filename, status, extraction_result IS NOT NULL as has_result 
FROM documents 
WHERE template_id = 1;

-- Update status
UPDATE documents 
SET status = 'validated' 
WHERE template_id = 1 
  AND extraction_result IS NOT NULL;
```

### Issue: "No documents with feedback found"
**Solution:**
```sql
-- Check feedback
SELECT COUNT(*) as feedback_count, COUNT(DISTINCT document_id) as doc_count
FROM feedback f
JOIN documents d ON f.document_id = d.id
WHERE d.template_id = 1;
```

If count is 0, you need to submit corrections via the UI.

### Issue: Scripts run but no plots generated
**Solution:** Install matplotlib if missing:
```bash
pip install matplotlib seaborn
```

---

## 📚 Reference

- **BAB4_CHECKLIST.md**: Detailed checklist & action plan
- **Evaluation Scripts**:
  - `backend/evaluation/baseline_evaluation.py`
  - `backend/evaluation/adaptive_learning_evaluation.py`
- **Database**: `backend/data/app.db`

---

**🎉 Good luck! Scripts are ready, just need data!**
