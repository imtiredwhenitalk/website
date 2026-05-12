"""Authentication helpers: user creation, verification, and JWT tokens.

This module uses the `User` model from `backend.integration` and the
`SessionLocal` from `backend.db`. Password hashing/verification re-uses the
Scrypt helpers in `backend.cryptography`.

Functions provided:
- `create_user(db, username, email, password)`
- `authenticate_user(db, username_or_email, password)`
- `create_access_token(data, expires_minutes=60)`
- `decode_access_token(token)`

Note: requires `PyJWT` (install `pyjwt`) or will raise an informative error.
"""

from __future__ import annotations

import os
import datetime
from typing import Optional, Tuple

import jwt
from sqlalchemy.orm import Session

from backend.db import SessionLocal
from backend.integration import User
from backend.cryptography import hash_password, verify_password

# secret key for tokens — prefer env var
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "change-me-in-prod"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """Create and persist a new user. Returns the created `User` instance."""
    pw_hash, salt = hash_password(password)
    user = User(username=username, email=email, password_hash=pw_hash, salt=salt)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """Verify credentials and return user if valid."""
    user = get_user_by_username(db, username_or_email) or get_user_by_email(db, username_or_email)
    if not user:
        return None
    if verify_password(password, user.password_hash, user.salt):
        return user
    return None


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Tuple[bool, Optional[dict]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, None
    except jwt.InvalidTokenError:
        return False, None


# Convenience context manager for ad-hoc usage
def create_user_and_get_token(username: str, email: str, password: str) -> Tuple[User, str]:
    db = SessionLocal()
    try:
        user = create_user(db, username, email, password)
        token = create_access_token({"sub": user.username})
        return user, token
    finally:
        db.close()


__all__ = [
    "create_user",
    "authenticate_user",
    "create_access_token",
    "decode_access_token",
    "create_user_and_get_token",
]
