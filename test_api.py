import requests
import os
import tempfile
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_api():
    """Test the Document Upload API"""
    
    print("Testing Document Upload API...")
    
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
                print(f"  User ID: {result['user_id']}")
                print(f"  Statement ID: {result['statement_id']}")
                print(f"  File size: {result['file_size']} bytes")
                
                document_id = result['id']
                
                # Test 4: Get document by ID
                response = requests.get(f"{BASE_URL}/documents/{document_id}")
                if response.status_code == 200:
                    doc = response.json()
                    print(f"✓ Retrieved document by ID: {doc['original_filename']}")
                
                # Test 5: Get documents by user ID
                response = requests.get(f"{BASE_URL}/documents/?user_id=test_user_123")
                if response.status_code == 200:
                    docs = response.json()
                    print(f"✓ Retrieved {len(docs)} documents for user")
                
                # Test 6: Get documents by statement ID
                response = requests.get(f"{BASE_URL}/documents/?statement_id=test_statement_456")
                if response.status_code == 200:
                    docs = response.json()
                    print(f"✓ Retrieved {len(docs)} documents for statement")
                
                # Test 7: Delete document
                response = requests.delete(f"{BASE_URL}/documents/{document_id}")
                if response.status_code == 200:
                    print(f"✓ Document deleted successfully")
                
            else:
                print(f"✗ Upload failed: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"✗ Error during upload: {str(e)}")
    
    # Clean up test file
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
        print(f"✓ Cleaned up test file")

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        # Create a temporary PDF file with minimal content
        # This is a very basic PDF structure - in real usage, you'd use a proper PDF library
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF Document) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n'
        
        # Create temporary file
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        test_pdf_path = temp_dir / "test_document.pdf"
        with open(test_pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        return str(test_pdf_path)
        
    except Exception as e:
        print(f"Error creating test PDF: {str(e)}")
        return None

if __name__ == "__main__":
    test_api() 