from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
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

    def __repr__(self):
        return f"<Document(id={self.id}, user_id='{self.user_id}', statement_id='{self.statement_id}')>" 