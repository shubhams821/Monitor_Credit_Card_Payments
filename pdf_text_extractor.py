import subprocess
import os
import tempfile
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFTextExtractor:
    """
    Extract text from PDF documents using Poppler utilities
    """
    
    def __init__(self):
        self.check_poppler_installation()
    
    def check_poppler_installation(self) -> bool:
        """
        Check if Poppler utilities are installed
        """
        try:
            # Check for pdftotext command
            result = subprocess.run(['pdftotext', '-v'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                logger.info("Poppler utilities found")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("Poppler utilities not found. Please install poppler-utils.")
        logger.info("Installation instructions:")
        logger.info("  Ubuntu/Debian: sudo apt-get install poppler-utils")
        logger.info("  macOS: brew install poppler")
        logger.info("  Windows: Download from https://poppler.freedesktop.org/")
        return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using pdftotext
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not self.check_poppler_installation():
            return {
                "success": False,
                "error": "Poppler utilities not installed",
                "text": "",
                "pages": 0,
                "word_count": 0
            }
        
        try:
            # Create temporary file for text output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_text_path = temp_file.name
            
            # Extract text using pdftotext
            cmd = [
                'pdftotext',
                '-layout',  # Maintain layout
                '-enc', 'UTF-8',  # UTF-8 encoding
                pdf_path,
                temp_text_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
            
            # Read extracted text
            with open(temp_text_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
            
            # Get page count using pdfinfo
            page_count = self.get_page_count(pdf_path)
            
            # Calculate word count
            word_count = len(extracted_text.split())
            
            # Clean up temporary file
            os.unlink(temp_text_path)
            
            return {
                "success": True,
                "text": extracted_text,
                "pages": page_count,
                "word_count": word_count,
                "file_path": pdf_path
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while extracting text from {pdf_path}")
            return {
                "success": False,
                "error": "Timeout during text extraction",
                "text": "",
                "pages": 0,
                "word_count": 0
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return {
                "success": False,
                "error": f"Poppler error: {e.stderr}",
                "text": "",
                "pages": 0,
                "word_count": 0
            }
        except Exception as e:
            logger.error(f"Unexpected error extracting text from {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "pages": 0,
                "word_count": 0
            }
    
    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the number of pages in a PDF using pdfinfo
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Number of pages
        """
        try:
            cmd = ['pdfinfo', pdf_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse output to find page count
                for line in result.stdout.split('\n'):
                    if line.startswith('Pages:'):
                        return int(line.split(':')[1].strip())
            
            return 0
            
        except Exception as e:
            logger.warning(f"Could not get page count for {pdf_path}: {e}")
            return 0
    
    def extract_text_by_pages(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF page by page
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing text for each page
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not self.check_poppler_installation():
            return {
                "success": False,
                "error": "Poppler utilities not installed",
                "pages": {}
            }
        
        try:
            page_count = self.get_page_count(pdf_path)
            pages_text = {}
            
            for page_num in range(1, page_count + 1):
                # Create temporary file for this page
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_text_path = temp_file.name
                
                # Extract text for specific page
                cmd = [
                    'pdftotext',
                    '-layout',
                    '-enc', 'UTF-8',
                    '-f', str(page_num),  # First page
                    '-l', str(page_num),  # Last page
                    pdf_path,
                    temp_text_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    with open(temp_text_path, 'r', encoding='utf-8') as f:
                        page_text = f.read()
                    pages_text[page_num] = page_text
                else:
                    pages_text[page_num] = f"Error extracting page {page_num}"
                
                # Clean up temporary file
                os.unlink(temp_text_path)
            
            return {
                "success": True,
                "pages": pages_text,
                "total_pages": page_count
            }
            
        except Exception as e:
            logger.error(f"Error extracting text by pages from {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pages": {}
            }

# Convenience function for easy usage
def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to extract text from PDF
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extracted text and metadata
    """
    extractor = PDFTextExtractor()
    return extractor.extract_text_from_pdf(pdf_path)

def extract_text_by_pages(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to extract text from PDF page by page
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing text for each page
    """
    extractor = PDFTextExtractor()
    return extractor.extract_text_by_pages(pdf_path) 