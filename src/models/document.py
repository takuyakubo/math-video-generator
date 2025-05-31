from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum

Base = declarative_base()

class DocumentType(PyEnum):
    PDF = "pdf"
    LATEX = "latex"
    MARKDOWN = "markdown"

class ProcessingStatus(PyEnum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    GENERATING_SLIDES = "generating_slides"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Metadata
    title = Column(String)
    author = Column(String)
    abstract = Column(Text)
    
    # Processing
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    error_message = Column(Text)
    processing_config = Column(JSON)
    
    # Structure
    chapters = Column(JSON)  # List of chapter metadata
    total_pages = Column(Integer)
    
    # Output
    video_path = Column(String)
    slides_path = Column(String)
    audio_path = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())