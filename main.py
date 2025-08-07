from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import aiofiles
import os
from datetime import datetime
import uuid
from typing import Optional
import asyncio
import threading

from database import get_db, engine
from models import Base, Document
from schemas import DocumentCreate, DocumentResponse, TextExtractionResponse
from pdf_text_extractor import extract_text_from_pdf
from vision_ocr import process_pdf_with_ocr

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Upload API",
    description="API for uploading PDF documents with user and statement information",
    version="1.0.0"
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def process_document_text_extraction(document_id: int, file_path: str, db: Session):
    """
    Process text extraction for a document (runs in background)
    """
    try:
        # Extract text using Poppler
        poppler_result = extract_text_from_pdf(file_path)
        
        # Extract text using Vision OCR
        ocr_result = process_pdf_with_ocr(file_path)
        
        # Update database with results
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            # Update Poppler results
            document.poppler_extraction_success = poppler_result.get("success", False)
            if poppler_result.get("success"):
                document.poppler_text = poppler_result.get("text", "")
                document.poppler_word_count = poppler_result.get("word_count", 0)
                document.poppler_pages = poppler_result.get("pages", 0)
            
            # Update OCR results
            document.ocr_extraction_success = ocr_result.get("success", False)
            if ocr_result.get("success"):
                document.ocr_text = ocr_result.get("complete_text", "")
                document.ocr_word_count = len(ocr_result.get("complete_text", "").split())
                document.ocr_pages = ocr_result.get("total_pages", 0)
                # Calculate average confidence
                pages = ocr_result.get("pages", {})
                if pages:
                    avg_confidence = sum(page.get("confidence", 0) for page in pages.values()) / len(pages)
                    document.ocr_confidence = int(avg_confidence * 100)  # Convert to percentage
            
            document.text_processing_completed = True
            db.commit()
            
    except Exception as e:
        # Log error and update database
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.text_processing_error = str(e)
            document.text_processing_completed = True
            db.commit()

@app.get("/")
async def root():
    return {"message": "Document Upload API is running"}

@app.post("/upload-document/", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    statement_id: str = Form(...),
    pdf_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document with user ID and statement ID
    """
    # Validate file type
    if not pdf_file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size (max 10MB)
    if pdf_file.size and pdf_file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        # Generate unique filename
        file_extension = os.path.splitext(pdf_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            content = await pdf_file.read()
            await f.write(content)
        
        # Create document record in database
        document_data = DocumentCreate(
            user_id=user_id,
            statement_id=statement_id,
            original_filename=pdf_file.filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_size=len(content),
            upload_date=datetime.utcnow()
        )
        
        db_document = Document(**document_data.model_dump())
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Add background task for text extraction
        background_tasks.add_task(process_document_text_extraction, db_document.id, file_path, db)
        
        return DocumentResponse(
            id=db_document.id,
            user_id=db_document.user_id,
            statement_id=db_document.statement_id,
            original_filename=db_document.original_filename,
            file_size=db_document.file_size,
            upload_date=db_document.upload_date,
            poppler_extraction_success=db_document.poppler_extraction_success,
            poppler_word_count=db_document.poppler_word_count,
            poppler_pages=db_document.poppler_pages,
            ocr_extraction_success=db_document.ocr_extraction_success,
            ocr_word_count=db_document.ocr_word_count,
            ocr_pages=db_document.ocr_pages,
            ocr_confidence=db_document.ocr_confidence,
            text_processing_completed=db_document.text_processing_completed,
            message="Document uploaded successfully. Text extraction is processing in background."
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/documents/", response_model=list[DocumentResponse])
async def get_documents(
    user_id: Optional[str] = None,
    statement_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve documents with optional filtering by user_id or statement_id
    """
    query = db.query(Document)
    
    if user_id:
        query = query.filter(Document.user_id == user_id)
    if statement_id:
        query = query.filter(Document.statement_id == statement_id)
    
    documents = query.all()
    
    return [
        DocumentResponse(
            id=doc.id,
            user_id=doc.user_id,
            statement_id=doc.statement_id,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            upload_date=doc.upload_date,
            message="Document retrieved successfully"
        )
        for doc in documents
    ]

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific document by ID
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=document.id,
        user_id=document.user_id,
        statement_id=document.statement_id,
        original_filename=document.original_filename,
        file_size=document.file_size,
        upload_date=document.upload_date,
        message="Document retrieved successfully"
    )

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document by ID
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file from disk
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete record from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.post("/documents/{document_id}/extract-text", response_model=TextExtractionResponse)
async def extract_document_text(document_id: int, db: Session = Depends(get_db)):
    """
    Manually trigger text extraction for a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    
    try:
        # Extract text using Poppler
        poppler_result = extract_text_from_pdf(document.file_path)
        
        # Extract text using Vision OCR
        ocr_result = process_pdf_with_ocr(document.file_path)
        
        # Update database with results
        document.poppler_extraction_success = poppler_result.get("success", False)
        if poppler_result.get("success"):
            document.poppler_text = poppler_result.get("text", "")
            document.poppler_word_count = poppler_result.get("word_count", 0)
            document.poppler_pages = poppler_result.get("pages", 0)
        
        document.ocr_extraction_success = ocr_result.get("success", False)
        if ocr_result.get("success"):
            document.ocr_text = ocr_result.get("complete_text", "")
            document.ocr_word_count = len(ocr_result.get("complete_text", "").split())
            document.ocr_pages = ocr_result.get("total_pages", 0)
            # Calculate average confidence
            pages = ocr_result.get("pages", {})
            if pages:
                avg_confidence = sum(page.get("confidence", 0) for page in pages.values()) / len(pages)
                document.ocr_confidence = int(avg_confidence * 100)
        
        document.text_processing_completed = True
        db.commit()
        
        # Calculate similarity if both methods succeeded
        similarity_score = None
        if (poppler_result.get("success") and ocr_result.get("success")):
            poppler_words = set(poppler_result.get("text", "").lower().split())
            ocr_words = set(ocr_result.get("complete_text", "").lower().split())
            if poppler_words and ocr_words:
                overlap = len(poppler_words.intersection(ocr_words))
                total_unique = len(poppler_words.union(ocr_words))
                similarity_score = overlap / total_unique if total_unique > 0 else 0
        
        return TextExtractionResponse(
            document_id=document.id,
            poppler_success=poppler_result.get("success", False),
            poppler_text_length=len(poppler_result.get("text", "")),
            poppler_word_count=poppler_result.get("word_count", 0),
            poppler_pages=poppler_result.get("pages", 0),
            ocr_success=ocr_result.get("success", False),
            ocr_text_length=len(ocr_result.get("complete_text", "")),
            ocr_word_count=len(ocr_result.get("complete_text", "").split()),
            ocr_pages=ocr_result.get("total_pages", 0),
            ocr_confidence=ocr_result.get("pages", {}).get(1, {}).get("confidence", 0.0) if ocr_result.get("pages") else 0.0,
            similarity_score=similarity_score,
            message="Text extraction completed successfully"
        )
        
    except Exception as e:
        document.text_processing_error = str(e)
        document.text_processing_completed = True
        db.commit()
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")

@app.get("/documents/{document_id}/text")
async def get_document_text(document_id: int, db: Session = Depends(get_db)):
    """
    Get extracted text from a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document.id,
        "poppler": {
            "success": document.poppler_extraction_success,
            "text": document.poppler_text,
            "word_count": document.poppler_word_count,
            "pages": document.poppler_pages
        },
        "ocr": {
            "success": document.ocr_extraction_success,
            "text": document.ocr_text,
            "word_count": document.ocr_word_count,
            "pages": document.ocr_pages,
            "confidence": document.ocr_confidence
        },
        "processing_completed": document.text_processing_completed,
        "error": document.text_processing_error
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 