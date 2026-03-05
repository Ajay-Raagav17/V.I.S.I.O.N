"""Unit tests for live captioning endpoints."""

import pytest
import os
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Set up environment variables BEFORE importing modules that need them
os.environ.setdefault('GOOGLE_CLOUD_API_KEY', 'test_api_key')
os.environ.setdefault('GEMINI_API_KEY', 'test_gemini_key')

# Import actual models - this ensures they're registered with Base
from models.user import User
from models.lecture import Lecture, LectureType, ProcessingStatus
from models.study_notes import StudyNotes  # Import to register with Base
from database.connection import Base


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test with UUID support for SQLite."""
    from sqlalchemy.dialects.sqlite import base as sqlite_base
    
    # Store original if it exists
    original_visit_UUID = None
    if hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID'):
        original_visit_UUID = sqlite_base.SQLiteTypeCompiler.visit_UUID
    
    # Override UUID type for SQLite BEFORE creating engine
    def visit_UUID(self, type_, **kw):
        return "CHAR(36)"
    
    sqlite_base.SQLiteTypeCompiler.visit_UUID = visit_UUID
    
    # Use a shared cache for in-memory SQLite to allow multiple connections
    # This is necessary because TestClient runs in a separate thread
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared&uri=true",
        connect_args={"check_same_thread": False}
    )
    
    # Set up foreign keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create tables
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    
    # Cleanup
    Base.metadata.drop_all(engine)
    engine.dispose()
    
    # Restore original if it existed
    if original_visit_UUID:
        sqlite_base.SQLiteTypeCompiler.visit_UUID = original_visit_UUID
    elif hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID'):
        delattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID')


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def mock_get_current_user(test_user):
    """Mock the get_current_user dependency."""
    def _mock_user():
        # Return the actual test user
        return test_user
    return _mock_user


@pytest.fixture
def client(test_db, mock_get_current_user):
    """Create a test client with mocked dependencies."""
    from api.live import app, active_sessions
    from api.auth import get_current_user
    from database.connection import get_db
    
    # Clear active sessions before each test
    active_sessions.clear()
    
    # Override dependencies - return the session directly, not a generator
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()
    active_sessions.clear()


class TestStartLiveSession:
    """Tests for POST /api/live/start endpoint."""
    
    def test_start_session_creates_lecture_record(self, client, test_db, test_user):
        """
        Test that starting a session creates a lecture record in the database.
        Requirements: 1.1
        """
        response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "message" in data
        assert data["message"] == "Live session started successfully"
        
        # Verify lecture was created in database
        lecture = test_db.query(Lecture).filter(
            Lecture.user_id == test_user.id
        ).first()
        
        assert lecture is not None
        assert lecture.title == "Test Lecture"
        assert lecture.lecture_type == LectureType.LIVE
        assert lecture.processing_status == ProcessingStatus.PENDING
    
    def test_start_session_returns_unique_session_id(self, client):
        """
        Test that each session gets a unique session ID.
        Requirements: 1.1
        """
        response1 = client.post(
            "/api/live/start",
            json={"title": "Lecture 1"}
        )
        response2 = client.post(
            "/api/live/start",
            json={"title": "Lecture 2"}
        )
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        session_id1 = response1.json()["session_id"]
        session_id2 = response2.json()["session_id"]
        
        assert session_id1 != session_id2
    
    def test_start_session_requires_title(self, client):
        """
        Test that starting a session requires a title.
        Requirements: 1.1
        """
        response = client.post(
            "/api/live/start",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestStopLiveSession:
    """Tests for POST /api/live/stop endpoint."""
    
    def test_stop_session_saves_transcript(self, client, test_db, test_user):
        """
        Test that stopping a session saves the transcript to the database.
        Requirements: 1.1
        """
        # Start a session first
        start_response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        session_id = start_response.json()["session_id"]
        
        # Manually add some transcript segments to the session
        from api.live import active_sessions
        if session_id in active_sessions:
            active_sessions[session_id]['transcript_segments'] = [
                {'text': 'Hello world', 'segment_id': 0},
                {'text': 'This is a test', 'segment_id': 1}
            ]
        
        # Stop the session
        stop_response = client.post(
            "/api/live/stop",
            json={"session_id": session_id}
        )
        
        assert stop_response.status_code == 200
        data = stop_response.json()
        
        # Verify response
        assert "lecture_id" in data
        assert "transcript" in data
        assert "duration_seconds" in data
        assert data["message"] == "Session stopped and data saved successfully"
        
        # Verify transcript was saved
        lecture = test_db.query(Lecture).filter(
            Lecture.id == uuid.UUID(data["lecture_id"])
        ).first()
        
        assert lecture is not None
        assert lecture.transcript is not None
        assert "Hello world" in lecture.transcript
        assert "This is a test" in lecture.transcript
        assert lecture.processing_status == ProcessingStatus.COMPLETED
    
    def test_stop_session_calculates_duration(self, client):
        """
        Test that stopping a session calculates the duration correctly.
        Requirements: 1.1
        """
        # Start a session
        start_response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        session_id = start_response.json()["session_id"]
        
        # Stop the session
        stop_response = client.post(
            "/api/live/stop",
            json={"session_id": session_id}
        )
        
        assert stop_response.status_code == 200
        data = stop_response.json()
        
        # Duration should be >= 0
        assert data["duration_seconds"] >= 0
    
    def test_stop_nonexistent_session_returns_404(self, client):
        """
        Test that stopping a non-existent session returns 404.
        Requirements: 1.1
        """
        response = client.post(
            "/api/live/stop",
            json={"session_id": str(uuid.uuid4())}
        )
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_stop_session_removes_from_active_sessions(self, client):
        """
        Test that stopping a session removes it from active sessions.
        Requirements: 1.1
        """
        from api.live import active_sessions
        
        # Start a session
        start_response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        session_id = start_response.json()["session_id"]
        
        # Verify session is active
        assert session_id in active_sessions
        
        # Stop the session
        client.post(
            "/api/live/stop",
            json={"session_id": session_id}
        )
        
        # Verify session is removed
        assert session_id not in active_sessions


class TestWebSocketStream:
    """Tests for WebSocket /api/live/stream endpoint."""
    
    def test_websocket_accepts_connection(self, client):
        """
        Test that WebSocket endpoint accepts connections.
        Requirements: 1.1
        """
        # Start a session first
        start_response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        session_id = start_response.json()["session_id"]
        
        # Connect to WebSocket
        with client.websocket_connect("/api/live/stream") as websocket:
            # Send session_id
            websocket.send_json({"session_id": session_id})
            
            # Receive connection confirmation
            data = websocket.receive_json()
            assert data["status"] == "connected"
    
    def test_websocket_rejects_invalid_session(self, client):
        """
        Test that WebSocket rejects invalid session IDs.
        Requirements: 1.1
        """
        with client.websocket_connect("/api/live/stream") as websocket:
            # Send invalid session_id
            websocket.send_json({"session_id": "invalid-session-id"})
            
            # Should receive error
            data = websocket.receive_json()
            assert "error" in data
    
    def test_websocket_processes_audio_segments(self, client):
        """
        Test that WebSocket processes audio data and returns transcriptions.
        Requirements: 1.1, 1.4, 4.1, 4.2
        """
        import base64
        
        # Start a session
        start_response = client.post(
            "/api/live/start",
            json={"title": "Test Lecture"}
        )
        session_id = start_response.json()["session_id"]
        
        # Connect to WebSocket
        with client.websocket_connect("/api/live/stream") as websocket:
            # Send session_id
            websocket.send_json({"session_id": session_id})
            websocket.receive_json()  # Receive connection confirmation
            
            # Send audio data (10 seconds worth of audio at 16kHz, mono, 16-bit)
            # 16000 samples/sec * 1 channel * 2 bytes * 10 seconds = 320000 bytes
            audio_data = b'\x00' * 320000
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            
            websocket.send_json({"audio": encoded_audio})
            
            # Receive transcription
            data = websocket.receive_json()
            
            # Verify response structure
            assert "segment_id" in data
            assert "text" in data
            assert "timestamp" in data
            assert "confidence" in data
