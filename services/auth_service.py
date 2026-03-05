"""Authentication service for user registration, login, and token management."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from models.user import User

# In-memory store for password reset tokens (in production, use Redis or database)
password_reset_tokens: Dict[str, dict] = {}


class AuthService:
    """
    Service for handling authentication operations.
    
    Provides methods for:
    - Password hashing and verification
    - JWT token generation and validation
    - User registration and login
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret = os.getenv("JWT_SECRET", "default_secret_key_change_in_production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "user_id": user_id,
            "email": email,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    def register_user(self, db: Session, email: str, password: str) -> User:
        """
        Register a new user with email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If email is already registered
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        user = User(email=email, password_hash=password_hash)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            db: Database session
            user_id: User's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        import uuid as uuid_module
        try:
            # Convert string to UUID if necessary
            if isinstance(user_id, str):
                user_id = uuid_module.UUID(user_id)
        except ValueError:
            return None
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user by their email.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def create_password_reset_token(self, email: str) -> str:
        """
        Create a password reset token for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Reset token string
        """
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        
        password_reset_tokens[token] = {
            'email': email,
            'expiry': expiry
        }
        
        return token
    
    def verify_reset_token(self, token: str) -> Optional[str]:
        """
        Verify a password reset token and return the associated email.
        
        Args:
            token: Reset token string
            
        Returns:
            Email address if token is valid, None otherwise
        """
        if token not in password_reset_tokens:
            return None
        
        token_data = password_reset_tokens[token]
        
        if datetime.utcnow() > token_data['expiry']:
            # Token expired, remove it
            del password_reset_tokens[token]
            return None
        
        return token_data['email']
    
    def reset_password(self, db: Session, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a valid reset token.
        
        Args:
            db: Database session
            token: Reset token string
            new_password: New password to set
            
        Returns:
            True if password was reset, False otherwise
        """
        email = self.verify_reset_token(token)
        if not email:
            return False
        
        user = self.get_user_by_email(db, email)
        if not user:
            return False
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        db.commit()
        
        # Remove used token
        del password_reset_tokens[token]
        
        return True
