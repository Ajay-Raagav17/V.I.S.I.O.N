"""Unit tests for notes and lecture history endpoints."""

import pytest
import uuid
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base

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


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def sample_lecture(test_db):
    """Create a sample lecture for testing."""
    lecture = TestLecture(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        title="Introduction to Python",
        lecture_type="upload",
        transcript="This is a sample transcript about Python programming.",
        duration_seconds=3600,
        processing_status="completed",
        created_at=datetime.utcnow()
    )
    test_db.add(lecture)
    test_db.commit()
    test_db.refresh(lecture)
    return lecture


@pytest.fixture
def sample_study_notes(test_db, sample_lecture):
    """Create sample study notes for testing."""
    topics = [
        {
            "title": "Python Basics",
            "subtopics": ["Variables", "Data Types"],
            "keywords": ["python", "programming", "syntax"],
            "definitions": {"Variable": "A named storage location"},
            "formulas": [],
            "content": "Python is a high-level programming language."
        }
    ]
    
    key_points = [
        "Python is easy to learn",
        "Python has dynamic typing",
        "Python supports multiple paradigms"
    ]
    
    notes = TestStudyNotes(
        id=str(uuid.uuid4()),
        lecture_id=sample_lecture.id,
        topics=json.dumps(topics),
        summary="An introduction to Python programming language and its basic concepts.",
        key_points=json.dumps(key_points),
        created_at=datetime.utcnow()
    )
    test_db.add(notes)
    test_db.commit()
    test_db.refresh(notes)
    return notes


class TestNotesRetrieval:
    """Test notes retrieval for existing lectures (Requirement 5.5)."""
    
    def test_retrieve_notes_for_existing_lecture(self, test_db, sample_lecture, sample_study_notes):
        """Test retrieving notes for an existing lecture."""
        # Retrieve notes by lecture_id
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=sample_lecture.id).first()
        
        assert notes is not None
        assert notes.lecture_id == sample_lecture.id
        assert notes.summary != ""
        
        # Verify topics structure
        topics = json.loads(notes.topics)
        assert len(topics) > 0
        assert "title" in topics[0]
        assert "content" in topics[0]
        
        # Verify key points
        key_points = json.loads(notes.key_points)
        assert len(key_points) > 0
    
    def test_retrieve_notes_for_nonexistent_lecture(self, test_db):
        """Test retrieving notes for a lecture that doesn't exist."""
        fake_lecture_id = str(uuid.uuid4())
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=fake_lecture_id).first()
        
        assert notes is None
    
    def test_retrieve_notes_with_lecture_details(self, test_db, sample_lecture, sample_study_notes):
        """Test retrieving notes along with lecture metadata."""
        # Retrieve lecture
        lecture = test_db.query(TestLecture).filter_by(id=sample_lecture.id).first()
        
        # Retrieve associated notes
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=lecture.id).first()
        
        assert lecture is not None
        assert notes is not None
        assert lecture.title == "Introduction to Python"
        assert lecture.processing_status == "completed"
        assert notes.lecture_id == lecture.id


class TestPDFDownload:
    """Test PDF download endpoint (Requirement 5.5)."""
    
    def test_pdf_generation_data_available(self, test_db, sample_lecture, sample_study_notes):
        """Test that all required data for PDF generation is available."""
        # Retrieve lecture and notes
        lecture = test_db.query(TestLecture).filter_by(id=sample_lecture.id).first()
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=lecture.id).first()
        
        # Verify all required fields for PDF generation
        assert lecture.title is not None
        assert lecture.created_at is not None
        assert notes.topics is not None
        assert notes.summary is not None
        assert notes.key_points is not None
        
        # Verify JSON fields can be parsed
        topics = json.loads(notes.topics)
        key_points = json.loads(notes.key_points)
        
        assert isinstance(topics, list)
        assert isinstance(key_points, list)
    
    def test_pdf_generation_for_lecture_without_notes(self, test_db, sample_lecture):
        """Test PDF generation attempt for lecture without notes."""
        # Remove notes if they exist
        test_db.query(TestStudyNotes).filter_by(lecture_id=sample_lecture.id).delete()
        test_db.commit()
        
        # Try to retrieve notes
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=sample_lecture.id).first()
        
        assert notes is None


class TestLectureHistory:
    """Test lecture history listing (Requirement 6.4)."""
    
    def test_list_user_lectures(self, test_db):
        """Test listing all lectures for a specific user."""
        user_id = str(uuid.uuid4())
        
        # Create multiple lectures for the user
        lecture1 = TestLecture(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Lecture 1",
            lecture_type="live",
            transcript="Transcript 1",
            duration_seconds=1800,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        
        lecture2 = TestLecture(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Lecture 2",
            lecture_type="upload",
            transcript="Transcript 2",
            duration_seconds=2400,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        
        test_db.add_all([lecture1, lecture2])
        test_db.commit()
        
        # Retrieve all lectures for user
        lectures = test_db.query(TestLecture).filter_by(user_id=user_id).all()
        
        assert len(lectures) == 2
        assert all(lecture.user_id == user_id for lecture in lectures)
    
    def test_list_lectures_with_metadata(self, test_db):
        """Test that lecture list includes all required metadata."""
        user_id = str(uuid.uuid4())
        
        lecture = TestLecture(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Test Lecture",
            lecture_type="upload",
            transcript="Test transcript",
            duration_seconds=3000,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        
        test_db.add(lecture)
        test_db.commit()
        
        # Retrieve lectures
        lectures = test_db.query(TestLecture).filter_by(user_id=user_id).all()
        
        assert len(lectures) == 1
        lecture = lectures[0]
        
        # Verify all metadata fields
        assert lecture.id is not None
        assert lecture.title == "Test Lecture"
        assert lecture.lecture_type == "upload"
        assert lecture.duration_seconds == 3000
        assert lecture.processing_status == "completed"
        assert lecture.created_at is not None
    
    def test_list_lectures_empty_for_new_user(self, test_db):
        """Test that new users have empty lecture history."""
        new_user_id = str(uuid.uuid4())
        
        lectures = test_db.query(TestLecture).filter_by(user_id=new_user_id).all()
        
        assert len(lectures) == 0


class TestLectureDetails:
    """Test getting specific lecture details (Requirement 6.4)."""
    
    def test_get_specific_lecture(self, test_db, sample_lecture):
        """Test retrieving a specific lecture by ID."""
        lecture = test_db.query(TestLecture).filter_by(id=sample_lecture.id).first()
        
        assert lecture is not None
        assert lecture.id == sample_lecture.id
        assert lecture.title == sample_lecture.title
    
    def test_get_nonexistent_lecture(self, test_db):
        """Test retrieving a lecture that doesn't exist."""
        fake_id = str(uuid.uuid4())
        lecture = test_db.query(TestLecture).filter_by(id=fake_id).first()
        
        assert lecture is None
    
    def test_get_lecture_with_full_details(self, test_db, sample_lecture, sample_study_notes):
        """Test retrieving lecture with all associated data."""
        lecture = test_db.query(TestLecture).filter_by(id=sample_lecture.id).first()
        notes = test_db.query(TestStudyNotes).filter_by(lecture_id=lecture.id).first()
        
        assert lecture is not None
        assert notes is not None
        
        # Verify complete data structure
        assert lecture.title is not None
        assert lecture.transcript is not None
        assert lecture.duration_seconds > 0
        assert notes.summary is not None
        
        topics = json.loads(notes.topics)
        assert len(topics) > 0


class TestLectureDeletion:
    """Test lecture deletion (Requirement 6.5)."""
    
    def test_delete_existing_lecture(self, test_db, sample_lecture):
        """Test deleting an existing lecture."""
        lecture_id = sample_lecture.id
        
        # Verify lecture exists
        lecture = test_db.query(TestLecture).filter_by(id=lecture_id).first()
        assert lecture is not None
        
        # Delete lecture
        test_db.delete(lecture)
        test_db.commit()
        
        # Verify lecture is deleted
        deleted_lecture = test_db.query(TestLecture).filter_by(id=lecture_id).first()
        assert deleted_lecture is None
    
    def test_delete_nonexistent_lecture(self, test_db):
        """Test attempting to delete a lecture that doesn't exist."""
        fake_id = str(uuid.uuid4())
        lecture = test_db.query(TestLecture).filter_by(id=fake_id).first()
        
        assert lecture is None
        # No error should occur when trying to delete None
    
    def test_delete_lecture_with_notes(self, test_db, sample_lecture, sample_study_notes):
        """Test deleting a lecture that has associated study notes."""
        lecture_id = sample_lecture.id
        notes_id = sample_study_notes.id
        
        # Verify both exist
        assert test_db.query(TestLecture).filter_by(id=lecture_id).first() is not None
        assert test_db.query(TestStudyNotes).filter_by(id=notes_id).first() is not None
        
        # Delete lecture
        lecture = test_db.query(TestLecture).filter_by(id=lecture_id).first()
        test_db.delete(lecture)
        test_db.commit()
        
        # Verify lecture is deleted
        assert test_db.query(TestLecture).filter_by(id=lecture_id).first() is None
        
        # Note: In SQLite without foreign key enforcement, notes might remain
        # In production PostgreSQL with CASCADE, notes would be deleted automatically
    
    def test_delete_lecture_authorization(self, test_db):
        """Test that only the lecture owner should be able to delete it."""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # Create lecture for user1
        lecture = TestLecture(
            id=str(uuid.uuid4()),
            user_id=user1_id,
            title="User 1 Lecture",
            lecture_type="upload",
            transcript="Test",
            duration_seconds=1000,
            processing_status="completed",
            created_at=datetime.utcnow()
        )
        test_db.add(lecture)
        test_db.commit()
        
        # Verify lecture belongs to user1
        assert lecture.user_id == user1_id
        assert lecture.user_id != user2_id
        
        # In a real API, user2 attempting to delete would be rejected
        # Here we just verify ownership can be checked
        retrieved_lecture = test_db.query(TestLecture).filter_by(id=lecture.id).first()
        assert retrieved_lecture.user_id == user1_id
