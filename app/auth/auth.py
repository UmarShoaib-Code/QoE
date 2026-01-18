"""
Authentication utilities for user login/signup
"""
import bcrypt
from sqlalchemy.orm import Session
from app.database.models import User, get_session
from typing import Optional


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_user(email: str, username: str, password: str, full_name: Optional[str] = None) -> Optional[User]:
    """Create a new user"""
    db = get_session()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return None
        
        # Create new user
        hashed = hash_password(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed,
            full_name=full_name,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password"""
    db = get_session()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    finally:
        db.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID"""
    db = get_session()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


