"""Pytest configuration for tests."""

import pytest
import sys
import uuid
from sqlalchemy import create_engine, Column, String, DateTime, event
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from services.auth_service import AuthService

# Disable problematic plugins
pytest_plugins = []

# Set up SQLite UUID support BEFORE any models are imported
from sqlalchemy.dialects.sqlite import base as sqlite_base

def _visit_UUID(self, type_, **kw):
    return "CHAR(36)"

# Apply the override at module load time
sqlite_base.SQLiteTypeCompiler.visit_UUID = _visit_UUID


def pytest_configure(config):
    """Configure pytest to disable web3 plugin."""
    try:
        config.pluginmanager.set_blocked("web3")
    except Exception:
        pass


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
def auth_service():
    """Create an AuthService instance."""
    return AuthService()
