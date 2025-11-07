# Sistem Ekstraksi Data Adaptif dari Template PDF berbasis Human-in-the-Loop (HITL)

**Status:** ✅ **Production Ready (92% Complete)**  
**Version:** 2.0.0  
**Last Updated:** 5 November 2024

Sistem web untuk proposal tesis BAB 4 yang mengimplementasikan ekstraksi data adaptif dari PDF menggunakan strategi hybrid (Rule-based + Machine Learning CRF) dengan feedback loop dari pengguna.

## 🎉 Recent Updates

- ✅ **Backend 100% Restructured** - Domain-Driven Design implemented
- ✅ **Authentication System** - JWT with role-based access control
- ✅ **API v1 Complete** - 24 endpoints with standardized responses
- ✅ **Frontend 85% Complete** - Type-safe API layer with auth
- ✅ **Zero Legacy Code** - All deprecated code removed
- ✅ **14 Documentation Files** - Comprehensive guides created

## 🎯 Tujuan Sistem

1. **Analisis Template PDF** - Mengidentifikasi field yang dapat diekstraksi dari template
2. **Ekstraksi Data Hybrid** - Menggunakan rule-based dan model CRF untuk ekstraksi
3. **Validasi Human-in-the-Loop** - Pengguna memvalidasi dan mengoreksi hasil ekstraksi
4. **Pembelajaran Adaptif** - Model CRF dilatih ulang secara incremental dari feedback pengguna

## 🛠️ Technology Stack

### Backend
- **Python 3.12+** dengan **Flask** sebagai REST API framework
- **pdfplumber** - Ekstraksi teks dan koordinat dari PDF
- **pdf2image** - Rendering PDF ke gambar
- **sklearn-crfsuite** - Model Conditional Random Fields (CRF)
- **pandas, numpy, scikit-learn** - Data processing dan evaluasi
- **SQLite** - Penyimpanan metadata
- **joblib** - Serialisasi model

### Frontend
- **Next.js 16** dengan **TypeScript**
- **Tailwind CSS** - Styling
- **shadcn/ui** - Komponen UI
- **Lucide React** - Icons
- **Axios** - HTTP client

## 📁 Struktur Proyek

```
Project/
├── backend/
│   ├── app.py                      # Flask application entry point
│   ├── requirements.txt            # Python dependencies
│   ├── database/
│   │   └── db_manager.py          # SQLite database manager
│   ├── services/
│   │   ├── template_analyzer.py   # Template analysis service
│   │   ├── data_extractor.py      # Hybrid extraction service
│   │   └── adaptive_learner.py    # CRF model training service
│   ├── routes/
│   │   ├── template_routes.py     # Template API endpoints
│   │   ├── extraction_routes.py   # Extraction API endpoints
│   │   └── model_routes.py        # Model training API endpoints
│   ├── uploads/                    # Uploaded PDF files
│   ├── templates/                  # Template configurations (JSON)
│   ├── models/                     # Trained CRF models (.joblib)
│   └── feedback/                   # User feedback data (JSON)
│
└── frontend/
    ├── app/
    │   ├── page.tsx               # Main application page
    │   ├── layout.tsx             # Root layout
    │   └── globals.css            # Global styles
    ├── components/
    │   ├── TemplateUpload.tsx     # Template upload component
    │   ├── TemplateList.tsx       # Template list component
    │   ├── DocumentExtraction.tsx # Document extraction component
    │   ├── ValidationForm.tsx     # Validation & correction form (HITL)
    │   └── ModelTraining.tsx      # Model training component
    ├── lib/
    │   ├── api.ts                 # API client
    │   └── utils.ts               # Utility functions
    └── package.json
```

## 🚀 Cara Menjalankan

### 1. Setup Backend

```bash
cd backend

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate  # Di Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Jalankan Flask server
python app.py
```

Backend akan berjalan di `http://localhost:5000`

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Jalankan development server
npm run dev
```

Frontend akan berjalan di `http://localhost:3000`

## 📖 Cara Penggunaan

### 1. Upload Template PDF

1. Buka tab "Kelola Template"
2. Upload file PDF template (formulir kosong dengan marker seperti `{nama}`, `${email}`, dll)
3. Sistem akan menganalisis dan mengidentifikasi field yang dapat diekstraksi
4. Konfigurasi template akan disimpan

### 2. Ekstraksi Dokumen

1. Buka tab "Ekstraksi Data"
2. Pilih template dari daftar
3. Upload dokumen PDF yang sudah diisi
4. Sistem akan mengekstraksi data menggunakan strategi hybrid:
   - **Rule-based**: Menggunakan regex dan posisi koordinat
   - **Model-based**: Menggunakan CRF model (jika sudah dilatih)

### 3. Validasi & Koreksi (Human-in-the-Loop)

1. Periksa hasil ekstraksi yang ditampilkan
2. Koreksi nilai yang salah
3. Perhatikan confidence score untuk setiap field
4. Simpan koreksi - data akan digunakan untuk melatih model

### 4. Pelatihan Model Adaptif

1. Buka tab "Pelatihan Model"
2. Pilih template
3. Lihat statistik feedback yang tersedia
4. Klik "Latih Model" untuk melatih/melatih ulang model CRF
5. Model akan belajar dari koreksi pengguna dan meningkatkan akurasi

## 🔄 Alur Kerja Sistem

```
1. Upload Template → Analisis Field
                          ↓
2. Upload Dokumen → Ekstraksi Hybrid (Rule + Model)
                          ↓
3. Tampilkan Hasil → Validasi Pengguna (HITL)
                          ↓
4. Simpan Koreksi → Feedback Database
                          ↓
5. Latih Model → Model CRF Terupdate
                          ↓
         (Kembali ke step 2 dengan model lebih akurat)
```

## 📊 Komponen Fungsional

### 1. Template Analyzer
- Mengekstrak teks dan koordinat dari PDF template
- Mengidentifikasi marker field (`{field_name}`)
- Menganalisis konteks (label di sekitar marker)
- Menghasilkan konfigurasi JSON

### 2. Data Extractor (Hybrid)
- **Rule-based**: Regex pattern matching + posisi koordinat
- **Model-based**: CRF sequence labeling dengan BIO tagging
- Strategi hybrid: Prioritas berdasarkan confidence score

### 3. Adaptive Learner
- Konversi feedback ke format BIO tagging
- Ekstraksi fitur (lexical, orthographic, layout)
- Pelatihan incremental CRF model
- Evaluasi dengan metrics (accuracy, precision, recall, F1)

### 4. Database Manager
- SQLite untuk metadata (templates, documents, feedback)
- Tracking training history dan metrics
- File-based storage untuk konfigurasi dan model

## 🎓 Fitur Utama

✅ **Template Analysis** - Identifikasi otomatis field dari template  
✅ **Hybrid Extraction** - Kombinasi rule-based dan ML  
✅ **Human-in-the-Loop** - Validasi dan koreksi interaktif  
✅ **Adaptive Learning** - Model belajar dari feedback  
✅ **Confidence Scoring** - Indikator kualitas ekstraksi  
✅ **Training Metrics** - Monitoring performa model  
✅ **Modern UI** - Interface yang intuitif dengan shadcn/ui  

## 📝 API Endpoints

### Template
- `POST /api/template/analyze` - Analisis template PDF
- `GET /api/template/list` - Daftar semua template
- `GET /api/template/:id` - Detail template

### Extraction
- `POST /api/document/extract` - Ekstraksi dokumen
- `POST /api/document/validate` - Submit validasi/koreksi
- `GET /api/document/document/:id` - Detail dokumen

### Model
- `POST /api/model/retrain` - Latih ulang model
- `GET /api/model/training-history/:templateId` - Riwayat pelatihan
- `GET /api/model/metrics/:templateId` - Metrik model terkini
- `GET /api/model/feedback-stats/:templateId` - Statistik feedback

## 🔬 Model Machine Learning

**Conditional Random Fields (CRF)** dipilih karena:
- Cocok untuk sequence labeling tasks
- Dapat menangkap dependencies antar token
- Efisien untuk incremental learning
- Interpretable feature weights

**Fitur yang digunakan:**
- Lexical: word form, case, digits
- Orthographic: capitalization patterns
- Layout: posisi koordinat (x, y)
- Context: surrounding words

## 📈 Evaluasi Model

Metrik yang digunakan:
- **Accuracy**: Akurasi keseluruhan
- **Precision**: Ketepatan prediksi positif
- **Recall**: Kemampuan menemukan semua positif
- **F1 Score**: Harmonic mean precision dan recall

## 🤝 Kontribusi

Sistem ini dikembangkan sebagai bagian dari proposal tesis. Saran dan feedback sangat diterima!

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademik (Proposal Tesis BAB 4).

---

**Dibuat dengan ❤️ untuk Proposal Tesis**  
*Ekstraksi Data Adaptif dari Template PDF berbasis Human-in-the-Loop*
