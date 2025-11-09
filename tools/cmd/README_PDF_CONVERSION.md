# PDF Conversion Setup

## Masalah Popup Microsoft Word di macOS

Saat menggunakan `docx2pdf` di macOS, akan muncul popup "grant file access" dari Microsoft Word karena library tersebut menggunakan AppleScript untuk mengontrol Microsoft Word.

## Solusi: Gunakan LibreOffice

Aplikasi ini telah dikonfigurasi untuk menggunakan **LibreOffice** sebagai converter utama yang tidak memerlukan popup izin.

### Install LibreOffice di macOS

```bash
# Menggunakan Homebrew
brew install --cask libreoffice

# Atau download manual dari
# https://www.libreoffice.org/download/download/
```

### Verifikasi Instalasi

```bash
# Check apakah LibreOffice sudah terinstall
ls /Applications/LibreOffice.app/Contents/MacOS/soffice

# Test konversi manual
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir /tmp test.docx
```

## Cara Kerja

1. **LibreOffice (Default)**: Metode utama, tidak ada popup, cocok untuk multiprocessing
2. **docx2pdf (Disabled)**: Di-skip secara default untuk menghindari popup
3. **WeasyPrint (Fallback)**: Alternatif jika LibreOffice gagal
4. **pdfkit (Fallback)**: Alternatif terakhir

## Konfigurasi

Jika ingin mengaktifkan kembali docx2pdf (akan muncul popup):

```python
# Di dalam kode
convert_docx_to_pdf(docx_path, pdf_path, skip_docx2pdf=False)
```

## Performa dengan Multiprocessing

Dengan LibreOffice dan multiprocessing:
- **CPU Count - 1** workers digunakan secara default
- Setiap worker process menjalankan instance LibreOffice terpisah
- Timeout 30 detik per dokumen untuk mencegah hanging
- Flags optimasi untuk stabilitas multiprocessing

## Troubleshooting

### LibreOffice tidak ditemukan
```bash
# Install via Homebrew
brew install --cask libreoffice
```

### Konversi lambat
```bash
# Kurangi jumlah workers
python main.py generate-documents --count 100 --workers 2
```

### Process hanging
- Timeout otomatis 30 detik per dokumen
- Check log untuk error details
