"""Integration tests for notes and lectures API endpoints."""

import pytest
import uuid
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Create test-specific models for SQLite compatibility
TestBase = declarative_base()


class TestLecture(TestBase):
    """Test Lecture model compatible with SQLite."""
    __tablename__ = "lectures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    lecture_type = Column(String(20), nullable=False)
    audio_file_path = Column(String(1000), nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    processing_status = Column(String(20), default="pending", nullable=False)


class TestStudyNotes(TestBase):
    """Test StudyNotes model compatible with SQLite."""
    __tablename__ = "study_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lecture_id = Column(String(36), nullable=False, unique=True, index=True)
    topics = Column(Text, nullable=False, default="[]")
    summary = Column(Text, nullable=False, default="")
    key_points = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def test_notes_and_lectures_endpoints_exist():
    """Test that the API endpoints are properly defined."""
    # Import the routers
    from api.notes import router as notes_router
    from api.lectures import router as lectures_router
    
    # Verify routers have the expected routes
    notes_routes = [route.path for route in notes_router.routes]
    lectures_routes = [route.path for route in lectures_router.routes]
    
    # Check notes endpoints
    assert "/api/notes/{lecture_id}" in notes_routes
    assert "/api/notes/{lecture_id}/pdf" in notes_routes
    
    # Check lectures endpoints
    assert "/api/lectures" in lectures_routes or "/api/lectures/" in lectures_routes
    assert "/api/lectures/{lecture_id}" in lectures_routes


def test_endpoint_structure():
    """Test that endpoints have proper structure and dependencies."""
    from api.notes import get_notes, download_pdf
    from api.lectures import list_lectures, get_lecture, delete_lecture
    
    # Verify functions exist
    assert callable(get_notes)
    assert callable(download_pdf)
    assert callable(list_lectures)
    assert callable(get_lecture)
    assert callable(delete_lecture)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
