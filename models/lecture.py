"""Lecture model for storing lecture metadata and transcripts."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.connection import Base
import enum


class LectureType(enum.Enum):
    """Enum for lecture types."""
    LIVE = "live"
    UPLOAD = "upload"


class ProcessingStatus(enum.Enum):
    """Enum for processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Lecture(Base):
    """
    Lecture model representing a recorded or live lecture session.
    
    Attributes:
        id: Unique identifier for the lecture
        user_id: Foreign key to the user who owns this lecture
        title: Title of the lecture
        lecture_type: Type of lecture ('live' or 'upload')
        audio_file_path: Path to stored audio file (optional)
        transcript: Full transcript text
        created_at: Timestamp when lecture was created
        duration_seconds: Duration of the lecture in seconds
        processing_status: Current processing status
    """
    __tablename__ = "lectures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    lecture_type = Column(Enum(LectureType), nullable=False)
    audio_file_path = Column(String(1000), nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="lectures")
    study_notes = relationship("StudyNotes", back_populates="lecture", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lecture(id={self.id}, title={self.title}, type={self.lecture_type.value})>"
