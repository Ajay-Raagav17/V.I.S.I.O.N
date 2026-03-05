"""Audio upload endpoints for file-based transcription and processing."""

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
import os
import asyncio

from database.connection import get_db
from services.transcription_service import TranscriptionService
from models.lecture import Lecture, LectureType, ProcessingStatus
from models.user import User
from api.auth import get_current_user

app = FastAPI()

# In-memory storage for upload status (in production, use Redis or database)
upload_status_store = {}


class UploadResponse(BaseModel):
    """Response model for audio upload."""
    upload_id: str
    message: str
    lecture_id: str


class StatusResponse(BaseModel):
    """Response model for upload status."""
    upload_id: str
    lecture_id: str
    status: str
    progress: int
    message: Optional[str] = None
    transcript: Optional[str] = None
    error: Optional[str] = None


def process_audio_file(
    upload_id: str,
    lecture_id: str,
    audio_content: bytes,
    file_format: str,
    db_session: Session
):
    """
    Background task to process uploaded audio file.
    
    Args:
        upload_id: Unique upload identifier
        lecture_id: Lecture database ID
        audio_content: Audio file content as bytes
        file_format: Audio file format
        db_session: Database session
        
    Requirements: 2.3, 2.4
    """
    try:
        # Update status to processing
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'processing',
            'progress': 10,
            'message': 'Starting transcription...'
        }
        
        # Initialize transcription service
        transcription_service = TranscriptionService()
        
        # Update progress
        upload_status_store[upload_id]['progress'] = 30
        upload_status_store[upload_id]['message'] = 'Transcribing audio...'
        
        # Transcribe the audio file
        transcript = transcription_service.transcribe_file(audio_content, file_format)
        
        # Update progress
        upload_status_store[upload_id]['progress'] = 80
        upload_status_store[upload_id]['message'] = 'Saving transcript...'
        
        # Update lecture record with transcript
        lecture = db_session.query(Lecture).filter(
            Lecture.id == lecture_id
        ).first()
        
        if lecture:
            lecture.transcript = transcript
            lecture.processing_status = 'completed'
            db_session.commit()
        
        # Update status to completed
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'completed',
            'progress': 100,
            'message': 'Transcription completed successfully',
            'transcript': transcript
        }
        
    except Exception as e:
        # Update status to failed
        upload_status_store[upload_id] = {
            'lecture_id': lecture_id,
            'status': 'failed',
            'progress': 0,
            'message': 'Transcription failed',
            'error': str(e)
        }
        
        # Update lecture status in database
        try:
            lecture = db_session.query(Lecture).filter(
                Lecture.id == lecture_id
            ).first()
            if lecture:
                lecture.processing_status = 'failed'
                db_session.commit()
        except Exception:
            pass
    
    finally:
        db_session.close()


@app.post("/api/upload/audio", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form("Uploaded Lecture"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload audio file for transcription and processing.
    
    Accepts audio files in supported formats (MP3, WAV, M4A, OGG),
    validates the file, and starts background processing.
    
    Args:
        background_tasks: FastAPI background tasks
        file: Uploaded audio file
        title: Optional title for the lecture
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Upload ID and lecture ID for status tracking
        
    Raises:
        HTTPException: If file validation fails
        
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    # Initialize transcription service for validation
    transcription_service = TranscriptionService()
    
    # Extract file format from filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    file_format = file.filename.split('.')[-1].lower()
    
    # Validate audio format
    if not transcription_service.validate_audio_format(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {file_format}. "
                   f"Supported formats: {', '.join(transcription_service.SUPPORTED_FORMATS)}"
        )
    
    # Read file content
    audio_content = await file.read()
    
    # Validate file size
    file_size = len(audio_content)
    if not transcription_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size {file_size} bytes exceeds maximum allowed size of "
                   f"{transcription_service.MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique upload ID and lecture ID
    upload_id = str(uuid.uuid4())
    lecture_id = str(uuid.uuid4())
    
    # Create lecture record in pending state
    lecture = Lecture(
        id=lecture_id,
        user_id=str(current_user.id),
        title=title,
        lecture_type='upload',
        audio_file_path=f"uploads/{current_user.id}/{upload_id}.{file_format}",
        processing_status='pending',
        created_at=datetime.utcnow()
    )
    
    db.add(lecture)
    db.commit()
    
    # Initialize status
    upload_status_store[upload_id] = {
        'lecture_id': lecture_id,
        'status': 'pending',
        'progress': 0,
        'message': 'Upload received, queued for processing'
    }
    
    # Create a new database session for the background task
    from database.connection import SessionLocal
    background_db = SessionLocal()
    
    # Start background processing
    background_tasks.add_task(
        process_audio_file,
        upload_id,
        lecture_id,
        audio_content,
        file_format,
        background_db
    )
    
    return UploadResponse(
        upload_id=upload_id,
        message="File uploaded successfully, processing started",
        lecture_id=lecture_id
    )


@app.get("/api/upload/status/{upload_id}", response_model=StatusResponse)
async def get_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check processing status of an uploaded audio file.
    
    Returns the current status, progress percentage, and any available
    results or error messages.
    
    Args:
        upload_id: Unique upload identifier
        current_user: Authenticated user
        
    Returns:
        Current status information including progress and results
        
    Raises:
        HTTPException: If upload ID not found
        
    Requirements: 2.4, 2.5
    """
    # Check if upload exists
    if upload_id not in upload_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    status_info = upload_status_store[upload_id]
    
    return StatusResponse(
        upload_id=upload_id,
        lecture_id=status_info['lecture_id'],
        status=status_info['status'],
        progress=status_info['progress'],
        message=status_info.get('message'),
        transcript=status_info.get('transcript'),
        error=status_info.get('error')
    )
