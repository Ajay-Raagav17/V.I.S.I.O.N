"""Unit tests for audio upload endpoints."""

import pytest
import uuid
import io
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Enum
from sqlalchemy.orm import sessionmaker, declarative_base
from unittest.mock import Mock, patch, MagicMock

from api.upload import app, upload_status_store
from models.lecture import LectureType, ProcessingStatus

# Create test-specific models for SQLite compatibility
TestBase = declarative_base()


class TestUser(TestBase):
    """Test User model compatible with SQLite."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)


class TestLecture(TestBase):
    """Test Lecture model compatible with SQLite."""
    __tablename__ = "lectures"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    lecture_type = Column(String(50), nullable=False)
    audio_file_path = Column(String(1000), nullable=True)
    transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    processing_status = Column(String(50), default="pending", nullable=False)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    engine.dispose()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = TestUser(
        id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash="hashed_password",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def mock_auth_token():
    """Mock authentication token."""
    return "mock_jwt_token"


@pytest.fixture
def client(test_db, test_user, mock_auth_token):
    """Create test client with mocked dependencies."""
    from database.connection import get_db
    from api.auth import get_current_user
    
    # Override dependencies
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    def override_get_current_user():
        return test_user
    
    # Patch the Lecture model to use test model
    import api.upload
    original_lecture = api.upload.Lecture
    api.upload.Lecture = TestLecture
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    
    # Clean up
    api.upload.Lecture = original_lecture
    app.dependency_overrides.clear()
    upload_status_store.clear()


class TestUploadAudioEndpoint:
    """Tests for POST /api/upload/audio endpoint."""
    
    def test_upload_valid_mp3_file(self, client, test_user):
        """
        Test file upload with valid MP3 format.
        
        Requirements: 2.1
        """
        # Create a mock MP3 file
        file_content = b"fake mp3 audio content"
        files = {
            'file': ('test_audio.mp3', io.BytesIO(file_content), 'audio/mpeg')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = True
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'Test Lecture'}
            )
        
        assert response.status_code == 202
        data = response.json()
        assert 'upload_id' in data
        assert 'lecture_id' in data
        assert data['message'] == "File uploaded successfully, processing started"
    
    def test_upload_valid_wav_file(self, client, test_user):
        """
        Test file upload with valid WAV format.
        
        Requirements: 2.1
        """
        file_content = b"fake wav audio content"
        files = {
            'file': ('test_audio.wav', io.BytesIO(file_content), 'audio/wav')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = True
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'WAV Test Lecture'}
            )
        
        assert response.status_code == 202
        data = response.json()
        assert 'upload_id' in data
        assert 'lecture_id' in data
    
    def test_upload_valid_m4a_file(self, client, test_user):
        """
        Test file upload with valid M4A format.
        
        Requirements: 2.1
        """
        file_content = b"fake m4a audio content"
        files = {
            'file': ('test_audio.m4a', io.BytesIO(file_content), 'audio/m4a')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = True
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'M4A Test Lecture'}
            )
        
        assert response.status_code == 202
        data = response.json()
        assert 'upload_id' in data
    
    def test_upload_valid_ogg_file(self, client, test_user):
        """
        Test file upload with valid OGG format.
        
        Requirements: 2.1
        """
        file_content = b"fake ogg audio content"
        files = {
            'file': ('test_audio.ogg', io.BytesIO(file_content), 'audio/ogg')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = True
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'OGG Test Lecture'}
            )
        
        assert response.status_code == 202
        data = response.json()
        assert 'upload_id' in data
    
    def test_upload_invalid_format_rejection(self, client, test_user):
        """
        Test file validation rejection for unsupported format.
        
        Requirements: 2.2, 2.5
        """
        file_content = b"fake video content"
        files = {
            'file': ('test_video.mp4', io.BytesIO(file_content), 'video/mp4')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = False
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'Invalid Format Test'}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'Unsupported audio format' in data['detail']
    
    def test_upload_file_too_large_rejection(self, client, test_user):
        """
        Test file validation rejection for file size exceeding limits.
        
        Requirements: 2.2, 2.5
        """
        # Create a large file content
        file_content = b"x" * (101 * 1024 * 1024)  # 101 MB
        files = {
            'file': ('large_audio.mp3', io.BytesIO(file_content), 'audio/mpeg')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = False
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'Large File Test'}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data
        assert 'exceeds maximum allowed size' in data['detail']
    
    def test_upload_missing_filename(self, client, test_user):
        """
        Test file upload with missing filename.
        
        Requirements: 2.2, 2.5
        """
        file_content = b"fake audio content"
        files = {
            'file': ('', io.BytesIO(file_content), 'audio/mpeg')
        }
        
        response = client.post(
            "/api/upload/audio",
            files=files,
            data={'title': 'No Filename Test'}
        )
        
        # FastAPI returns 422 for validation errors or 400 for our custom validation
        assert response.status_code in [400, 422]
        data = response.json()
        assert 'detail' in data
    
    def test_upload_creates_lecture_record(self, client, test_user, test_db):
        """
        Test that upload creates a lecture record in the database.
        
        Requirements: 2.3
        """
        file_content = b"fake mp3 audio content"
        files = {
            'file': ('test_audio.mp3', io.BytesIO(file_content), 'audio/mpeg')
        }
        
        with patch('api.upload.TranscriptionService') as MockTranscriptionService:
            mock_service = MockTranscriptionService.return_value
            mock_service.validate_audio_format.return_value = True
            mock_service.validate_file_size.return_value = True
            mock_service.SUPPORTED_FORMATS = {'mp3', 'wav', 'm4a', 'ogg'}
            mock_service.MAX_FILE_SIZE = 100 * 1024 * 1024
            
            response = client.post(
                "/api/upload/audio",
                files=files,
                data={'title': 'Database Test Lecture'}
            )
        
        assert response.status_code == 202
        data = response.json()
        lecture_id = data['lecture_id']
        
        # Verify lecture was created in database
        lecture = test_db.query(TestLecture).filter(
            TestLecture.id == lecture_id
        ).first()
        
        assert lecture is not None
        assert lecture.title == 'Database Test Lecture'
        assert lecture.lecture_type == 'upload'
        assert lecture.processing_status == 'pending'


class TestUploadStatusEndpoint:
    """Tests for GET /api/upload/status/:id endpoint."""
    
    def test_status_endpoint_returns_pending_status(self, client, test_user):
        """
        Test status endpoint returns pending status for new upload.
        
        Requirements: 2.4
        """
        # Create a mock upload status
        upload_id = str(uuid.uuid4())
        lecture_id = str(uuid.uuid4())
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Upload received, queued for processing'
        }
        
        response = client.get(f"/api/upload/status/{upload_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['upload_id'] == upload_id
        assert data['lecture_id'] == lecture_id
        assert data['status'] == 'pending'
        assert data['progress'] == 0
        assert data['message'] == 'Upload received, queued for processing'
    
    def test_status_endpoint_returns_processing_status(self, client, test_user):
        """
        Test status endpoint returns processing status with progress.
        
        Requirements: 2.4
        """
        upload_id = str(uuid.uuid4())
        lecture_id = str(uuid.uuid4())
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'processing',
            'progress': 50,
            'message': 'Transcribing audio...'
        }
        
        response = client.get(f"/api/upload/status/{upload_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'processing'
        assert data['progress'] == 50
        assert data['message'] == 'Transcribing audio...'
    
    def test_status_endpoint_returns_completed_status(self, client, test_user):
        """
        Test status endpoint returns completed status with transcript.
        
        Requirements: 2.4, 2.5
        """
        upload_id = str(uuid.uuid4())
        lecture_id = str(uuid.uuid4())
        transcript = "This is the transcribed text from the audio file."
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Transcription completed successfully',
            'transcript': transcript
        }
        
        response = client.get(f"/api/upload/status/{upload_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'completed'
        assert data['progress'] == 100
        assert data['transcript'] == transcript
    
    def test_status_endpoint_returns_failed_status(self, client, test_user):
        """
        Test status endpoint returns failed status with error message.
        
        Requirements: 2.5
        """
        upload_id = str(uuid.uuid4())
        lecture_id = str(uuid.uuid4())
        error_message = "Google Speech-to-Text API error: Connection timeout"
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'failed',
            'progress': 0,
            'message': 'Transcription failed',
            'error': error_message
        }
        
        response = client.get(f"/api/upload/status/{upload_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'failed'
        assert data['error'] == error_message
    
    def test_status_endpoint_not_found(self, client, test_user):
        """
        Test status endpoint returns 404 for non-existent upload ID.
        
        Requirements: 2.5
        """
        non_existent_id = str(uuid.uuid4())
        
        response = client.get(f"/api/upload/status/{non_existent_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert 'detail' in data
        assert 'Upload not found' in data['detail']
    
    def test_status_endpoint_tracks_progress_updates(self, client, test_user):
        """
        Test status endpoint reflects progress updates during processing.
        
        Requirements: 2.4
        """
        upload_id = str(uuid.uuid4())
        lecture_id = str(uuid.uuid4())
        
        # Initial status
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'pending',
            'progress': 0,
            'message': 'Upload received'
        }
        
        response = client.get(f"/api/upload/status/{upload_id}")
        assert response.json()['progress'] == 0
        
        # Update to processing
        upload_status_store[upload_id]['status'] = 'processing'
        upload_status_store[upload_id]['progress'] = 30
        upload_status_store[upload_id]['message'] = 'Transcribing...'
        
        response = client.get(f"/api/upload/status/{upload_id}")
        assert response.json()['progress'] == 30
        assert response.json()['status'] == 'processing'
        
        # Update to near completion
        upload_status_store[upload_id]['progress'] = 80
        upload_status_store[upload_id]['message'] = 'Saving transcript...'
        
        response = client.get(f"/api/upload/status/{upload_id}")
        assert response.json()['progress'] == 80
