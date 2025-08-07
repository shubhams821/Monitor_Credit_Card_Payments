import requests
import os
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_text_extraction():
    """Test the text extraction features of the Document Upload API"""
    
    print("Testing Text Extraction Features...")
    
    # Test 1: Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✓ API is running: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("✗ API is not running. Please start the server first.")
        return
    
    # Test 2: Create a test PDF file
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        print("✗ Failed to create test PDF file")
        return
    
    print(f"✓ Created test PDF: {test_pdf_path}")
    
    # Test 3: Upload document
    try:
        with open(test_pdf_path, 'rb') as f:
            files = {"pdf_file": f}
            data = {
                "user_id": "test_user_123",
                "statement_id": "test_statement_456"
            }
            
            response = requests.post(f"{BASE_URL}/upload-document/", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Document uploaded successfully!")
                print(f"  Document ID: {result['id']}")
                print(f"  Text processing status: {result['text_processing_completed']}")
                
                document_id = result['id']
                
                # Test 4: Wait for background processing (or trigger manually)
                print("Waiting for background text processing...")
                time.sleep(5)  # Wait a bit for background processing
                
                # Test 5: Manually trigger text extraction
                print("Manually triggering text extraction...")
                response = requests.post(f"{BASE_URL}/documents/{document_id}/extract-text")
                
                if response.status_code == 200:
                    extraction_result = response.json()
                    print(f"✓ Text extraction completed!")
                    print(f"  Poppler success: {extraction_result['poppler_success']}")
                    print(f"  Poppler word count: {extraction_result['poppler_word_count']}")
                    print(f"  OCR success: {extraction_result['ocr_success']}")
                    print(f"  OCR word count: {extraction_result['ocr_word_count']}")
                    print(f"  OCR confidence: {extraction_result['ocr_confidence']}")
                    if extraction_result.get('similarity_score'):
                        print(f"  Similarity score: {extraction_result['similarity_score']:.2f}")
                
                # Test 6: Get extracted text
                print("Retrieving extracted text...")
                response = requests.get(f"{BASE_URL}/documents/{document_id}/text")
                
                if response.status_code == 200:
                    text_result = response.json()
                    print(f"✓ Retrieved text data!")
                    print(f"  Poppler text length: {len(text_result['poppler']['text'])}")
                    print(f"  OCR text length: {len(text_result['ocr']['text'])}")
                    
                    # Show sample text
                    if text_result['poppler']['text']:
                        print(f"  Poppler sample: {text_result['poppler']['text'][:100]}...")
                    if text_result['ocr']['text']:
                        print(f"  OCR sample: {text_result['ocr']['text'][:100]}...")
                
                # Test 7: Get updated document info
                response = requests.get(f"{BASE_URL}/documents/{document_id}")
                if response.status_code == 200:
                    doc = response.json()
                    print(f"✓ Updated document info retrieved!")
                    print(f"  Text processing completed: {doc['text_processing_completed']}")
                    print(f"  Poppler extraction success: {doc['poppler_extraction_success']}")
                    print(f"  OCR extraction success: {doc['ocr_extraction_success']}")
                
                # Test 8: Delete document
                response = requests.delete(f"{BASE_URL}/documents/{document_id}")
                if response.status_code == 200:
                    print(f"✓ Document deleted successfully")
                
            else:
                print(f"✗ Upload failed: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
    
    # Clean up test file
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
        print(f"✓ Cleaned up test file")

def create_test_pdf():
    """Create a simple test PDF file with text content"""
    try:
        # Create a temporary PDF file with text content
        # This is a very basic PDF structure - in real usage, you'd use a proper PDF library
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 100\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Document with Text Content) Tj\n72 700 Td\n(This is a sample document for testing text extraction.) Tj\n72 680 Td\n(It contains multiple lines of text to test both Poppler and OCR.) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n353\n%%EOF\n'
        
        # Create temporary file
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        test_pdf_path = temp_dir / "test_document_with_text.pdf"
        with open(test_pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        return str(test_pdf_path)
        
    except Exception as e:
        print(f"Error creating test PDF: {str(e)}")
        return None

def test_standalone_extractors():
    """Test the standalone text extraction modules"""
    print("\nTesting Standalone Text Extractors...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        return
    
    try:
        # Test Poppler extractor
        print("Testing Poppler text extraction...")
        from pdf_text_extractor import extract_text_from_pdf
        
        poppler_result = extract_text_from_pdf(test_pdf_path)
        print(f"  Poppler success: {poppler_result.get('success')}")
        if poppler_result.get('success'):
            print(f"  Text length: {len(poppler_result.get('text', ''))}")
            print(f"  Word count: {poppler_result.get('word_count')}")
            print(f"  Pages: {poppler_result.get('pages')}")
        
        # Test Vision OCR (if API key is available)
        print("Testing Vision OCR...")
        from vision_ocr import process_pdf_with_ocr
        
        ocr_result = process_pdf_with_ocr(test_pdf_path)
        print(f"  OCR success: {ocr_result.get('success')}")
        if ocr_result.get('success'):
            print(f"  Text length: {len(ocr_result.get('complete_text', ''))}")
            print(f"  Word count: {len(ocr_result.get('complete_text', '').split())}")
            print(f"  Pages: {ocr_result.get('total_pages')}")
        else:
            print(f"  OCR error: {ocr_result.get('error')}")
        
        # Test comparison
        print("Testing comparison...")
        from vision_ocr import compare_extraction_methods
        
        comparison = compare_extraction_methods(test_pdf_path)
        print(f"  Comparison completed: {comparison.get('success', False)}")
        if comparison.get('similarity'):
            print(f"  Similarity score: {comparison['similarity']['similarity_score']:.2f}")
        
    except Exception as e:
        print(f"✗ Error testing standalone extractors: {str(e)}")
    
    # Clean up
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)

if __name__ == "__main__":
    test_text_extraction()
    test_standalone_extractors() 