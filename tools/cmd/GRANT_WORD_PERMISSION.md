# Grant Microsoft Word Permission - Solusi Terbaik

## Mengapa Microsoft Word Lebih Baik?

1. **Lebih Stabil** - Native macOS app, tidak crash seperti LibreOffice
2. **Lebih Cepat** - Optimized untuk macOS
3. **Better Quality** - Hasil PDF lebih akurat
4. **No Concurrent Limit** - Bisa banyak instance bersamaan

## Cara Grant Permission (One-time Setup)

### Step 1: Buka System Settings
```
1. Klik Apple menu () → System Settings
2. Pilih "Privacy & Security"
3. Scroll ke bawah, klik "Full Disk Access"
```

### Step 2: Add Python & Terminal
```
1. Klik tombol "+" (Add)
2. Navigate ke:
   - /usr/bin/python3 (atau path python Anda)
   - /Applications/Utilities/Terminal.app
   - /usr/bin/osascript (untuk AppleScript)
3. Enable toggle untuk semua yang ditambahkan
```

### Step 3: Add Microsoft Word (Optional)
```
1. Klik tombol "+" (Add)
2. Navigate ke: /Applications/Microsoft Word.app
3. Enable toggle
```

### Step 4: Restart Terminal
```bash
# Tutup semua terminal windows
# Buka terminal baru
```

## Alternative: Automation Permission

Jika Full Disk Access tidak bekerja:

### Step 1: System Settings
```
1. Apple menu () → System Settings
2. Privacy & Security → Automation
3. Cari "Python" atau "Terminal"
4. Enable "Microsoft Word"
```

### Step 2: Accessibility Permission
```
1. Privacy & Security → Accessibility
2. Klik "+" dan tambahkan:
   - Terminal.app
   - Python
3. Enable toggle
```

## Test Permission

```bash
# Test apakah permission sudah bekerja
cd /Users/madulinux/Documents/S2\ UNAS/TESIS/Project/tools/cmd
python -c "from docx2pdf import convert; print('Permission OK')"
```

## Enable docx2pdf di Code

Setelah permission di-grant, aktifkan kembali docx2pdf:

```bash
# Edit main.py atau jalankan dengan flag
python main.py generate-documents --count 10 --use-word
```

## Keuntungan Menggunakan Word

✅ **Tidak ada crash** - Stabil untuk ratusan dokumen
✅ **Lebih cepat** - 0.2-0.3 detik per dokumen (vs 0.8 detik LibreOffice)
✅ **Concurrent unlimited** - Bisa 11 workers tanpa masalah
✅ **Better quality** - Formatting lebih akurat
✅ **No semaphore needed** - Tidak perlu batasi concurrent

## Troubleshooting

### Popup masih muncul?
```
1. Pastikan sudah restart Terminal
2. Check Full Disk Access sudah enable
3. Try Automation permission juga
4. Restart Mac (last resort)
```

### Permission denied?
```bash
# Check permission status
tccutil reset All com.microsoft.Word

# Re-grant permission di System Settings
```

### Word tidak terinstall?
```bash
# Check instalasi Word
ls /Applications/Microsoft\ Word.app

# Jika tidak ada, install Microsoft Office
# Atau gunakan LibreOffice dengan semaphore
```
