"""
Property-based tests for authentication system.

**Feature: vision-accessibility, Property 6: Authentication correctness**
**Validates: Requirements 6.2**
"""

import pytest
import uuid
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from services.auth_service import AuthService


# Create a test-specific Base and User model for SQLite compatibility
TestBase = declarative_base()


class TestUser(TestBase):
    """Test User model compatible with SQLite."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)


# Create in-memory SQLite database for testing
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    engine = create_engine("sqlite:///:memory:")
    TestBase.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def auth_service():
    """Create an AuthService instance."""
    return AuthService()


# Strategy for generating valid email addresses
email_strategy = st.emails()

# Strategy for generating passwords (at least 6 characters, ASCII only for bcrypt compatibility)
password_strategy = st.text(
    min_size=6, 
    max_size=30,
    alphabet=st.characters(min_codepoint=33, max_codepoint=126)  # Printable ASCII
)


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    email=email_strategy,
    password=password_strategy,
    wrong_password=password_strategy
)
def test_authentication_correctness(test_db, auth_service, email, password, wrong_password):
    """
    Property 6: Authentication correctness
    
    For any user account with stored credentials, authentication should succeed 
    when provided with matching email and password, and fail when provided with 
    non-matching credentials.
    
    **Feature: vision-accessibility, Property 6: Authentication correctness**
    **Validates: Requirements 6.2**
    """
    # Ensure wrong_password is actually different from password
    if wrong_password == password:
        wrong_password = "WRONG_" + password
    
    # Check if user already exists
    existing_user = test_db.query(TestUser).filter(TestUser.email == email).first()
    if existing_user:
        # Skip if email already exists in this test run
        return
    
    # Create a user with the given email and password
    password_hash = auth_service.hash_password(password)
    user = TestUser(email=email, password_hash=password_hash)
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Property: Authentication with correct credentials should succeed
    authenticated_user = test_db.query(TestUser).filter(TestUser.email == email).first()
    assert authenticated_user is not None, \
        f"User should exist in database for {email}"
    assert auth_service.verify_password(password, authenticated_user.password_hash), \
        "Password verification should succeed with correct password"
    
    # Property: Authentication with wrong password should fail
    assert not auth_service.verify_password(wrong_password, authenticated_user.password_hash), \
        f"Password verification should fail with incorrect password for {email}"
    
    # Property: Authentication with non-existent email should fail
    non_existent_email = "nonexistent_" + email
    failed_auth_no_user = test_db.query(TestUser).filter(TestUser.email == non_existent_email).first()
    assert failed_auth_no_user is None, \
        "Query should return None for non-existent user"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    email=email_strategy,
    password=password_strategy
)
def test_password_hashing_verification_roundtrip(auth_service, email, password):
    """
    Property: Password hashing and verification should be consistent.
    
    For any password, hashing it and then verifying the original password 
    against the hash should succeed, while verifying a different password 
    should fail.
    
    **Feature: vision-accessibility, Property 6: Authentication correctness**
    **Validates: Requirements 6.2**
    """
    # Hash the password
    hashed = auth_service.hash_password(password)
    
    # Property: Verifying the original password should succeed
    assert auth_service.verify_password(password, hashed), \
        "Original password should verify against its hash"
    
    # Property: Verifying a different password should fail
    different_password = "WRONG_" + password
    assert not auth_service.verify_password(different_password, hashed), \
        "Different password should not verify against hash"


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    email=email_strategy,
    password=password_strategy
)
def test_token_generation_verification_roundtrip(auth_service, email, password):
    """
    Property: Token generation and verification should be consistent.
    
    For any user credentials, generating a token and then verifying it 
    should return the original user information.
    
    **Feature: vision-accessibility, Property 6: Authentication correctness**
    **Validates: Requirements 6.2**
    """
    user_id = "test-user-id-123"
    
    # Generate token
    token = auth_service.create_access_token(user_id, email)
    
    # Property: Verifying the token should return the original payload
    payload = auth_service.verify_token(token)
    assert payload is not None, "Token verification should succeed"
    assert payload["user_id"] == user_id, "User ID should match"
    assert payload["email"] == email, "Email should match"
    
    # Property: Verifying an invalid token should fail
    invalid_token = token + "invalid"
    invalid_payload = auth_service.verify_token(invalid_token)
    assert invalid_payload is None, "Invalid token should not verify"
