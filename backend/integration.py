"""Database models and small crypto helpers used by the backend.

This module provides:
- SQLAlchemy models: `User` and `Item`
- a safe default `DATABASE_URL` (overridable via env)
- session helper `get_db()` as a generator
- RSA key helpers + encrypt/decrypt convenience wrappers
- Scrypt-based password hashing and verification helpers
"""

from __future__ import annotations

import base64
import os
from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

# Configuration: prefer environment variable, fallback to a local sqlite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./website.db")

SCRYPT_PARAMS = dict(length=32, n=2 ** 14, r=8, p=1)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    # store password hash (base64) and salt (base64)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - small helper
        return f"<User(username={self.username!s}, email={self.email!s})>"


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=True)
    price = Column(Integer, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="items")

    def __repr__(self) -> str:  # pragma: no cover - small helper
        return f"<Item(title={self.title!s}, price={self.price})>"


# SQLAlchemy engine and sessionmaker
_create_engine_kwargs = {}
if DATABASE_URL.startswith("sqlite:"):
    _create_engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_create_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator:
    """Yield a SQLAlchemy session; meant to be used as a dependency.

    Example:
        with get_db() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------- RSA helpers --------------------


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate an RSA private/public keypair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key, private_key.public_key()


def serialize_private_key(private_key: rsa.RSAPrivateKey, password: Optional[bytes] = None) -> bytes:
    """Return PEM bytes for a private key. If `password` provided, the PEM is encrypted."""
    encryption = (
        serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
    )
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )


def load_private_key(pem_data: bytes, password: Optional[bytes] = None) -> rsa.RSAPrivateKey:
    return serialization.load_pem_private_key(pem_data, password=password)


def serialize_public_key(public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)


def load_public_key(pem_data: bytes) -> rsa.RSAPublicKey:
    return serialization.load_pem_public_key(pem_data)


def encrypt_with_rsa(plaintext: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """Encrypt bytes with RSA-OAEP-SHA256."""
    return public_key.encrypt(
        plaintext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def decrypt_with_rsa(ciphertext: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


# -------------------- Password hashing (Scrypt) --------------------


def hash_password(password: str) -> Tuple[str, str]:
    """Hash a password with Scrypt.

    Returns a tuple `(password_hash_b64, salt_b64)` suitable for storage.
    """
    salt = os.urandom(16)
    kdf = Scrypt(salt=salt, **SCRYPT_PARAMS)
    key = kdf.derive(password.encode())
    return base64.b64encode(key).decode(), base64.b64encode(salt).decode()


def verify_password(password: str, password_hash_b64: str, salt_b64: str) -> bool:
    """Verify a password against stored base64-encoded hash and salt."""
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(password_hash_b64)
    kdf = Scrypt(salt=salt, **SCRYPT_PARAMS)
    try:
        kdf.verify(password.encode(), expected)
        return True
    except InvalidKey:
        return False


__all__ = [
    "Base",
    "User",
    "Item",
    "engine",
    "get_db",
    "generate_rsa_keypair",
    "serialize_private_key",
    "load_private_key",
    "serialize_public_key",
    "load_public_key",
    "encrypt_with_rsa",
    "decrypt_with_rsa",
    "hash_password",
    "verify_password",
]
