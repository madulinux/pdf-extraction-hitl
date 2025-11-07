# 🌱 Automated Seeder untuk BAB 4

Automated seeder untuk mempercepat pembuatan dataset evaluasi BAB 4 dengan mengikuti alur kerja normal sistem (Upload Template → Upload Document → Correction → Validation).

## 📋 Features

✅ **Automated workflow**: Template upload → Document extraction → Auto-correction → Validation  
✅ **Ground truth comparison**: Otomatis compare hasil ekstraksi dengan ground truth JSON  
✅ **Batch processing**: Seed multiple templates sekaligus  
✅ **Statistics tracking**: Track accuracy, corrections, dan performa per template  
✅ **Realistic simulation**: Mengikuti alur UI yang sebenarnya

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Pastikan backend sudah running
cd backend
python app.py

# Setup authentication (create admin user)
cd tools/seeder
python setup_auth.py

# Pastikan sudah ada generated documents
cd ../cmd
python main.py generate-documents --count 40
```

### 2. Seed Single Template

```bash
cd tools/seeder

# Seed certificate template (40 docs) - uses default admin/admin123
python automated_seeder.py --template certificate_template --count 40

# Seed invoice template (30 docs)
python automated_seeder.py --template invoice_template --count 30

# With custom credentials
python automated_seeder.py --template certificate_template --count 40 \
  --username myuser --password mypass
```

### 3. Seed All Templates (Batch)

```bash
# Seed all templates dengan default counts
python batch_seeder.py --all

# Generate documents dulu, lalu seed
python batch_seeder.py --all --generate --count 30

# Seed specific templates only
python batch_seeder.py --templates certificate_template invoice_template --count 30
```

---

## 📊 Template Configurations

| Template | Default Count | Priority | Description |
|----------|---------------|----------|-------------|
| `certificate_template` | 40 | 1 | Sertifikat Pelatihan (sudah ada) |
| `invoice_template` | 30 | 2 | Invoice/Faktur |
| `contract_template` | 30 | 3 | Kontrak Kerja |
| `job_application_template` | 20 | 4 | Lamaran Kerja |
| `medical_form_template` | 20 | 5 | Form Medis |

**Total:** 140 documents across 5 templates

---

## 🔄 Workflow Detail

### Automated Seeder Flow:

```
1. Upload Template PDF
   ↓
2. System analyzes template → template_id
   ↓
3. For each generated document:
   a. Load ground truth JSON
   b. Upload PDF for extraction
   c. Compare extracted_data vs ground_truth
   d. Generate corrections (only different fields)
   e. Submit corrections via API
   f. Mark as validated
   ↓
4. Generate statistics & summary
```

### Example Output:

```
🚀 Starting automated seeding for: certificate_template
📊 Target documents: 40

📤 Uploading template: certificate_template
✅ Template uploaded successfully. ID: 1

📄 Processing document 1/40: 2025-11-07_201526_673401_0.pdf
🔍 Extracting document: 2025-11-07_201526_673401_0.pdf
✅ Extraction complete. Document ID: 1
  ✅ certificate_number: Correct
  ✅ recipient_name: Correct
  ❌ event_location: 'Sorong' → 'Gang Rawamangun No. 70, Sorong'
  ❌ supervisor_name: 'Tedi' → 'R. Tedi Yuliarti, S.IP'
📝 Submitting 2 corrections for document 1
✅ Corrections submitted successfully

...

📊 SEEDING SUMMARY
======================================================================
Template: certificate_template
Template ID: 1
Documents processed: 40/40
Failed: 0

Field Statistics:
  Total fields: 360
  Correct: 250 (69.4%)
  Incorrect: 110 (30.6%)
  Overall accuracy: 69.44%

Time elapsed: 120.50 seconds
Avg time per document: 3.01 seconds
======================================================================
```

---

## 📈 Use Cases untuk BAB 4

### Scenario 1: Evaluasi Baseline (Single Template)

```bash
# Seed certificate template dengan 40 docs
python automated_seeder.py --template certificate_template --count 40

# Hasil: 40 validated documents dengan ground truth
# Gunakan untuk Section 4.2.1 - Evaluasi Akurasi Ekstraksi
```

### Scenario 2: Comparative Analysis (Multiple Templates)

```bash
# Seed 3 templates untuk comparative analysis
python batch_seeder.py --templates certificate_template invoice_template contract_template --count 30

# Hasil: 90 documents across 3 different template types
# Gunakan untuk Section 4.3.1 - Perbandingan Antar Template
```

### Scenario 3: Complete Dataset (All Templates)

```bash
# Generate & seed all templates
python batch_seeder.py --all --generate

# Hasil: 140 documents across 5 templates
# Gunakan untuk comprehensive evaluation di BAB 4
```

---

## 🎯 Advantages

### vs Manual Input:

| Aspect | Manual | Automated Seeder | Improvement |
|--------|--------|------------------|-------------|
| **Time per doc** | ~3-5 min | ~3 sec | **60-100x faster** |
| **40 docs** | ~2-3 hours | ~2 minutes | **60-90x faster** |
| **Accuracy** | Human error | 100% consistent | Perfect ground truth |
| **Reproducibility** | Hard | Easy | Re-run anytime |

### Benefits:

✅ **Mempercepat pembuatan dataset** - 40 docs dalam 2 menit vs 2-3 jam manual  
✅ **Ground truth akurat** - Langsung dari generator, no human error  
✅ **Reproducible** - Bisa re-run kapan saja dengan hasil konsisten  
✅ **Realistic simulation** - Mengikuti alur UI yang sebenarnya  
✅ **Statistics tracking** - Auto-generate metrics untuk BAB 4  

---

## 🔧 Advanced Usage

### Custom API URL

```bash
# If backend running on different port
python automated_seeder.py --template certificate_template --count 40 --api-url http://localhost:8000/api/v1
```

### Generate Documents with Microsoft Word

```bash
# Use Word instead of LibreOffice (faster, more stable)
python batch_seeder.py --all --generate --use-word
```

### Seed Specific Count

```bash
# Override default counts
python batch_seeder.py --all --count 50
```

---

## 📁 Output Files

### Generated by Seeder:

```
tools/seeder/results/
└── batch_seeding_20251107_203045.json  # Detailed results
```

### In Database:

```sql
-- Templates
SELECT * FROM templates;  -- 5 templates

-- Documents
SELECT * FROM documents WHERE status='validated';  -- 140 validated docs

-- Feedback (corrections)
SELECT * FROM feedback;  -- All corrections tracked

-- Extraction results
SELECT * FROM documents;  -- All extraction_result JSON
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused"

```bash
# Make sure backend is running
cd backend
python app.py
```

### Issue: "No documents found"

```bash
# Generate documents first
cd tools/cmd
python main.py generate-documents --count 40
```

### Issue: "Template upload failed"

```bash
# Check if template PDF exists
ls tools/cmd/storage/templates/pdf/

# Convert DOCX to PDF if needed
cd tools/cmd
python main.py generate-documents --count 1
```

---

## 📊 Expected Results untuk BAB 4

### Dengan 2 Templates (Minimum):

- **Certificate**: 40 docs → Section 4.2.1 (Baseline)
- **Invoice**: 30 docs → Section 4.3.1 (Comparative)
- **Total**: 70 docs

### Dengan 3 Templates (Ideal):

- **Certificate**: 40 docs
- **Invoice**: 30 docs
- **Contract**: 30 docs
- **Total**: 100 docs

### Dengan 5 Templates (Complete):

- **All templates**: 140 docs
- **Comprehensive evaluation** untuk BAB 4

---

## 🎓 Untuk Penulisan BAB 4

### Data yang Tersedia:

1. ✅ **Ground truth** - Dari JSON generator
2. ✅ **Extraction results** - Dari sistem
3. ✅ **Corrections** - Otomatis generated
4. ✅ **Accuracy metrics** - Per template & overall
5. ✅ **Processing time** - Per document & batch

### Sections yang Bisa Ditulis:

- **4.2.1** - Evaluasi Akurasi (single template)
- **4.2.2** - Evaluasi Pembelajaran Adaptif (with feedback)
- **4.3.1** - Comparative Analysis (multiple templates)
- **4.3.2** - Performance Analysis (time, efficiency)

---

## 🚀 Next Steps

1. ✅ **Generate documents** - `python main.py generate-documents --count 40`
2. ✅ **Run seeder** - `python batch_seeder.py --all`
3. ✅ **Check results** - Review statistics & accuracy
4. ✅ **Run evaluation** - `python backend/evaluation/baseline_evaluation.py`
5. ✅ **Write BAB 4** - Use generated data & metrics

**Seeder siap digunakan! 🎉**
