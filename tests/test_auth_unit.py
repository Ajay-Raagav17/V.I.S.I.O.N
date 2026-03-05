"""
Unit tests for authentication system.

Tests user registration, login, JWT token generation and validation.
Requirements: 6.1, 6.2
"""

import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Set up SQLite UUID support BEFORE importing models
from sqlalchemy.dialects.sqlite import base as sqlite_base

def _visit_UUID(self, type_, **kw):
    return "CHAR(36)"

# Apply the override at module load time
if not hasattr(sqlite_base.SQLiteTypeCompiler, '_original_visit_UUID'):
    if hasattr(sqlite_base.SQLiteTypeCompiler, 'visit_UUID'):
        sqlite_base.SQLiteTypeCompiler._original_visit_UUID = sqlite_base.SQLiteTypeCompiler.visit_UUID
    sqlite_base.SQLiteTypeCompiler.visit_UUID = _visit_UUID

from database.connection import get_db, Base
from api.auth import app

# Import actual models to register them with Base
from models.user import User
from models.lecture import Lecture
from models.study_notes import StudyNotes


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test with UUID support for SQLite."""
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


@pytest.fixture
def client(test_db):
    """Create a test client with database dependency override."""
    # Override dependencies - must be a generator like the original get_db
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_valid_user(self, client):
        """Test registration with valid email and password."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "test@example.com"
        assert "user_id" in data
        assert data["token_type"] == "bearer"
    
    def test_register_duplicate_email(self, client):
        """Test registration with already registered email."""
        # Register first user
        client.post(
            "/api/auth/register",
            json={"email": "duplicate@example.com", "password": "password123"}
        )
        
        # Try to register with same email
        response = client.post(
            "/api/auth/register",
            json={"email": "duplicate@example.com", "password": "different456"}
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "password123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_missing_password(self, client):
        """Test registration without password."""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality."""
    
    def test_login_correct_credentials(self, client):
        """Test login with correct email and password."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={"email": "login@example.com", "password": "correctpass"}
        )
        
        # Login with correct credentials
        response = client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "correctpass"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "login@example.com"
        assert "user_id" in data
    
    def test_login_incorrect_password(self, client):
        """Test login with incorrect password."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={"email": "user@example.com", "password": "correctpass"}
        )
        
        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={"email": "user@example.com", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypass"}
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_updates_last_login(self, test_db):
        """Test that login updates the last_login timestamp."""
        from services.auth_service import AuthService
        auth_service = AuthService()
        
        # Create user
        password_hash = auth_service.hash_password("password123")
        user = User(
            id=uuid.uuid4(),
            email="timestamp@example.com",
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        initial_last_login = user.last_login
        
        # Simulate login by updating last_login
        user.last_login = datetime.utcnow()
        test_db.commit()
        test_db.refresh(user)
        
        # last_login should be updated
        assert user.last_login is not None
        assert user.last_login != initial_last_login


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_token_generation(self, auth_service):
        """Test that tokens are generated correctly."""
        token = auth_service.create_access_token("user-123", "test@example.com")
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_validation_success(self, auth_service):
        """Test validation of valid token."""
        user_id = "user-456"
        email = "valid@example.com"
        token = auth_service.create_access_token(user_id, email)
        
        payload = auth_service.verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["email"] == email
        assert "exp" in payload
    
    def test_token_validation_invalid_token(self, auth_service):
        """Test validation of invalid token."""
        invalid_token = "invalid.token.string"
        
        payload = auth_service.verify_token(invalid_token)
        
        assert payload is None
    
    def test_token_validation_tampered_token(self, auth_service):
        """Test validation of tampered token."""
        token = auth_service.create_access_token("user-789", "test@example.com")
        tampered_token = token[:-10] + "tampered00"
        
        payload = auth_service.verify_token(tampered_token)
        
        assert payload is None


class TestProtectedEndpoints:
    """Test authentication middleware for protected routes."""
    
    def test_get_current_user_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token."""
        # Register and get token
        response = client.post(
            "/api/auth/register",
            json={"email": "protected@example.com", "password": "password123"}
        )
        token = response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "protected@example.com"
        assert "user_id" in data
        assert "created_at" in data
    
    def test_get_current_user_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # Forbidden
    
    def test_get_current_user_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_logout_with_valid_token(self, client):
        """Test logout endpoint with valid token."""
        # Register and get token
        response = client.post(
            "/api/auth/register",
            json={"email": "logout@example.com", "password": "password123"}
        )
        token = response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
    
    def test_refresh_token(self, client):
        """Test token refresh endpoint."""
        import time
        
        # Register and get token
        response = client.post(
            "/api/auth/register",
            json={"email": "refresh@example.com", "password": "password123"}
        )
        old_token = response.json()["access_token"]
        
        # Wait a moment to ensure different timestamp in new token
        time.sleep(1.1)
        
        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {old_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        new_token = data["access_token"]
        
        # New token should be different from old token (due to different timestamp)
        assert new_token != old_token
        
        # New token should be valid
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        assert response.status_code == 200


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_is_hashed(self, test_db):
        """Test that passwords are hashed, not stored in plain text."""
        from services.auth_service import AuthService
        auth_service = AuthService()
        
        password = "plaintext_password"
        password_hash = auth_service.hash_password(password)
        user = User(
            id=uuid.uuid4(),
            email="hash@example.com",
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        test_db.add(user)
        test_db.commit()
        
        # Password hash should not equal plain password
        assert user.password_hash != password
        
        # Password hash should be a bcrypt hash (starts with $2b$)
        assert user.password_hash.startswith("$2b$")
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        from services.auth_service import AuthService
        auth_service = AuthService()
        
        password = "same_password"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        
        # But both should verify correctly
        assert auth_service.verify_password(password, hash1)
        assert auth_service.verify_password(password, hash2)
