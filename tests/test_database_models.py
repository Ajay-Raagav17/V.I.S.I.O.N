"""
Unit tests for database models.

Tests model creation, validation, and CRUD operations.
Requirements: 6.1, 6.3
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import postgresql
from database.connection import Base
from models.user import User
from models.lecture import Lecture, LectureType, ProcessingStatus
from models.study_notes import StudyNotes


# Test database setup - use PostgreSQL-style URL but with SQLite
# We'll handle UUID compatibility through type compilation
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create a test database engine with UUID support for SQLite."""
    from sqlalchemy.types import TypeDecorator, CHAR
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    import uuid as uuid_module
    
    # Create engine
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    
    # Register UUID type compiler for SQLite
    from sqlalchemy import types
    from sqlalchemy.dialects.sqlite import base as sqlite_base
    
    # Monkey-patch UUID support into SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Override UUID type for SQLite
    original_visit_UUID = None
    if hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID'):
        original_visit_UUID = sqlite_base.SQLiteTypeCompiler.visit_UUID
    
    def visit_UUID(self, type_, **kw):
        return "CHAR(36)"
    
    sqlite_base.SQLiteTypeCompiler.visit_UUID = visit_UUID
    
    # Create tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()
    
    # Restore original if it existed
    if original_visit_UUID:
        sqlite_base.SQLiteTypeCompiler.visit_UUID = original_visit_UUID
    elif hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID'):
        delattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID')


@pytest.fixture
def session(engine):
    """Create a test database session."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.mark.unit
class TestUserModel:
    """Test User model creation and validation."""
    
    def test_create_user(self, session):
        """Test creating a user with valid data."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password_123"
        )
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
        assert user.last_login is None
    
    def test_user_email_unique(self, session):
        """Test that user email must be unique."""
        user1 = User(email="test@example.com", password_hash="hash1")
        session.add(user1)
        session.commit()
        
        user2 = User(email="test@example.com", password_hash="hash2")
        session.add(user2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            session.commit()
    
    def test_user_repr(self, session):
        """Test user string representation."""
        user = User(email="test@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert str(user.id) in repr_str
        assert "test@example.com" in repr_str


@pytest.mark.unit
class TestLectureModel:
    """Test Lecture model creation and validation."""
    
    def test_create_lecture(self, session):
        """Test creating a lecture with valid data."""
        # Create user first
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        # Create lecture
        lecture = Lecture(
            user_id=user.id,
            title="Introduction to Python",
            lecture_type=LectureType.UPLOAD,
            audio_file_path="/path/to/audio.mp3",
            transcript="This is a test transcript",
            duration_seconds=3600
        )
        session.add(lecture)
        session.commit()
        
        assert lecture.id is not None
        assert lecture.user_id == user.id
        assert lecture.title == "Introduction to Python"
        assert lecture.lecture_type == LectureType.UPLOAD
        assert lecture.audio_file_path == "/path/to/audio.mp3"
        assert lecture.transcript == "This is a test transcript"
        assert lecture.duration_seconds == 3600
        assert lecture.processing_status == ProcessingStatus.PENDING
        assert lecture.created_at is not None
    
    def test_lecture_type_enum(self, session):
        """Test lecture type enum values."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        # Test LIVE type
        lecture_live = Lecture(
            user_id=user.id,
            title="Live Lecture",
            lecture_type=LectureType.LIVE
        )
        session.add(lecture_live)
        session.commit()
        assert lecture_live.lecture_type == LectureType.LIVE
        
        # Test UPLOAD type
        lecture_upload = Lecture(
            user_id=user.id,
            title="Uploaded Lecture",
            lecture_type=LectureType.UPLOAD
        )
        session.add(lecture_upload)
        session.commit()
        assert lecture_upload.lecture_type == LectureType.UPLOAD
    
    def test_lecture_processing_status(self, session):
        """Test lecture processing status enum."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.LIVE,
            processing_status=ProcessingStatus.PROCESSING
        )
        session.add(lecture)
        session.commit()
        
        assert lecture.processing_status == ProcessingStatus.PROCESSING
        
        # Update status
        lecture.processing_status = ProcessingStatus.COMPLETED
        session.commit()
        assert lecture.processing_status == ProcessingStatus.COMPLETED
    
    def test_lecture_user_relationship(self, session):
        """Test relationship between lecture and user."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.LIVE
        )
        session.add(lecture)
        session.commit()
        
        # Access user through relationship
        assert lecture.user.email == "student@example.com"
        
        # Access lectures through user
        assert len(user.lectures) == 1
        assert user.lectures[0].title == "Test Lecture"
    
    def test_lecture_cascade_delete(self, session):
        """Test that deleting a user deletes their lectures."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.LIVE
        )
        session.add(lecture)
        session.commit()
        
        lecture_id = lecture.id
        
        # Delete user
        session.delete(user)
        session.commit()
        
        # Lecture should be deleted
        deleted_lecture = session.query(Lecture).filter_by(id=lecture_id).first()
        assert deleted_lecture is None


@pytest.mark.unit
class TestStudyNotesModel:
    """Test StudyNotes model creation and validation."""
    
    def test_create_study_notes(self, session):
        """Test creating study notes with valid data."""
        # Create user and lecture first
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.UPLOAD
        )
        session.add(lecture)
        session.commit()
        
        # Create study notes
        topics = [
            {
                "title": "Introduction",
                "subtopics": ["Overview", "Goals"],
                "keywords": ["python", "programming"],
                "definitions": {"variable": "A named storage location"},
                "formulas": [],
                "content": "Introduction to programming"
            }
        ]
        key_points = ["Learn Python basics", "Understand variables"]
        
        notes = StudyNotes(
            lecture_id=lecture.id,
            topics=topics,
            summary="This lecture covers Python basics",
            key_points=key_points
        )
        session.add(notes)
        session.commit()
        
        assert notes.id is not None
        assert notes.lecture_id == lecture.id
        assert len(notes.topics) == 1
        assert notes.topics[0]["title"] == "Introduction"
        assert notes.summary == "This lecture covers Python basics"
        assert len(notes.key_points) == 2
        assert notes.created_at is not None
    
    def test_study_notes_lecture_relationship(self, session):
        """Test relationship between study notes and lecture."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.UPLOAD
        )
        session.add(lecture)
        session.commit()
        
        notes = StudyNotes(
            lecture_id=lecture.id,
            topics=[],
            summary="Test summary",
            key_points=[]
        )
        session.add(notes)
        session.commit()
        
        # Access lecture through notes
        assert notes.lecture.title == "Test Lecture"
        
        # Access notes through lecture
        assert lecture.study_notes.summary == "Test summary"
    
    def test_study_notes_cascade_delete(self, session):
        """Test that deleting a lecture deletes its study notes."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.UPLOAD
        )
        session.add(lecture)
        session.commit()
        
        notes = StudyNotes(
            lecture_id=lecture.id,
            topics=[],
            summary="Test summary",
            key_points=[]
        )
        session.add(notes)
        session.commit()
        
        notes_id = notes.id
        
        # Delete lecture
        session.delete(lecture)
        session.commit()
        
        # Study notes should be deleted
        deleted_notes = session.query(StudyNotes).filter_by(id=notes_id).first()
        assert deleted_notes is None
    
    def test_study_notes_unique_per_lecture(self, session):
        """Test that each lecture can have only one study notes entry."""
        user = User(email="student@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Test Lecture",
            lecture_type=LectureType.UPLOAD
        )
        session.add(lecture)
        session.commit()
        
        notes1 = StudyNotes(
            lecture_id=lecture.id,
            topics=[],
            summary="First notes",
            key_points=[]
        )
        session.add(notes1)
        session.commit()
        
        notes2 = StudyNotes(
            lecture_id=lecture.id,
            topics=[],
            summary="Second notes",
            key_points=[]
        )
        session.add(notes2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            session.commit()


@pytest.mark.unit
class TestDatabaseCRUD:
    """Test CRUD operations on database models."""
    
    def test_create_and_read_user(self, session):
        """Test creating and reading a user."""
        user = User(email="crud@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        # Read user
        retrieved_user = session.query(User).filter_by(email="crud@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "crud@example.com"
    
    def test_update_user(self, session):
        """Test updating a user."""
        user = User(email="update@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        # Update user
        user.last_login = datetime.utcnow()
        session.commit()
        
        # Verify update
        retrieved_user = session.query(User).filter_by(email="update@example.com").first()
        assert retrieved_user.last_login is not None
    
    def test_delete_user(self, session):
        """Test deleting a user."""
        user = User(email="delete@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        user_id = user.id
        
        # Delete user
        session.delete(user)
        session.commit()
        
        # Verify deletion
        deleted_user = session.query(User).filter_by(id=user_id).first()
        assert deleted_user is None
    
    def test_query_lectures_by_user(self, session):
        """Test querying lectures for a specific user."""
        user = User(email="query@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        # Create multiple lectures
        for i in range(3):
            lecture = Lecture(
                user_id=user.id,
                title=f"Lecture {i}",
                lecture_type=LectureType.UPLOAD
            )
            session.add(lecture)
        session.commit()
        
        # Query lectures
        lectures = session.query(Lecture).filter_by(user_id=user.id).all()
        assert len(lectures) == 3
    
    def test_update_lecture_status(self, session):
        """Test updating lecture processing status."""
        user = User(email="status@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        
        lecture = Lecture(
            user_id=user.id,
            title="Status Test",
            lecture_type=LectureType.LIVE
        )
        session.add(lecture)
        session.commit()
        
        assert lecture.processing_status == ProcessingStatus.PENDING
        
        # Update to processing
        lecture.processing_status = ProcessingStatus.PROCESSING
        session.commit()
        
        # Update to completed
        lecture.processing_status = ProcessingStatus.COMPLETED
        lecture.transcript = "Completed transcript"
        session.commit()
        
        # Verify
        retrieved = session.query(Lecture).filter_by(id=lecture.id).first()
        assert retrieved.processing_status == ProcessingStatus.COMPLETED
        assert retrieved.transcript == "Completed transcript"
