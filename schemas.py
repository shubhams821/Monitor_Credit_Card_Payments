from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for data stored in JWT token"""
    user_id: Optional[str] = None
    
class DocumentBase(BaseModel):
    user_id: int
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
    user_id: int
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


# Transaction Details Schemas
class TransactionDetailsBase(BaseModel):
    statement_id: str
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    balance: Optional[Decimal] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None
    extraction_source: Optional[str] = None
    confidence_score: Optional[Decimal] = None

class TransactionDetailsCreate(TransactionDetailsBase):
    pass

class TransactionDetailsResponse(BaseModel):
    id: int
    statement_id: str
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    balance: Optional[Decimal] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None
    extraction_source: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    processed_at: datetime
    processing_completed: bool
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionDetailsUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    balance: Optional[Decimal] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None

class TransactionExtractionResponse(BaseModel):
    document_id: int
    statement_id: str
    total_transactions: int
    successful_extractions: int
    failed_extractions: int
    processing_time_seconds: float
    message: str
    transactions: List[TransactionDetailsResponse] 