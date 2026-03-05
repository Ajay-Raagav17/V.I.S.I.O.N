"""Lecture history endpoints for managing user lectures."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import secrets

from database.connection import get_db
from models.lecture import Lecture
from models.study_notes import StudyNotes
from services.auth_service import AuthService

router = APIRouter(prefix="/api/lectures", tags=["lectures"])
security = HTTPBearer()
auth_service = AuthService()

# In-memory store for share tokens (in production, use database)
share_tokens: Dict[str, str] = {}  # token -> lecture_id


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> str:
    """Extract user_id from JWT token."""
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return user_id


@router.get("")
async def list_lectures(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> List[Dict[str, Any]]:
    """
    List all lectures for a specific user.
    
    Args:
        user_id: UUID of the user
        db: Database session
        
    Returns:
        List of lecture objects with metadata
        
    Requirements: 6.4
    """
    # Retrieve all lectures for the user, ordered by creation date (newest first)
    lectures = db.query(Lecture).filter(
        Lecture.user_id == user_id
    ).order_by(Lecture.created_at.desc()).all()
    
    # Format response
    result = []
    for lecture in lectures:
        lecture_data = {
            "id": str(lecture.id),
            "title": lecture.title,
            "lecture_type": lecture.lecture_type.value if hasattr(lecture.lecture_type, 'value') else lecture.lecture_type,
            "created_at": lecture.created_at.isoformat(),
            "duration_seconds": lecture.duration_seconds,
            "processing_status": lecture.processing_status.value if hasattr(lecture.processing_status, 'value') else lecture.processing_status
        }
        
        # Check if notes exist
        notes = db.query(StudyNotes).filter(StudyNotes.lecture_id == lecture.id).first()
        lecture_data["has_notes"] = notes is not None
        
        result.append(lecture_data)
    
    return result


@router.get("/{lecture_id}")
async def get_lecture(lecture_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get specific lecture details.
    
    Args:
        lecture_id: UUID of the lecture
        db: Database session
        
    Returns:
        Lecture object with full details
        
    Raises:
        HTTPException: 404 if lecture not found
        
    Requirements: 6.4
    """
    # Retrieve lecture
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Format response
    lecture_data = {
        "id": str(lecture.id),
        "user_id": str(lecture.user_id),
        "title": lecture.title,
        "lecture_type": lecture.lecture_type.value if hasattr(lecture.lecture_type, 'value') else lecture.lecture_type,
        "audio_file_path": lecture.audio_file_path,
        "transcript": lecture.transcript,
        "created_at": lecture.created_at.isoformat(),
        "duration_seconds": lecture.duration_seconds,
        "processing_status": lecture.processing_status.value if hasattr(lecture.processing_status, 'value') else lecture.processing_status
    }
    
    # Check if notes exist and include them
    notes = db.query(StudyNotes).filter(StudyNotes.lecture_id == lecture.id).first()
    if notes:
        topics = json.loads(notes.topics) if isinstance(notes.topics, str) else notes.topics
        key_points = json.loads(notes.key_points) if isinstance(notes.key_points, str) else notes.key_points
        
        lecture_data["notes"] = {
            "id": str(notes.id),
            "topics": topics,
            "summary": notes.summary,
            "key_points": key_points,
            "created_at": notes.created_at.isoformat()
        }
    else:
        lecture_data["notes"] = None
    
    return lecture_data


@router.delete("/{lecture_id}")
async def delete_lecture(
    lecture_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    """
    Delete a specific lecture.
    
    Args:
        lecture_id: UUID of the lecture to delete
        user_id: UUID of the user (from auth token)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if lecture not found
        HTTPException: 403 if user doesn't own the lecture
        
    Requirements: 6.5
    """
    # Retrieve lecture
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    # Check authorization - user must own the lecture
    if str(lecture.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this lecture")
    
    # Delete lecture (cascade will delete associated notes in PostgreSQL)
    db.delete(lecture)
    db.commit()
    
    return {"message": "Lecture deleted successfully", "lecture_id": lecture_id}


@router.post("/{lecture_id}/share")
async def create_share_link(
    lecture_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    """
    Create a shareable link for a lecture.
    
    Args:
        lecture_id: UUID of the lecture to share
        user_id: UUID of the user (from auth token)
        db: Database session
        
    Returns:
        Share token and URL
    """
    # Verify lecture exists and user owns it
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    if str(lecture.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to share this lecture")
    
    # Check if share token already exists for this lecture
    existing_token = None
    for token, lid in share_tokens.items():
        if lid == lecture_id:
            existing_token = token
            break
    
    if existing_token:
        return {"share_token": existing_token, "share_url": f"/shared/{existing_token}"}
    
    # Create new share token
    share_token = secrets.token_urlsafe(16)
    share_tokens[share_token] = lecture_id
    
    return {"share_token": share_token, "share_url": f"/shared/{share_token}"}


@router.delete("/{lecture_id}/share")
async def revoke_share_link(
    lecture_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, str]:
    """
    Revoke a shareable link for a lecture.
    """
    # Verify lecture exists and user owns it
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    if str(lecture.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove share token
    tokens_to_remove = [t for t, lid in share_tokens.items() if lid == lecture_id]
    for token in tokens_to_remove:
        del share_tokens[token]
    
    return {"message": "Share link revoked"}


@router.get("/shared/{share_token}")
async def get_shared_lecture(share_token: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get a lecture via share token (no authentication required).
    """
    if share_token not in share_tokens:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    
    lecture_id = share_tokens[share_token]
    lecture = db.query(Lecture).filter(Lecture.id == lecture_id).first()
    
    if not lecture:
        # Lecture was deleted, remove token
        del share_tokens[share_token]
        raise HTTPException(status_code=404, detail="Lecture no longer exists")
    
    # Return lecture data (limited info for shared view)
    lecture_data = {
        "id": str(lecture.id),
        "title": lecture.title,
        "lecture_type": lecture.lecture_type.value if hasattr(lecture.lecture_type, 'value') else lecture.lecture_type,
        "created_at": lecture.created_at.isoformat(),
        "duration_seconds": lecture.duration_seconds,
        "transcript": lecture.transcript
    }
    
    # Include notes if available
    notes = db.query(StudyNotes).filter(StudyNotes.lecture_id == lecture.id).first()
    if notes:
        topics = json.loads(notes.topics) if isinstance(notes.topics, str) else notes.topics
        key_points = json.loads(notes.key_points) if isinstance(notes.key_points, str) else notes.key_points
        
        lecture_data["notes"] = {
            "topics": topics,
            "summary": notes.summary,
            "key_points": key_points
        }
    
    return lecture_data
