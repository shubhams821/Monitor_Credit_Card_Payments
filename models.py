from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime



class User(Base):
    """User account model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to documents
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")




class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_id = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Text extraction fields
    poppler_text = Column(Text, nullable=True)
    poppler_word_count = Column(Integer, nullable=True)
    poppler_pages = Column(Integer, nullable=True)
    poppler_extraction_success = Column(Boolean, default=False)
    
    # OCR fields
    ocr_text = Column(Text, nullable=True)
    ocr_word_count = Column(Integer, nullable=True)
    ocr_pages = Column(Integer, nullable=True)
    ocr_extraction_success = Column(Boolean, default=False)
    ocr_confidence = Column(Integer, nullable=True)  # Store as percentage (0-100)
    
    # Processing status
    text_processing_completed = Column(Boolean, default=False)
    text_processing_error = Column(Text, nullable=True)

    # Relationship to user
    user = relationship("User", back_populates="documents")

    # Relationship to transaction details
    transaction_details = relationship(
        "TransactionDetails",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Document(id={self.id}, user_id='{self.user_id}', statement_id='{self.statement_id}')>"


class TransactionDetails(Base):
    __tablename__ = "transaction_details"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(String(255), ForeignKey("documents.statement_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction information
    transaction_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=True)
    transaction_type = Column(String(50), nullable=True)  # debit, credit, etc.
    balance = Column(Numeric(precision=15, scale=2), nullable=True)
    reference_number = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    
    # Processing metadata
    extraction_source = Column(String(50), nullable=True)  # poppler or ocr
    confidence_score = Column(Numeric(precision=5, scale=4), nullable=True)  # 0-1 confidence
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    llm_raw_response = Column(Text, nullable=True)  # Store the original LLM response
    
    # Processing status
    processing_completed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship back to document
    document = relationship("Document", back_populates="transaction_details")
    # statement = relationship("Statement", back_populates="transactions")

    def __repr__(self):
        return f"<TransactionDetails(id={self.id}, statement_id='{self.statement_id}', amount={self.amount})>" 