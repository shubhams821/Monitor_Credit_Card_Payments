from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import aiofiles
import os
from datetime import datetime
import uuid
from typing import Optional
import asyncio
import threading
import time
import logging

from database import get_db, engine
from models import Base, Document, TransactionDetails
from schemas import (
    DocumentCreate, DocumentResponse, TextExtractionResponse,
    TransactionDetailsResponse, TransactionExtractionResponse
)
from pdf_text_extractor import extract_text_from_pdf
from vision_ocr import process_pdf_with_ocr
from transaction_extractor import TransactionExtractor

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document Upload API",
    description="API for uploading PDF documents with user and statement information",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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


def process_transaction_extraction(statement_id: str, db: Session):
    """
    Process transaction extraction for a statement (runs in background)
    """
    start_time = time.time()
    extractor = TransactionExtractor()
    
    try:
        # Get the document by statement_id
        document = db.query(Document).filter(Document.statement_id == statement_id).first()
        if not document:
            logging.error(f"Document not found for statement_id: {statement_id}")
            return
        
        # Determine which text to use for extraction
        text_to_extract = None
        extraction_source = None
        
        # Prefer OCR text if available and successful, otherwise use Poppler
        
        if document.poppler_extraction_success and document.poppler_text:
            text_to_extract = document.poppler_text
            extraction_source = "poppler"
            
        elif document.ocr_extraction_success and document.ocr_text:
            text_to_extract = document.ocr_text
            extraction_source = "ocr"
        else:
            logging.warning(f"No extracted text available for statement_id: {statement_id}")
            return
        
        # Extract transactions using LLM
        extraction_result = extractor.extract_transactions(text_to_extract, statement_id)
        
        if extraction_result["success"]:
            # Save each transaction to database
            saved_count = 0
            failed_count = 0
            
            for transaction_data in extraction_result["transactions"]:
                try:
                    # Set extraction source
                    transaction_data["extraction_source"] = extraction_source
                    
                    # Create transaction record
                    transaction = TransactionDetails(**transaction_data)
                    db.add(transaction)
                    db.commit()
                    db.refresh(transaction)
                    saved_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save transaction for statement {statement_id}: {e}")
                    failed_count += 1
                    db.rollback()
            
            processing_time = time.time() - start_time
            logging.info(f"Transaction extraction completed for statement {statement_id}: "
                        f"{saved_count} saved, {failed_count} failed, "
                        f"processing time: {processing_time:.2f}s")
        
        else:
            logging.error(f"Transaction extraction failed for statement {statement_id}: "
                         f"{extraction_result.get('error', 'Unknown error')}")
            
            # Save error record
            error_transaction = TransactionDetails(
                statement_id=statement_id,
                description=f"Transaction extraction failed: {extraction_result.get('error', 'Unknown error')}",
                extraction_source=extraction_source,
                processing_completed=False,
                processing_error=extraction_result.get('error', 'Unknown error'),
                llm_raw_response=extraction_result.get('raw_response')
            )
            db.add(error_transaction)
            db.commit()
            
    except Exception as e:
        processing_time = time.time() - start_time
        logging.error(f"Transaction extraction process failed for statement {statement_id}: {e}")
        
        # Save error record
        try:
            error_transaction = TransactionDetails(
                statement_id=statement_id,
                description=f"Transaction extraction process failed: {str(e)}",
                processing_completed=False,
                processing_error=str(e)
            )
            db.add(error_transaction)
            db.commit()
        except Exception as save_error:
            logging.error(f"Failed to save error record: {save_error}")


def enhanced_process_document_text_extraction(document_id: int, file_path: str, db: Session):
    """
    Enhanced process that includes both text extraction and transaction extraction
    """
    # First run the original text extraction
    process_document_text_extraction(document_id, file_path, db)
    
    # Then trigger transaction extraction
    document = db.query(Document).filter(Document.id == document_id).first()
    if document and document.text_processing_completed:
        # Run transaction extraction in a separate thread to avoid blocking
        threading.Thread(
            target=process_transaction_extraction,
            args=(document.statement_id, db),
            daemon=True
        ).start()

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
        
        # Add background task for enhanced text extraction (includes transaction extraction)
        background_tasks.add_task(enhanced_process_document_text_extraction, db_document.id, file_path, db)
        
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


# Transaction Details Endpoints

@app.get("/statements/{statement_id}/transactions", response_model=list[TransactionDetailsResponse])
async def get_transactions_by_statement(statement_id: str, db: Session = Depends(get_db)):
    """
    Get all transactions for a specific statement
    """
    transactions = db.query(TransactionDetails).filter(
        TransactionDetails.statement_id == statement_id
    ).order_by(TransactionDetails.transaction_date.desc()).all()
    
    return transactions


@app.get("/transactions/{transaction_id}", response_model=TransactionDetailsResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Get a specific transaction by ID
    """
    transaction = db.query(TransactionDetails).filter(
        TransactionDetails.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@app.post("/statements/{statement_id}/extract-transactions", response_model=TransactionExtractionResponse)
async def manually_extract_transactions(
    statement_id: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually trigger transaction extraction for a statement
    """
    start_time = time.time()
    
    # Check if document exists
    document = db.query(Document).filter(Document.statement_id == statement_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    # Check if text extraction is completed
    if not document.text_processing_completed:
        raise HTTPException(
            status_code=400, 
            detail="Text extraction not completed. Please wait for text processing to finish."
        )
    
    try:
        # Run transaction extraction in background
        background_tasks.add_task(process_transaction_extraction, statement_id, db)
        
        # Return existing transactions if any
        existing_transactions = db.query(TransactionDetails).filter(
            TransactionDetails.statement_id == statement_id
        ).all()
        
        processing_time = time.time() - start_time
        
        return TransactionExtractionResponse(
            document_id=document.id,
            statement_id=statement_id,
            total_transactions=len(existing_transactions),
            successful_extractions=len([t for t in existing_transactions if t.processing_completed]),
            failed_extractions=len([t for t in existing_transactions if not t.processing_completed]),
            processing_time_seconds=processing_time,
            message="Transaction extraction started in background. Existing transactions returned.",
            transactions=existing_transactions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start transaction extraction: {str(e)}")


@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific transaction
    """
    transaction = db.query(TransactionDetails).filter(
        TransactionDetails.id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    try:
        db.delete(transaction)
        db.commit()
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete transaction: {str(e)}")


@app.delete("/statements/{statement_id}/transactions")
async def delete_all_transactions(statement_id: str, db: Session = Depends(get_db)):
    """
    Delete all transactions for a statement
    """
    try:
        deleted_count = db.query(TransactionDetails).filter(
            TransactionDetails.statement_id == statement_id
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Successfully deleted {deleted_count} transactions for statement {statement_id}",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete transactions: {str(e)}")


@app.get("/statements/{statement_id}/transactions/summary")
async def get_transaction_summary(statement_id: str, db: Session = Depends(get_db)):
    """
    Get transaction summary for a statement
    """
    transactions = db.query(TransactionDetails).filter(
        TransactionDetails.statement_id == statement_id,
        TransactionDetails.processing_completed == True
    ).all()
    
    if not transactions:
        return {
            "statement_id": statement_id,
            "total_transactions": 0,
            "total_credits": 0,
            "total_debits": 0,
            "net_amount": 0,
            "categories": {},
            "date_range": None
        }
    
    # Calculate summary statistics
    total_credits = sum(t.amount for t in transactions if t.amount and t.amount > 0)
    total_debits = sum(abs(t.amount) for t in transactions if t.amount and t.amount < 0)
    net_amount = total_credits - total_debits
    
    # Category breakdown
    categories = {}
    for transaction in transactions:
        if transaction.category:
            if transaction.category not in categories:
                categories[transaction.category] = {"count": 0, "amount": 0}
            categories[transaction.category]["count"] += 1
            if transaction.amount:
                categories[transaction.category]["amount"] += float(transaction.amount)
    
    # Date range
    valid_dates = [t.transaction_date for t in transactions if t.transaction_date]
    date_range = None
    if valid_dates:
        date_range = {
            "earliest": min(valid_dates),
            "latest": max(valid_dates)
        }
    
    return {
        "statement_id": statement_id,
        "total_transactions": len(transactions),
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "net_amount": float(net_amount),
        "categories": categories,
        "date_range": date_range
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 