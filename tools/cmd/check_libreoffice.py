#!/usr/bin/env python3
"""
Script untuk check instalasi LibreOffice dan test konversi PDF
"""

import os
import sys
import subprocess
import platform

def check_libreoffice():
    """Check apakah LibreOffice terinstall"""
    print("=" * 60)
    print("LibreOffice Installation Check")
    print("=" * 60)
    
    if platform.system() == "Darwin":  # macOS
        libreoffice_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        
        if os.path.exists(libreoffice_path):
            print("✅ LibreOffice FOUND at:", libreoffice_path)
            
            # Get version
            try:
                result = subprocess.run(
                    [libreoffice_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                print("📦 Version:", result.stdout.strip())
            except Exception as e:
                print("⚠️  Could not get version:", str(e))
            
            return True
        else:
            print("❌ LibreOffice NOT FOUND")
            print("\n📥 Install LibreOffice:")
            print("   brew install --cask libreoffice")
            print("   OR download from: https://www.libreoffice.org/download/")
            return False
    
    elif platform.system() == "Windows":
        paths = [
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe"
        ]
        
        for path in paths:
            if os.path.exists(path):
                print("✅ LibreOffice FOUND at:", path)
                return True
        
        print("❌ LibreOffice NOT FOUND")
        print("\n📥 Download from: https://www.libreoffice.org/download/")
        return False
    
    else:  # Linux
        try:
            result = subprocess.run(
                ["which", "libreoffice"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                print("✅ LibreOffice FOUND at:", path)
                return True
            else:
                print("❌ LibreOffice NOT FOUND")
                print("\n📥 Install LibreOffice:")
                print("   sudo apt-get install libreoffice  # Debian/Ubuntu")
                print("   sudo yum install libreoffice      # RHEL/CentOS")
                return False
        except Exception as e:
            print("❌ Error checking LibreOffice:", str(e))
            return False

def test_conversion():
    """Test konversi DOCX ke PDF"""
    print("\n" + "=" * 60)
    print("Testing PDF Conversion")
    print("=" * 60)
    
    # Check if there are any template files
    template_dir = os.path.join(os.getcwd(), "storage/templates")
    
    if not os.path.exists(template_dir):
        print("⚠️  Template directory not found:", template_dir)
        return
    
    docx_files = [f for f in os.listdir(template_dir) if f.endswith('.docx')]
    
    if not docx_files:
        print("⚠️  No DOCX files found in:", template_dir)
        return
    
    print(f"📄 Found {len(docx_files)} template(s)")
    
    # Test with the first template
    test_file = os.path.join(template_dir, docx_files[0])
    print(f"\n🧪 Testing with: {docx_files[0]}")
    
    try:
        from utils.document_processor import convert_docx_to_pdf
        import tempfile
        
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        print("⏳ Converting...")
        result = convert_docx_to_pdf(test_file, output_path)
        
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"✅ Conversion SUCCESSFUL!")
            print(f"   Output: {result}")
            print(f"   Size: {file_size:,} bytes")
            
            # Clean up
            os.remove(result)
        else:
            print("❌ Conversion FAILED - output file not created")
    
    except Exception as e:
        print(f"❌ Conversion FAILED: {str(e)}")

def main():
    """Main function"""
    # Check LibreOffice installation
    libreoffice_ok = check_libreoffice()
    
    if libreoffice_ok:
        # Test conversion
        test_conversion()
    
    print("\n" + "=" * 60)
    
    if libreoffice_ok:
        print("✅ System ready for document generation!")
        print("\n💡 Run: python main.py generate-documents --count 10")
    else:
        print("⚠️  Please install LibreOffice first")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
