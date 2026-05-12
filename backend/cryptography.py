"""Secure crypto helpers used across the backend.

Provides:
- AES-CBC encryption/decryption with PKCS7 padding
- RSA keypair generation, serialization, OAEP encrypt/decrypt
- Scrypt-based password hashing and verification
- Random generators for keys/iv/salt/token/uuid

All functions return bytes unless otherwise documented.
"""

from __future__ import annotations

import base64
import os
import secrets
import uuid
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, padding as sym_padding, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.exceptions import InvalidKey

# Scrypt parameters — tune these for your deployment
SCRYPT_PARAMS = dict(length=32, n=2 ** 14, r=8, p=1)


def generate_random_bytes(length: int = 32) -> bytes:
    return os.urandom(length)


def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_random_uuid() -> str:
    return str(uuid.uuid4())


# ---------------- AES-CBC (with PKCS7) ----------------


def encrypt_aes_cbc(plaintext: bytes, key: bytes) -> Tuple[bytes, bytes]:
    """Encrypt data using AES-CBC.

    Returns a tuple `(iv, ciphertext)` where both are raw bytes. `key` must be
    16/24/32 bytes long.
    """
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 16, 24 or 32 bytes long")
    iv = os.urandom(16)
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return iv, ciphertext


def decrypt_aes_cbc(iv: bytes, ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt AES-CBC data and remove PKCS7 padding."""
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 16, 24 or 32 bytes long")
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded) + unpadder.finalize()
    return plaintext


# ---------------- RSA helpers ----------------


def generate_rsa_key_pair(key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key, private_key.public_key()


def serialize_private_key(private_key: rsa.RSAPrivateKey, password: Optional[bytes] = None) -> bytes:
    encryption = serialization.BestAvailableEncryption(password) if password else serialization.NoEncryption()
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


def encrypt_with_rsa(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.encrypt(
        data,
        asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def decrypt_with_rsa(ciphertext: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    return private_key.decrypt(
        ciphertext,
        asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


# ---------------- Password hashing (Scrypt) ----------------


def hash_password(password: str) -> Tuple[str, str]:
    """Hash a password using Scrypt.

    Returns `(hash_b64, salt_b64)` both as base64-encoded strings.
    """
    salt = os.urandom(16)
    kdf = Scrypt(salt=salt, **SCRYPT_PARAMS)
    key = kdf.derive(password.encode())
    return base64.b64encode(key).decode(), base64.b64encode(salt).decode()


def verify_password(password: str, hash_b64: str, salt_b64: str) -> bool:
    salt = base64.b64decode(salt_b64)
    expected = base64.b64decode(hash_b64)
    kdf = Scrypt(salt=salt, **SCRYPT_PARAMS)
    try:
        kdf.verify(password.encode(), expected)
        return True
    except InvalidKey:
        return False


__all__ = [
    "generate_random_bytes",
    "generate_random_token",
    "generate_random_uuid",
    "encrypt_aes_cbc",
    "decrypt_aes_cbc",
    "generate_rsa_key_pair",
    "serialize_private_key",
    "load_private_key",
    "serialize_public_key",
    "load_public_key",
    "encrypt_with_rsa",
    "decrypt_with_rsa",
    "hash_password",
    "verify_password",
]
