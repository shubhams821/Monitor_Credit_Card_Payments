from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentBase(BaseModel):
    user_id: str
    statement_id: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    upload_date: datetime

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(BaseModel):
    id: int
    user_id: str
    statement_id: str
    original_filename: str
    file_size: int
    upload_date: datetime
    message: str
    # Text extraction info
    poppler_extraction_success: Optional[bool] = None
    poppler_word_count: Optional[int] = None
    poppler_pages: Optional[int] = None
    ocr_extraction_success: Optional[bool] = None
    ocr_word_count: Optional[int] = None
    ocr_pages: Optional[int] = None
    ocr_confidence: Optional[int] = None
    text_processing_completed: Optional[bool] = None

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    user_id: Optional[str] = None
    statement_id: Optional[str] = None

class TextExtractionResponse(BaseModel):
    document_id: int
    poppler_success: bool
    poppler_text_length: int
    poppler_word_count: int
    poppler_pages: int
    ocr_success: bool
    ocr_text_length: int
    ocr_word_count: int
    ocr_pages: int
    ocr_confidence: float
    similarity_score: Optional[float] = None
    message: str 