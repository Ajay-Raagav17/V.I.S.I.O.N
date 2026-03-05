"""Study notes model for storing AI-generated structured notes."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.connection import Base


class StudyNotes(Base):
    """
    Study notes model representing AI-generated structured notes.
    
    Attributes:
        id: Unique identifier for the study notes
        lecture_id: Foreign key to the associated lecture
        topics: JSON array of topic objects with structure
        summary: Text summary of the lecture
        key_points: JSON array of key learning points
        created_at: Timestamp when notes were generated
    
    Topic structure in JSON:
    {
        "title": str,
        "subtopics": List[str],
        "keywords": List[str],
        "definitions": Dict[str, str],
        "formulas": List[str],
        "content": str
    }
    """
    __tablename__ = "study_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecture_id = Column(UUID(as_uuid=True), ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    topics = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=False, default="")
    key_points = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lecture = relationship("Lecture", back_populates="study_notes")
    
    def __repr__(self):
        return f"<StudyNotes(id={self.id}, lecture_id={self.lecture_id})>"
