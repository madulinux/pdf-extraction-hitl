# PDF conversion module

import os
import logging
import time
import threading
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger("docservice.processor")

# Global semaphore to limit concurrent LibreOffice processes
# Maximum 3 concurrent LibreOffice instances to prevent crashes
# Using threading.Semaphore instead of multiprocessing to avoid daemon process issues
_libreoffice_semaphore = threading.Semaphore(3)

def _get_libreoffice_semaphore():
    """Get the LibreOffice semaphore"""
    return _libreoffice_semaphore

def convert_docx_to_pdf(docx_path: str, output_path: str = None, skip_docx2pdf: bool = True, prefer_word: bool = False) -> str:
    """
    Convert a DOCX file to PDF.
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file (optional)
        skip_docx2pdf: Skip docx2pdf to avoid Microsoft Word popup on macOS (default: True)
        prefer_word: Prefer Microsoft Word over LibreOffice (requires permission granted)
        
    Returns:
        Path to the PDF file
    """
    # Check if file exists
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")
    
    # Generate output path if not provided
    if output_path is None:
        output_path = os.path.splitext(docx_path)[0] + ".pdf"
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try multiple conversion methods
    pdf_path = None
    
    # If prefer_word is True, try docx2pdf first (requires permission granted)
    if prefer_word and not skip_docx2pdf:
        try:
            pdf_path = _convert_with_docx2pdf(docx_path, output_path)
            if pdf_path:
                return pdf_path
        except Exception as e:
            logger.warning(f"docx2pdf conversion failed: {str(e)}, falling back to LibreOffice")
    
    # Method 1: Try with LibreOffice (if available) - RECOMMENDED for macOS
    try:
        pdf_path = _convert_with_libreoffice(docx_path, output_path)
        if pdf_path:
            return pdf_path
    except Exception as e:
        logger.warning(f"LibreOffice conversion failed: {str(e)}")
    
    # Method 2: Try with docx2pdf (SKIP by default on macOS to avoid popup)
    if not skip_docx2pdf and not prefer_word:
        try:
            pdf_path = _convert_with_docx2pdf(docx_path, output_path)
            if pdf_path:
                return pdf_path
        except Exception as e:
            logger.warning(f"docx2pdf conversion failed: {str(e)}")
    elif skip_docx2pdf:
        logger.debug("Skipping docx2pdf to avoid Microsoft Word popup on macOS")
    
    # Method 3: Try with WeasyPrint
    try:
        pdf_path = _convert_with_weasyprint(docx_path, output_path)
        if pdf_path:
            return pdf_path
    except Exception as e:
        logger.warning(f"WeasyPrint conversion failed: {str(e)}")
    
    # Method 4: Try with pdfkit
    try:
        pdf_path = _convert_with_pdfkit(docx_path, output_path)
        if pdf_path:
            return pdf_path
    except Exception as e:
        logger.warning(f"pdfkit conversion failed: {str(e)}")
    
    # If all methods failed, raise an exception
    if not pdf_path:
        raise Exception("All PDF conversion methods failed. Please ensure LibreOffice is installed.")
    
    return pdf_path

def _convert_with_libreoffice(docx_path: str, output_path: str, max_retries: int = 2) -> Optional[str]:
    """
    Convert a DOCX file to PDF using LibreOffice with semaphore control.
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file
        max_retries: Maximum number of retry attempts
        
    Returns:
        Path to the PDF file or None if conversion failed
    """
    import subprocess
    import platform
    
    # Get the semaphore to limit concurrent LibreOffice processes
    semaphore = _get_libreoffice_semaphore()
    
    for attempt in range(max_retries + 1):
        try:
            # Acquire semaphore (wait if 3 processes are already running)
            with semaphore:
                # Small delay to prevent race conditions
                if attempt > 0:
                    time.sleep(0.5 * attempt)  # Increasing delay on retries
                
                return _do_libreoffice_conversion(docx_path, output_path)
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"LibreOffice conversion attempt {attempt + 1} failed: {str(e)}, retrying...")
                time.sleep(1)  # Wait before retry
            else:
                logger.error(f"LibreOffice conversion failed after {max_retries + 1} attempts: {str(e)}")
                return None
    
    return None

def _do_libreoffice_conversion(docx_path: str, output_path: str) -> Optional[str]:
    """
    Actual LibreOffice conversion logic (called within semaphore context).
    Uses isolated user profile to prevent crashes in multiprocessing.
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file
        
    Returns:
        Path to the PDF file or None if conversion failed
    """
    import subprocess
    import platform
    import tempfile
    import uuid
    
    # Determine the LibreOffice executable path based on the platform
    if platform.system() == "Windows":
        # Try common installation paths on Windows
        libreoffice_paths = [
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe"
        ]
        libreoffice_exe = None
        for path in libreoffice_paths:
            if os.path.exists(path):
                libreoffice_exe = path
                break
        if not libreoffice_exe:
            raise FileNotFoundError("LibreOffice executable not found")
    elif platform.system() == "Darwin":  # macOS
        libreoffice_exe = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        if not os.path.exists(libreoffice_exe):
            raise FileNotFoundError("LibreOffice executable not found")
    else:  # Linux and other Unix-like systems
        # Try to find LibreOffice in PATH
        try:
            libreoffice_exe = subprocess.check_output(["which", "libreoffice"]).decode().strip()
        except subprocess.CalledProcessError:
            try:
                libreoffice_exe = subprocess.check_output(["which", "soffice"]).decode().strip()
            except subprocess.CalledProcessError:
                raise FileNotFoundError("LibreOffice executable not found")
    
    # Get the output directory
    output_dir = os.path.dirname(output_path)
    if not output_dir:
        output_dir = os.getcwd()
    
    # Create isolated user profile directory for this process
    # This prevents crashes when multiple LibreOffice instances run simultaneously
    temp_profile_dir = tempfile.mkdtemp(prefix=f"libreoffice_profile_{uuid.uuid4().hex[:8]}_")
    
    try:
        # Run LibreOffice to convert the file
        # Key flags for multiprocessing stability:
        # -env:UserInstallation: Use isolated user profile (CRITICAL for preventing crashes)
        # --headless: Run without GUI
        # --invisible: Run in invisible mode
        # --norestore: Don't restore previous session
        # --nolockcheck: Don't check for lock files
        cmd = [
            libreoffice_exe,
            f"-env:UserInstallation=file://{temp_profile_dir}",  # ISOLATED PROFILE
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
    
        # Use timeout to prevent hanging processes
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=45  # 45 seconds timeout per document
        )
        
        # Small delay after conversion to let LibreOffice cleanup
        time.sleep(0.1)
        
        # LibreOffice creates the PDF file with the same name as the input file but with .pdf extension
        default_pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
        
        # If the default path is different from the requested output path, rename the file
        if default_pdf_path != output_path and os.path.exists(default_pdf_path):
            os.rename(default_pdf_path, output_path)
        
        # Check if the PDF file was created
        if os.path.exists(output_path):
            # logger.info(f"Successfully converted DOCX to PDF using LibreOffice: {output_path}")
            return output_path
        else:
            logger.warning(f"LibreOffice did not create the PDF file: {output_path}")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"LibreOffice conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error during LibreOffice conversion: {str(e)}")
        return None
    finally:
        # Cleanup temporary profile directory
        try:
            import shutil
            if os.path.exists(temp_profile_dir):
                shutil.rmtree(temp_profile_dir, ignore_errors=True)
        except Exception as e:
            logger.debug(f"Failed to cleanup temp profile: {str(e)}")

def _convert_with_docx2pdf(docx_path: str, output_path: str) -> Optional[str]:
    """
    Convert a DOCX file to PDF using docx2pdf.
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file
        
    Returns:
        Path to the PDF file or None if conversion failed
    """
    try:
        from docx2pdf import convert
        
        # Convert the file
        convert(docx_path, output_path)
        
        # Check if the PDF file was created
        if os.path.exists(output_path):
            # logger.info(f"Successfully converted DOCX to PDF using docx2pdf: {output_path}")
            return output_path
        else:
            logger.warning(f"docx2pdf did not create the PDF file: {output_path}")
            return None
    except ImportError:
        logger.warning("docx2pdf module not installed")
        return None
    except Exception as e:
        logger.error(f"Error during docx2pdf conversion: {str(e)}")
        return None

def _convert_with_weasyprint(docx_path: str, output_path: str) -> Optional[str]:
    """
    Convert a DOCX file to PDF using WeasyPrint (via HTML).
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file
        
    Returns:
        Path to the PDF file or None if conversion failed
    """
    try:
        # First convert DOCX to HTML
        from .html_converter import docx_to_html
        html_content = docx_to_html(docx_path)
        
        # Then convert HTML to PDF
        from weasyprint import HTML
        
        # Create a temporary HTML file
        html_path = output_path + ".html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML to PDF
        HTML(html_path).write_pdf(output_path)
        
        # Clean up the temporary HTML file
        if os.path.exists(html_path):
            os.remove(html_path)
        
        # Check if the PDF file was created
        if os.path.exists(output_path):
            # logger.info(f"Successfully converted DOCX to PDF using WeasyPrint: {output_path}")
            return output_path
        else:
            logger.warning(f"WeasyPrint did not create the PDF file: {output_path}")
            return None
    except ImportError:
        logger.warning("WeasyPrint module not installed")
        return None
    except Exception as e:
        logger.error(f"Error during WeasyPrint conversion: {str(e)}")
        return None

def _convert_with_pdfkit(docx_path: str, output_path: str) -> Optional[str]:
    """
    Convert a DOCX file to PDF using pdfkit (via HTML).
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file
        
    Returns:
        Path to the PDF file or None if conversion failed
    """
    try:
        # First convert DOCX to HTML
        from .html_converter import docx_to_html
        html_content = docx_to_html(docx_path)
        
        # Then convert HTML to PDF
        import pdfkit
        
        # Create a temporary HTML file
        html_path = output_path + ".html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML to PDF
        pdfkit.from_file(html_path, output_path)
        
        # Clean up the temporary HTML file
        if os.path.exists(html_path):
            os.remove(html_path)
        
        # Check if the PDF file was created
        if os.path.exists(output_path):
            # logger.info(f"Successfully converted DOCX to PDF using pdfkit: {output_path}")
            return output_path
        else:
            logger.warning(f"pdfkit did not create the PDF file: {output_path}")
            return None
    except ImportError:
        logger.warning("pdfkit module not installed")
        return None
    except Exception as e:
        logger.error(f"Error during pdfkit conversion: {str(e)}")
        return None
