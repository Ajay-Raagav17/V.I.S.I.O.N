"""Authentication endpoints for user registration, login, and token management."""

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from database.connection import get_db
from services.auth_service import AuthService

app = FastAPI()
security = HTTPBearer()
auth_service = AuthService()


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    email: str
    created_at: str
    last_login: Optional[str]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
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
    """
    Register a new user account.
    
    Args:
        request: Registration request with email and password
        db: Database session
        
    Returns:
        Authentication response with access token and user info
        
    Raises:
        HTTPException: If email is already registered or validation fails
    """
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
    """
    Authenticate user and generate access token.
    
    Args:
        request: Login request with email and password
        db: Database session
        
    Returns:
        Authentication response with access token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
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


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        User information
    """
    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None
    )


@app.post("/api/auth/logout", response_model=MessageResponse)
async def logout(current_user = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token. This endpoint validates the token and confirms logout.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        Success message
    """
    return MessageResponse(message="Successfully logged out")


@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(current_user = Depends(get_current_user)):
    """
    Refresh access token for authenticated user.
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        New authentication response with refreshed token
    """
    access_token = auth_service.create_access_token(str(current_user.id), current_user.email)
    
    return AuthResponse(
        access_token=access_token,
        user_id=str(current_user.id),
        email=current_user.email
    )
