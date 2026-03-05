"""Live captioning endpoints for real-time audio streaming and transcription."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict
from datetime import datetime
import uuid
import asyncio

from database.connection import get_db
from services.audio_processing import AudioProcessingPipeline, TranscriptSegment
from services.transcription_service import TranscriptionService
from models.lecture import Lecture, LectureType, ProcessingStatus
from models.user import User
from api.auth import get_current_user

app = FastAPI()

# Store active sessions in memory (in production, use Redis or similar)
active_sessions: Dict[str, dict] = {}


class StartSessionRequest(BaseModel):
    """Request model for starting a live session."""
    title: str


class StartSessionResponse(BaseModel):
    """Response model for starting a live session."""
    session_id: str
    message: str


class StopSessionRequest(BaseModel):
    """Request model for stopping a live session."""
    session_id: str


class StopSessionResponse(BaseModel):
    """Response model for stopping a live session."""
    lecture_id: str
    message: str
    transcript: str
    duration_seconds: int


@app.post("/api/live/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_live_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize a live captioning session.
    
    Creates a new session ID and prepares the system for real-time audio streaming.
    
    Args:
        request: Session start request with lecture title
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Session ID and confirmation message
        
    Requirements: 1.1
    """
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Create lecture record in pending state
    lecture = Lecture(
        user_id=current_user.id,
        title=request.title,
        lecture_type=LectureType.LIVE,
        processing_status=ProcessingStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    
    # Store session information
    active_sessions[session_id] = {
        'lecture_id': str(lecture.id),
        'user_id': str(current_user.id),
        'title': request.title,
        'start_time': datetime.utcnow(),
        'transcript_segments': [],
        'audio_pipeline': AudioProcessingPipeline(segment_duration=10),
        'transcription_service': TranscriptionService()
    }
    
    return StartSessionResponse(
        session_id=session_id,
        message="Live session started successfully"
    )


@app.post("/api/live/stop", response_model=StopSessionResponse)
async def stop_live_session(
    request: StopSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a live captioning session and save the data.
    
    Finalizes the session, combines all transcript segments, and updates
    the lecture record with the complete transcript.
    
    Args:
        request: Session stop request with session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Lecture ID, complete transcript, and confirmation message
        
    Raises:
        HTTPException: If session not found or unauthorized
        
    Requirements: 1.1, 4.3
    """
    # Check if session exists
    if request.session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session = active_sessions[request.session_id]
    
    # Verify user owns this session
    if session['user_id'] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to stop this session"
        )
    
    # Calculate duration
    duration = (datetime.utcnow() - session['start_time']).total_seconds()
    
    # Combine transcript segments
    transcript_segments = session['transcript_segments']
    full_transcript = ' '.join(segment['text'] for segment in transcript_segments if segment['text'])
    
    # Update lecture record
    lecture = db.query(Lecture).filter(Lecture.id == uuid.UUID(session['lecture_id'])).first()
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecture record not found"
        )
    
    lecture.transcript = full_transcript
    lecture.duration_seconds = int(duration)
    lecture.processing_status = ProcessingStatus.COMPLETED
    
    db.commit()
    db.refresh(lecture)
    
    # Clean up session
    lecture_id = session['lecture_id']
    del active_sessions[request.session_id]
    
    return StopSessionResponse(
        lecture_id=lecture_id,
        message="Session stopped and data saved successfully",
        transcript=full_transcript,
        duration_seconds=int(duration)
    )


@app.websocket("/api/live/stream")
async def websocket_stream(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time audio streaming and transcription.
    
    Accepts audio chunks from the client, processes them through the segmentation
    pipeline, transcribes them, and streams the text back to the client.
    
    Protocol:
    - Client sends: {"session_id": "...", "audio": <base64_encoded_audio>}
    - Server sends: {"segment_id": 0, "text": "...", "timestamp": 0.0}
    
    Args:
        websocket: WebSocket connection
        db: Database session
        
    Requirements: 1.1, 1.4, 4.1, 4.2
    """
    await websocket.accept()
    
    session_id = None
    audio_buffer = bytearray()
    segment_counter = 0
    
    # Audio parameters (16kHz, mono, 16-bit)
    SAMPLE_RATE = 16000
    CHANNELS = 1
    SAMPLE_WIDTH = 2
    SEGMENT_DURATION = 10
    BYTES_PER_SEGMENT = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH * SEGMENT_DURATION
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_json()
            
            # First message should contain session_id
            if session_id is None:
                session_id = data.get('session_id')
                
                if not session_id or session_id not in active_sessions:
                    await websocket.send_json({
                        'error': 'Invalid or missing session_id'
                    })
                    await websocket.close(code=1008)
                    return
                
                await websocket.send_json({
                    'status': 'connected',
                    'message': 'WebSocket connection established'
                })
                continue
            
            # Process audio data
            if 'audio' in data:
                import base64
                
                # Decode base64 audio
                audio_chunk = base64.b64decode(data['audio'])
                audio_buffer.extend(audio_chunk)
                
                # Process complete segments
                while len(audio_buffer) >= BYTES_PER_SEGMENT:
                    segment = bytes(audio_buffer[:BYTES_PER_SEGMENT])
                    audio_buffer = audio_buffer[BYTES_PER_SEGMENT:]
                    
                    # Get session data
                    session = active_sessions[session_id]
                    pipeline = session['audio_pipeline']
                    
                    # Process segment (in production, this would call transcription service)
                    # For now, we'll simulate transcription
                    transcript_segment = {
                        'segment_id': segment_counter,
                        'text': f"Transcribed segment {segment_counter}",
                        'timestamp': segment_counter * SEGMENT_DURATION,
                        'confidence': 0.95
                    }
                    
                    # Store segment
                    session['transcript_segments'].append(transcript_segment)
                    
                    # Send transcription back to client
                    await websocket.send_json({
                        'segment_id': transcript_segment['segment_id'],
                        'text': transcript_segment['text'],
                        'timestamp': transcript_segment['timestamp'],
                        'confidence': transcript_segment['confidence']
                    })
                    
                    segment_counter += 1
    
    except WebSocketDisconnect:
        # Client disconnected
        if session_id and session_id in active_sessions:
            # Process any remaining audio in buffer
            if len(audio_buffer) > 0:
                session = active_sessions[session_id]
                transcript_segment = {
                    'segment_id': segment_counter,
                    'text': f"Transcribed segment {segment_counter} (final)",
                    'timestamp': segment_counter * SEGMENT_DURATION,
                    'confidence': 0.95
                }
                session['transcript_segments'].append(transcript_segment)
    
    except Exception as e:
        # Handle errors
        await websocket.send_json({
            'error': str(e)
        })
        await websocket.close(code=1011)
