# Database Setup

This directory contains database connection utilities and migration management for the VISION application.

## Database Models

The application uses the following models:

- **User**: Student accounts with authentication
- **Lecture**: Lecture sessions (live or uploaded)
- **StudyNotes**: AI-generated structured notes for lectures

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database URL

Set the `DATABASE_URL` environment variable in your `.env` file:

```
DATABASE_URL=postgresql://user:password@localhost:5432/vision_db
```

### 3. Run Migrations

Initialize the database schema using Alembic:

```bash
# Run migrations
python -m alembic upgrade head
```

### 4. Create New Migrations

When you modify models, create a new migration:

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/
# Then apply it
python -m alembic upgrade head
```

## Database Connection

The `database/connection.py` module provides:

- `engine`: SQLAlchemy engine with connection pooling
- `SessionLocal`: Session factory for database operations
- `Base`: Declarative base for models
- `get_db()`: Dependency function for FastAPI endpoints
- `init_db()`: Initialize database tables
- `close_db()`: Close all connections

### Usage Example

```python
from database import get_db
from models import User

# In FastAPI endpoint
@app.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

## Running Tests

Unit tests for database models use SQLite in-memory database:

```bash
python -m pytest tests/test_database_models.py -v
```

## Connection Pooling

The database engine is configured with:
- Pool size: 5 connections
- Max overflow: 10 additional connections
- Pool pre-ping: Verify connections before use
- Pool recycle: Recycle connections after 1 hour

This configuration is optimized for serverless deployment on Vercel.
