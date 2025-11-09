# Optimization Summary - Document Generation

## Masalah yang Diselesaikan

### 1. ❌ Popup Microsoft Word di macOS
**Masalah**: Saat menggunakan `docx2pdf`, muncul popup "grant file access" dari Microsoft Word secara berulang karena library menggunakan AppleScript.

**Solusi**: 
- ✅ Menonaktifkan `docx2pdf` secara default (`skip_docx2pdf=True`)
- ✅ Menggunakan LibreOffice sebagai converter utama
- ✅ LibreOffice tidak memerlukan popup izin dan lebih stabil untuk multiprocessing

### 2. 🚀 Performa Lambat (Sequential Processing)
**Sebelum**: Proses dokumen satu per satu secara sequential

**Sesudah**: Multiprocessing dengan worker pool
- ✅ Menggunakan CPU count - 1 workers secara default
- ✅ Parallel processing untuk semua dokumen
- ✅ Progress tracking real-time

## Hasil Optimalisasi

### Performa Test (25 dokumen)
```
Total documents: 25
Successful: 25
Failed: 0
Workers used: 11
Time elapsed: 13.41 seconds
Average time per document: 0.54 seconds
```

### Peningkatan Kecepatan
- **Sequential (sebelum)**: ~2-3 detik per dokumen = ~50-75 detik untuk 25 dokumen
- **Multiprocessing (sesudah)**: 13.41 detik untuk 25 dokumen
- **Speedup**: ~4-5x lebih cepat

## Fitur Baru

### 1. Multiprocessing
```python
def generate_documents(
    count: int = 1,
    workers: int = None,  # Auto: CPU count - 1
    show_progress: bool = True
)
```

### 2. Progress Tracking
```
2025-11-07 01:22:54,743 - INFO - Progress: 20/25 documents processed (80%)
2025-11-07 01:22:58,264 - INFO - Progress: 25/25 documents processed (100%)
```

### 3. Comprehensive Summary
```
============================================================
Document Generation Summary
============================================================
Total documents: 25
Successful: 25
Failed: 0
Workers used: 11
Time elapsed: 13.41 seconds
Average time per document: 0.54 seconds
============================================================
```

### 4. Error Handling per Dokumen
- Satu dokumen gagal tidak menghentikan proses
- Detail error untuk setiap dokumen yang gagal
- Retry mechanism dengan fallback converters

### 5. LibreOffice Optimization
```python
cmd = [
    libreoffice_exe,
    "--headless",
    "--invisible",
    "--nodefault",
    "--nofirststartwizard",
    "--nolockcheck",
    "--nologo",
    "--norestore",
    "--convert-to", "pdf",
    "--outdir", output_dir,
    docx_path
]
```

## Cara Penggunaan

### Basic
```bash
python main.py generate-documents --count 100
```

### Custom Workers
```bash
python main.py generate-documents --count 100 --workers 4
```

### Tanpa Progress
```bash
python main.py generate-documents --count 100 --show-progress=False
```

### Check LibreOffice
```bash
python check_libreoffice.py
```

## Fallback Converters

Urutan prioritas konversi:
1. **LibreOffice** (Primary) - No popup, stable, fast
2. **docx2pdf** (Disabled) - Causes popup on macOS
3. **WeasyPrint** (Fallback) - Via HTML conversion
4. **pdfkit** (Fallback) - Via HTML conversion

## Requirements

### LibreOffice (Required)
```bash
# macOS
brew install --cask libreoffice

# Linux
sudo apt-get install libreoffice

# Windows
# Download from https://www.libreoffice.org/download/
```

### Python Packages
```bash
pip install python-docx faker typer
pip install weasyprint  # Optional fallback
pip install pdfkit      # Optional fallback
```

## Troubleshooting

### Popup masih muncul?
- Pastikan `skip_docx2pdf=True` (default)
- Check log untuk memastikan LibreOffice digunakan

### LibreOffice tidak ditemukan?
```bash
python check_libreoffice.py
```

### Konversi lambat?
```bash
# Kurangi workers
python main.py generate-documents --count 100 --workers 2
```

### Process hanging?
- Timeout otomatis 30 detik per dokumen
- Check system resources (CPU, Memory)

## Performance Tips

1. **Optimal Workers**: CPU count - 1 (default)
2. **Batch Size**: 50-100 dokumen per batch untuk monitoring
3. **Disk Space**: Pastikan cukup space untuk output files
4. **Memory**: Monitor memory usage untuk batch besar

## Code Changes

### Files Modified
1. `/cmd/main.py` - Added multiprocessing support
2. `/cmd/utils/document/pdf_converter.py` - Optimized LibreOffice, disabled docx2pdf

### Files Created
1. `/cmd/README_PDF_CONVERSION.md` - PDF conversion documentation
2. `/cmd/check_libreoffice.py` - LibreOffice check utility
3. `/cmd/OPTIMIZATION_SUMMARY.md` - This file

## Kesimpulan

✅ **Tidak ada popup lagi** - LibreOffice tidak memerlukan izin interaktif
✅ **4-5x lebih cepat** - Multiprocessing dengan optimal workers
✅ **Lebih stabil** - Error handling per dokumen
✅ **Better monitoring** - Progress tracking dan summary
✅ **Production ready** - Timeout, logging, fallback mechanisms
