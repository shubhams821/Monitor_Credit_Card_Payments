import base64
import json
import logging
from typing import Dict, Any, List, Optional
import fitz  # PyMuPDF
import io
from PIL import Image
import os
import dotenv

dotenv.load_dotenv()

api_key=os.getenv("GROQ_API_KEY")
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Import the LLM client (you'll need to configure this)
try:
    from groq import Groq
    client = Groq(api_key=api_key)
except ImportError:
    logger.warning("Groq client not available. Please install groq package.")
    client = None

def get_llm_response_over_images(system_prompt: str, user_input: str) -> str:
    """
    Get LLM response for image processing using Groq API
    
    Args:
        system_prompt: System prompt for the LLM
        user_input: User input with image data
        
    Returns:
        LLM response as string
    """
    if not client:
        return "Error: Groq client not configured"
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=0.6,
            max_completion_tokens=8192,
            top_p=0.95,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting LLM response: {e}")
        return f"Error: {str(e)}"

class VisionOCR:
    """
    OCR processing using vision models for PDF documents
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize VisionOCR
        
        Args:
            api_key: API key for the vision service
        """
        self.api_key = api_key
        if not self.api_key:
            logger.warning("No API key provided for vision OCR")
    
    def extract_images_from_pdf(self, pdf_path: str, dpi: int = 300) -> List[Dict[str, Any]]:
        """
        Extract images from PDF pages
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for image extraction
            
        Returns:
            List of dictionaries containing page images and metadata
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Convert page to image
                mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Convert to base64 for API
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                images.append({
                    "page_number": page_num + 1,
                    "image": img,
                    "image_base64": img_base64,
                    "width": img.width,
                    "height": img.height,
                    "dpi": dpi
                })
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {e}")
            return []
    
    def process_image_with_ocr(self, image_base64: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Process a single image with OCR using vision model
        
        Args:
            image_base64: Base64 encoded image
            system_prompt: Custom system prompt for OCR
            
        Returns:
            Dictionary containing OCR results
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured",
                "text": "",
                "confidence": 0.0
            }
        
        # Default system prompt for OCR
        if not system_prompt:
            system_prompt = """You are an expert OCR (Optical Character Recognition) system. 
            Your task is to extract all text from the provided image with high accuracy.
            
            Instructions:
            1. Read all text visible in the image
            2. Maintain the original formatting and layout as much as possible
            3. Include headers, footers, and any text in margins
            4. Preserve numbers, dates, and special characters
            5. If text is unclear or partially visible, indicate with [unclear] or [partial]
            6. Return the extracted text in a clean, readable format
            
            Please extract all text from the image:"""
        
        try:
            # Create user input with image
            # user_input = f"<image>\n{image_base64}\n</image>\n\nPlease extract all text from this image."
            user_input= [{
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_base64}"
            }}]
            # Get LLM response
            response = get_llm_response_over_images(system_prompt, user_input)
            
            return {
                "success": True,
                "text": response,
                "confidence": 0.9,  # Placeholder confidence score
                "model": "meta-llama/llama-4-scout-17b-16e-instruct"
            }
            
        except Exception as e:
            logger.error(f"Error processing image with OCR: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "confidence": 0.0
            }
    
    def process_pdf_with_ocr(self, pdf_path: str, dpi: int = 300, 
                           system_prompt: str = None) -> Dict[str, Any]:
        """
        Process entire PDF with OCR
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for image extraction
            system_prompt: Custom system prompt for OCR
            
        Returns:
            Dictionary containing OCR results for all pages
        """
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "error": f"PDF file not found: {pdf_path}",
                "pages": {},
                "total_pages": 0
            }
        
        try:
            # Extract images from PDF
            images = self.extract_images_from_pdf(pdf_path, dpi)
            
            if not images:
                return {
                    "success": False,
                    "error": "No images extracted from PDF",
                    "pages": {},
                    "total_pages": 0
                }
            
            # Process each page with OCR
            ocr_results = {}
            total_text = ""
            
            for img_data in images:
                page_num = img_data["page_number"]
                logger.info(f"Processing page {page_num} with OCR...")
                
                # Process image with OCR
                ocr_result = self.process_image_with_ocr(
                    img_data["image_base64"], 
                    system_prompt
                )
                
                ocr_results[page_num] = {
                    "text": ocr_result.get("text", ""),
                    "success": ocr_result.get("success", False),
                    "confidence": ocr_result.get("confidence", 0.0),
                    "error": ocr_result.get("error", ""),
                    "image_info": {
                        "width": img_data["width"],
                        "height": img_data["height"],
                        "dpi": img_data["dpi"]
                    }
                }
                
                if ocr_result.get("success"):
                    total_text += f"\n--- Page {page_num} ---\n"
                    total_text += ocr_result.get("text", "")
            
            return {
                "success": True,
                "pages": ocr_results,
                "total_pages": len(images),
                "complete_text": total_text.strip(),
                "file_path": pdf_path
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF with OCR {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pages": {},
                "total_pages": 0
            }
    
    def compare_text_extraction_methods(self, pdf_path: str) -> Dict[str, Any]:
        """
        Compare text extraction using Poppler vs Vision OCR
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing comparison results
        """
        try:
            # Import Poppler extractor
            from pdf_text_extractor import extract_text_from_pdf
            
            # Extract text using Poppler
            poppler_result = extract_text_from_pdf(pdf_path)
            
            # Extract text using Vision OCR
            ocr_result = self.process_pdf_with_ocr(pdf_path)
            
            # Compare results
            comparison = {
                "pdf_path": pdf_path,
                "poppler": {
                    "success": poppler_result.get("success", False),
                    "text_length": len(poppler_result.get("text", "")),
                    "word_count": poppler_result.get("word_count", 0),
                    "pages": poppler_result.get("pages", 0),
                    "error": poppler_result.get("error", "")
                },
                "vision_ocr": {
                    "success": ocr_result.get("success", False),
                    "text_length": len(ocr_result.get("complete_text", "")),
                    "word_count": len(ocr_result.get("complete_text", "").split()),
                    "pages": ocr_result.get("total_pages", 0),
                    "error": ocr_result.get("error", "")
                }
            }
            
            # Calculate similarity (basic word overlap)
            if (comparison["poppler"]["success"] and 
                comparison["vision_ocr"]["success"]):
                
                poppler_words = set(poppler_result.get("text", "").lower().split())
                ocr_words = set(ocr_result.get("complete_text", "").lower().split())
                
                if poppler_words and ocr_words:
                    overlap = len(poppler_words.intersection(ocr_words))
                    total_unique = len(poppler_words.union(ocr_words))
                    similarity = overlap / total_unique if total_unique > 0 else 0
                    
                    comparison["similarity"] = {
                        "overlap_words": overlap,
                        "total_unique_words": total_unique,
                        "similarity_score": similarity
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing text extraction methods: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": pdf_path
            }

# Convenience functions
def process_pdf_with_ocr(pdf_path: str, dpi: int = 300, 
                        system_prompt: str = None) -> Dict[str, Any]:
    """
    Convenience function to process PDF with OCR
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for image extraction
        system_prompt: Custom system prompt for OCR
        
    Returns:
        Dictionary containing OCR results
    """
    ocr = VisionOCR(api_key=api_key)
    return ocr.process_pdf_with_ocr(pdf_path, dpi, system_prompt)

def compare_extraction_methods(pdf_path: str) -> Dict[str, Any]:
    """
    Convenience function to compare text extraction methods
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing comparison results
    """
    ocr = VisionOCR(api_key=api_key)
    return ocr.compare_text_extraction_methods(pdf_path) 