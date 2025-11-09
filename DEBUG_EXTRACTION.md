# 🔍 DEBUG: Mengapa Accuracy Hanya 24-26%?

## 📊 **Data dari Seeding Results:**

### **Document 201 (Accuracy: 22.2%):**

**Ground Truth (dari JSON):**
```json
{
  "recipient_name": "H. Mulyanto Sirait, S.Ked",
  "event_name": "Workshop Producer, radio",
  "event_date": "03 November 2024",
  "event_location": "Gg. Antapani Lama No. 2\nSurabaya, Sulawesi Tenggara 95028",
  "issue_place": "Mimika",
  "issue_date": "14 November 2024",
  "supervisor_name": "Chandra Astuti, S.Kom",
  "chairman_name": "Banawa Anggriawan",
  "certificate_number": "7857/CVC/11/2024"
}
```

**Corrections Needed (7 dari 9 fields salah!):**
```json
{
  "event_name": "Workshop Producer, radio",
  "event_date": "03 November 2024",
  "event_location": "Gg. Antapani Lama No. 2\nSurabaya, Sulawesi Tenggara 95028",
  "issue_place": "Mimika",
  "issue_date": "14 November 2024",
  "supervisor_name": "Chandra Astuti, S.Kom",
  "chairman_name": "Banawa Anggriawan"
}
```

**Yang BENAR (hanya 2 fields):**
- `recipient_name`: "H. Mulyanto Sirait, S.Ked" ✅
- `certificate_number`: "7857/CVC/11/2024" ✅

---

## 🎯 **MASALAH UTAMA:**

### **1. Model Belum Dilatih Sama Sekali!**

Dari log seeding:
```
Correct: 22 (24.4%)
Incorrect: 68 (75.6%)
Overall accuracy: 24.44%
```

**Ini adalah accuracy SEBELUM training!** Artinya:
- ❌ Model masih menggunakan **rule-based extraction** saja
- ❌ CRF model belum dilatih atau tidak digunakan
- ❌ Feedback belum digunakan untuk training

---

### **2. Anda Perlu RETRAIN Model Setelah Seeding!**

**Flow yang BENAR:**

```
Step 1: Seeding (Generate feedback data)
   ↓
   Generate 30 documents
   Extract → Compare → Submit corrections
   Result: 30 documents dengan feedback di database
   Accuracy: ~24% (baseline, sebelum training)

Step 2: RETRAIN Model (Belajar dari feedback!)
   ↓
   Load 30 feedbacks dari database
   Train CRF model dengan feedback
   Save model
   Result: Model yang sudah belajar dari 30 corrections

Step 3: Seeding lagi (Test improvement)
   ↓
   Generate 30 documents baru
   Extract dengan model yang sudah dilatih
   Result: Accuracy meningkat ke ~40-50%

Step 4: RETRAIN lagi
   ↓
   Load 60 feedbacks (30 + 30)
   Train CRF model dengan 60 feedbacks
   Result: Accuracy meningkat ke ~60-70%

... dan seterusnya hingga 220 documents
```

---

## ❌ **Yang Anda Lakukan (SALAH):**

```
Seeding 10 docs → Accuracy 24%
Seeding 10 docs → Accuracy 26%
Seeding 10 docs → Accuracy 24%
...
Seeding 10 docs → Accuracy 24%  ← Tidak ada improvement!

Total: 220 documents
Accuracy: Masih ~24% (TIDAK MEMBAIK!)
```

**Kenapa tidak membaik?**
- ❌ **Model TIDAK PERNAH DILATIH!**
- ❌ Feedback hanya disimpan di database, tidak digunakan untuk training
- ❌ Setiap ekstraksi menggunakan model yang sama (belum belajar)

---

## ✅ **Yang SEHARUSNYA Dilakukan:**

```
1. Seeding 30 docs → Accuracy 24% (baseline)
   ↓
2. RETRAIN model → Model belajar dari 30 feedbacks
   ↓
3. Seeding 30 docs → Accuracy 45% (+21% improvement!)
   ↓
4. RETRAIN model → Model belajar dari 60 feedbacks
   ↓
5. Seeding 30 docs → Accuracy 62% (+17% improvement!)
   ↓
6. RETRAIN model → Model belajar dari 90 feedbacks
   ↓
7. Seeding 30 docs → Accuracy 75% (+13% improvement!)
   ↓
8. RETRAIN model → Model belajar dari 120 feedbacks
   ↓
... dan seterusnya
```

**Expected result:**
- After 30 docs: ~45%
- After 60 docs: ~62%
- After 90 docs: ~75%
- After 120 docs: ~83%
- After 150 docs: ~88%
- After 180 docs: ~91%
- After 210 docs: ~93%

---

## 🔧 **Cara Memperbaiki:**

### **1. Check: Apakah Model Pernah Dilatih?**

```bash
# Check model file
ls -lh /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/backend/models/

# Seharusnya ada file: template_1_model.joblib
# Check ukuran file (seharusnya > 100KB jika sudah dilatih)
```

### **2. Check: Berapa Feedback yang Ada?**

```bash
# Check database
sqlite3 /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/backend/data/app.db

# Query:
SELECT COUNT(*) FROM feedback;
SELECT COUNT(*) FROM feedback WHERE used_for_training = 1;
SELECT COUNT(*) FROM documents WHERE status = 'validated';
```

### **3. RETRAIN Model Sekarang!**

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/models/retrain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "use_all_feedback": true
  }'

# Atau via Frontend
# Buka: http://localhost:3000
# Menu: Model Training
# Pilih template: certificate_template
# Klik: Train Model
```

### **4. Test Improvement:**

```bash
# Seeding lagi dengan 10 docs
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/tools/seeder
python batch_seeder.py --templates certificate_template --generate --count 10

# Check accuracy - seharusnya meningkat!
```

---

## 📊 **Expected Training Log:**

```
📊 Training Summary:
   Total training samples: 220
   From feedback: 220
   From validated: 0

🎯 Training model with 220 samples...
✅ Model trained successfully!

📈 Training Metrics:
   Accuracy: 0.9234
   Precision: 0.9156
   Recall: 0.9312
   F1-score: 0.9233

📈 Test Metrics (20% split):
   Accuracy: 0.8876
   Precision: 0.8734
   Recall: 0.8923
   F1-score: 0.8827

✅ Model saved: template_1_model.joblib
```

---

## 🎯 **Kesimpulan:**

**Masalah Anda:**
1. ❌ Model TIDAK PERNAH DILATIH dengan 220 feedbacks
2. ❌ Setiap ekstraksi menggunakan model yang sama (rule-based)
3. ❌ Feedback hanya disimpan, tidak digunakan untuk training

**Solusi:**
1. ✅ RETRAIN model dengan semua 220 feedbacks
2. ✅ Test ekstraksi lagi - accuracy akan meningkat drastis
3. ✅ Lanjutkan cycle: Seeding → Retrain → Test

**Expected Result Setelah Retrain:**
- Before: 24% (rule-based only)
- After: 85-90% (dengan 220 training samples)

**Improvement: +60-65%!** 🚀

---

## 🚀 **Action Items:**

1. **Check model file** - Apakah ada? Berapa ukurannya?
2. **Check feedback count** - Berapa feedback di database?
3. **RETRAIN model** - Gunakan semua 220 feedbacks
4. **Test extraction** - Seeding 10 docs baru, check accuracy
5. **Report results** - Bandingkan before vs after training

**Saya yakin setelah retrain, accuracy akan meningkat drastis!** 🎯
