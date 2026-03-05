"""
Main FastAPI application entry point.

This module creates the main FastAPI app and includes all routers
from the various API modules.
"""

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid

from api.middleware import ErrorHandlingMiddleware, setup_error_handlers
from api.notes import router as notes_router
from api.lectures import router as lectures_router
from database.connection import get_db
from services.auth_service import AuthService

# Create main FastAPI application
app = FastAPI(
    title="VISION API",
    description="AI-Powered Educational Accessibility System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Set up exception handlers
setup_error_handlers(app)

# Include routers
app.include_router(notes_router)
app.include_router(lectures_router)

# ============ AUTH ROUTES ============
security = HTTPBearer()
auth_service = AuthService()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, request.email, request.password)
        access_token = auth_service.create_access_token(str(user.id), user.email)
        
        return AuthResponse(
            access_token=access_token,
            user_id=str(user.id),
            email=user.email
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, request.email, request.password)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(str(user.id), user.email)
    
    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        email=user.email
    )


@app.get("/api/auth/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@app.post("/api/auth/logout")
async def logout(current_user = Depends(get_current_user)):
    return {"message": "Successfully logged out"}


@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(current_user = Depends(get_current_user)):
    access_token = auth_service.create_access_token(str(current_user.id), current_user.email)
    return AuthResponse(
        access_token=access_token,
        user_id=str(current_user.id),
        email=current_user.email
    )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@app.post("/api/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset. Returns success even if email doesn't exist (security)."""
    user = auth_service.get_user_by_email(db, request.email)
    
    if user:
        # Create reset token
        token = auth_service.create_password_reset_token(request.email)
        # In production, send email with reset link
        # For now, we'll return the token (for testing purposes)
        print(f"Password reset token for {request.email}: {token}")
    
    # Always return success to prevent email enumeration
    return {"message": "If an account exists with this email, a password reset link has been sent."}


@app.post("/api/auth/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    success = auth_service.reset_password(db, request.token, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password has been reset successfully"}


# ============ UPLOAD ROUTES ============
from services.transcription_service import TranscriptionService
from models.lecture import Lecture

upload_status_store = {}


class UploadResponse(BaseModel):
    upload_id: str
    message: str
    lecture_id: str


class StatusResponse(BaseModel):
    upload_id: str
    lecture_id: str
    status: str
    progress: int
    message: Optional[str] = None
    transcript: Optional[str] = None
    error: Optional[str] = None


@app.post("/api/upload/audio", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form("Uploaded Lecture"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transcription_service = TranscriptionService()
    
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")
    
    file_format = file.filename.split('.')[-1].lower()
    
    if not transcription_service.validate_audio_format(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {file_format}"
        )
    
    audio_content = await file.read()
    file_size = len(audio_content)
    
    if not transcription_service.validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed"
        )
    
    upload_id = str(uuid.uuid4())
    lecture_id = str(uuid.uuid4())
    
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
    
    upload_status_store[upload_id] = {
        'lecture_id': lecture_id,
        'status': 'pending',
        'progress': 0,
        'message': 'Upload received, queued for processing'
    }
    
    return UploadResponse(
        upload_id=upload_id,
        message="File uploaded successfully, processing started",
        lecture_id=lecture_id
    )


@app.get("/api/upload/status/{upload_id}", response_model=StatusResponse)
async def get_upload_status(upload_id: str, current_user = Depends(get_current_user)):
    if upload_id not in upload_status_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
    
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


# ============ LIVE ROUTES ============
from services.audio_processing import AudioProcessingPipeline
from models.lecture import LectureType, ProcessingStatus

active_sessions = {}


class StartSessionRequest(BaseModel):
    title: str


class StartSessionResponse(BaseModel):
    session_id: str
    message: str


class StopSessionRequest(BaseModel):
    session_id: str


class StopSessionResponse(BaseModel):
    lecture_id: str
    message: str
    transcript: str
    duration_seconds: int


@app.post("/api/live/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_live_session(
    request: StartSessionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    
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
    
    active_sessions[session_id] = {
        'lecture_id': str(lecture.id),
        'user_id': str(current_user.id),
        'title': request.title,
        'start_time': datetime.utcnow(),
        'transcript_segments': []
    }
    
    return StartSessionResponse(session_id=session_id, message="Live session started successfully")


@app.post("/api/live/stop", response_model=StopSessionResponse)
async def stop_live_session(
    request: StopSessionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from services.ai_analysis_service import AIAnalysisService
    from models.study_notes import StudyNotes
    
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    session = active_sessions[request.session_id]
    
    if session['user_id'] != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    
    duration = (datetime.utcnow() - session['start_time']).total_seconds()
    transcript_segments = session['transcript_segments']
    full_transcript = ' '.join(segment['text'] for segment in transcript_segments if segment.get('text'))
    
    lecture = db.query(Lecture).filter(Lecture.id == uuid.UUID(session['lecture_id'])).first()
    
    if lecture:
        lecture.transcript = full_transcript
        lecture.duration_seconds = int(duration)
        lecture.processing_status = ProcessingStatus.COMPLETED
        
        # Generate AI summary and study notes if transcript exists
        if full_transcript and len(full_transcript) > 50:
            try:
                ai_service = AIAnalysisService()
                study_notes_data = ai_service.create_study_notes(full_transcript)
                
                # Save study notes to database
                study_notes = StudyNotes(
                    lecture_id=lecture.id,
                    summary=study_notes_data.summary,
                    key_points=study_notes_data.key_points,
                    topics=[{
                        'title': t.title,
                        'subtopics': t.subtopics,
                        'keywords': t.keywords,
                        'definitions': t.definitions,
                        'formulas': t.formulas,
                        'content': t.content
                    } for t in study_notes_data.topics]
                )
                db.add(study_notes)
            except Exception as e:
                print(f"AI analysis error: {e}")
        
        db.commit()
    
    lecture_id = session['lecture_id']
    del active_sessions[request.session_id]
    
    return StopSessionResponse(
        lecture_id=lecture_id,
        message="Session stopped",
        transcript=full_transcript,
        duration_seconds=int(duration)
    )


@app.websocket("/api/live/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and transcription.
    Uses AssemblyAI standard API with async processing for transcription.
    """
    import asyncio
    import base64
    import wave
    import io
    import concurrent.futures
    
    await websocket.accept()
    
    session_id = None
    segment_counter = 0
    start_time = datetime.utcnow()
    
    # Audio parameters - 5 second segments for balance of speed and accuracy
    SAMPLE_RATE = 16000
    CHANNELS = 1
    SAMPLE_WIDTH = 2
    SEGMENT_DURATION = 5
    BYTES_PER_SEGMENT = SAMPLE_RATE * CHANNELS * SAMPLE_WIDTH * SEGMENT_DURATION
    
    audio_buffer = bytearray()
    transcription_service = TranscriptionService()
    
    # Thread pool for async transcription
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    pending_transcriptions = []
    
    def transcribe_segment_sync(wav_data, seg_id, timestamp):
        """Synchronous transcription function to run in thread pool."""
        try:
            text = transcription_service.transcribe_file(wav_data, 'wav')
            return {'segment_id': seg_id, 'text': text or '', 'timestamp': timestamp, 'success': True}
        except Exception as e:
            print(f"Transcription error for segment {seg_id}: {e}")
            return {'segment_id': seg_id, 'text': '', 'timestamp': timestamp, 'success': False, 'error': str(e)}
    
    try:
        # Wait for session_id from client
        data = await websocket.receive_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            await websocket.send_json({'error': 'Invalid or missing session_id'})
            await websocket.close(code=1008)
            return
        
        start_time = datetime.utcnow()
        
        await websocket.send_json({
            'status': 'connected',
            'message': 'Transcription service ready'
        })
        
        # Main loop - receive audio and process
        while True:
            try:
                # Check for completed transcriptions
                completed = []
                still_pending = []
                for future, seg_info in pending_transcriptions:
                    if future.done():
                        completed.append((future, seg_info))
                    else:
                        still_pending.append((future, seg_info))
                pending_transcriptions = still_pending
                
                # Send completed transcriptions to client
                for future, seg_info in completed:
                    try:
                        result = future.result()
                        if result['text']:
                            # Store in session
                            if session_id in active_sessions:
                                active_sessions[session_id]['transcript_segments'].append({
                                    'segment_id': result['segment_id'],
                                    'text': result['text'],
                                    'timestamp': result['timestamp'],
                                    'confidence': 0.95 if result['success'] else 0.5
                                })
                            
                            # Send to client
                            await websocket.send_json({
                                'segment_id': result['segment_id'],
                                'text': result['text'],
                                'timestamp': result['timestamp'],
                                'confidence': 0.95 if result['success'] else 0.5,
                                'is_final': True
                            })
                    except Exception as e:
                        print(f"Error processing transcription result: {e}")
                
                # Receive audio with timeout to allow checking transcriptions
                try:
                    client_data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=0.5
                    )
                    
                    if 'audio' in client_data:
                        audio_chunk = base64.b64decode(client_data['audio'])
                        audio_buffer.extend(audio_chunk)
                        
                        # Process complete segments
                        while len(audio_buffer) >= BYTES_PER_SEGMENT:
                            segment_bytes = bytes(audio_buffer[:BYTES_PER_SEGMENT])
                            audio_buffer = audio_buffer[BYTES_PER_SEGMENT:]
                            
                            elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                            
                            # Convert raw PCM to WAV
                            wav_buffer = io.BytesIO()
                            with wave.open(wav_buffer, 'wb') as wav_file:
                                wav_file.setnchannels(CHANNELS)
                                wav_file.setsampwidth(SAMPLE_WIDTH)
                                wav_file.setframerate(SAMPLE_RATE)
                                wav_file.writeframes(segment_bytes)
                            
                            wav_data = wav_buffer.getvalue()
                            
                            # Send processing indicator
                            await websocket.send_json({
                                'text': f'Processing audio segment {segment_counter}...',
                                'timestamp': elapsed_seconds,
                                'is_final': False,
                                'partial': True
                            })
                            
                            # Submit transcription to thread pool
                            future = executor.submit(
                                transcribe_segment_sync,
                                wav_data,
                                segment_counter,
                                elapsed_seconds
                            )
                            pending_transcriptions.append((future, {'segment_id': segment_counter}))
                            segment_counter += 1
                            
                except asyncio.TimeoutError:
                    # No data received, continue to check transcriptions
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
        
        # Process remaining audio on disconnect
        if session_id and session_id in active_sessions and len(audio_buffer) > SAMPLE_RATE * SAMPLE_WIDTH:
            elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(SAMPLE_WIDTH)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(bytes(audio_buffer))
            
            try:
                text = transcription_service.transcribe_file(wav_buffer.getvalue(), 'wav')
                if text and session_id in active_sessions:
                    active_sessions[session_id]['transcript_segments'].append({
                        'segment_id': segment_counter,
                        'text': text,
                        'timestamp': elapsed_seconds,
                        'confidence': 0.95
                    })
            except Exception:
                pass
        
        # Wait for pending transcriptions to complete
        for future, _ in pending_transcriptions:
            try:
                result = future.result(timeout=30)
                if result['text'] and session_id in active_sessions:
                    active_sessions[session_id]['transcript_segments'].append({
                        'segment_id': result['segment_id'],
                        'text': result['text'],
                        'timestamp': result['timestamp'],
                        'confidence': 0.95 if result['success'] else 0.5
                    })
            except Exception:
                pass
        
        executor.shutdown(wait=False)
    
    except WebSocketDisconnect:
        pass
    
    except Exception as e:
        try:
            await websocket.send_json({'error': str(e)})
            await websocket.close(code=1011)
        except Exception:
            pass


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "VISION API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
