# Document Upload API

A FastAPI-based Python API for uploading PDF documents with user ID and statement ID information, storing them in a database.

## Features

- Upload PDF documents with user ID and statement ID
- File validation (PDF only, max 10MB)
- Database storage with SQLAlchemy
- Support for SQLite (default) and PostgreSQL
- **Automatic text extraction using Poppler utilities**
- **OCR processing using Vision models (Groq API)**
- **Background text processing during upload**
- **Text extraction comparison and analysis**
- RESTful API endpoints
- Automatic file management
- Comprehensive error handling

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MonitorCredit
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Poppler utilities (required for text extraction):
   - **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
   - **macOS**: `brew install poppler`
   - **Windows**: Download from https://poppler.freedesktop.org/

5. Set up environment variables:
```bash
# Copy the example file
cp env_example.txt .env
# Edit .env with your configuration
```

6. Configure API keys (optional, for OCR):
   - Add your Groq API key to `.env`: `GROQ_API_KEY=your_api_key_here`

## Database Setup

The API uses SQLite by default. The database file (`documents.db`) will be created automatically when you first run the application.

### Database Migration (if upgrading from older version)

If you're upgrading from a previous version and encounter database errors, run the migration script:

```bash
python fix_database.py
```

Or use the interactive migration tool:

```bash
python migrate_database.py
```

### For PostgreSQL:
1. Install PostgreSQL
2. Create a database
3. Set the `DATABASE_URL` environment variable:
```
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

## Running the API

Start the development server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Upload Document
- **POST** `/upload-document/`
- Upload a PDF document with user ID and statement ID
- Form data: `user_id`, `statement_id`, `pdf_file`

### Get Documents
- **GET** `/documents/`
- Retrieve all documents with optional filtering
- Query parameters: `user_id`, `statement_id`

### Get Document by ID
- **GET** `/documents/{document_id}`
- Retrieve a specific document by its ID

### Delete Document
- **DELETE** `/documents/{document_id}`
- Delete a document and its associated file

### Extract Text (Manual)
- **POST** `/documents/{document_id}/extract-text`
- Manually trigger text extraction for a document
- Returns comparison between Poppler and OCR methods

### Get Document Text
- **GET** `/documents/{document_id}/text`
- Get extracted text from both Poppler and OCR methods

## Usage Examples

### Upload a document using curl:
```bash
curl -X POST "http://localhost:8000/upload-document/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "user_id=user123" \
  -F "statement_id=stmt456" \
  -F "pdf_file=@/path/to/your/document.pdf"
```

### Upload using Python requests:
```python
import requests

url = "http://localhost:8000/upload-document/"
files = {"pdf_file": open("document.pdf", "rb")}
data = {
    "user_id": "user123",
    "statement_id": "stmt456"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Get documents for a specific user:
```bash
curl "http://localhost:8000/documents/?user_id=user123"
```

### Extract text from a document:
```bash
curl -X POST "http://localhost:8000/documents/1/extract-text"
```

### Get extracted text:
```bash
curl "http://localhost:8000/documents/1/text"
```

## Project Structure

```
MonitorCredit/
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables example
├── README.md           # This file
├── uploads/            # Directory for uploaded files (created automatically)
└── documents.db        # SQLite database (created automatically)
```

## Database Schema

The `documents` table contains:
- `id`: Primary key
- `user_id`: User identifier
- `statement_id`: Statement identifier
- `original_filename`: Original filename
- `stored_filename`: Unique stored filename
- `file_path`: Path to stored file
- `file_size`: File size in bytes
- `upload_date`: Upload timestamp
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

### Text Extraction Fields:
- `poppler_text`: Text extracted using Poppler utilities
- `poppler_word_count`: Word count from Poppler extraction
- `poppler_pages`: Number of pages processed by Poppler
- `poppler_extraction_success`: Whether Poppler extraction succeeded
- `ocr_text`: Text extracted using Vision OCR
- `ocr_word_count`: Word count from OCR extraction
- `ocr_pages`: Number of pages processed by OCR
- `ocr_extraction_success`: Whether OCR extraction succeeded
- `ocr_confidence`: OCR confidence score (0-100)
- `text_processing_completed`: Whether text processing is complete
- `text_processing_error`: Error message if processing failed

## Error Handling

The API includes comprehensive error handling for:
- Invalid file types (non-PDF)
- File size limits (10MB max)
- Database errors
- File system errors
- Missing documents

## Security Considerations

- File type validation
- File size limits
- Unique filename generation
- Proper error handling
- Database connection management

## Development

To run in development mode with auto-reload:
```bash
uvicorn main:app --reload
```

## Production Deployment

For production deployment:
1. Use a production WSGI server like Gunicorn
2. Set up proper database (PostgreSQL recommended)
3. Configure environment variables
4. Set up reverse proxy (nginx)
5. Implement authentication and authorization
6. Set up proper logging and monitoring

## License

This project is open source and available under the MIT License. 