import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ENCRYPTION_VERSION = 0x01
NONCE_SIZE = 12


def generate_encryption_key() -> str:
    key = AESGCM.generate_key(bit_length=256)
    return base64.urlsafe_b64encode(key).decode("ascii")


def encrypt(plaintext: bytes, key_b64: str) -> bytes:
    key = base64.urlsafe_b64decode(key_b64)
    nonce = os.urandom(NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return bytes([ENCRYPTION_VERSION]) + nonce + ciphertext


def decrypt(data: bytes, key_b64: str) -> bytes:
    if not data or data[0] != ENCRYPTION_VERSION:
        raise ValueError("Data is not encrypted or has unsupported version")
    nonce = data[1 : 1 + NONCE_SIZE]
    ciphertext = data[1 + NONCE_SIZE :]
    key = base64.urlsafe_b64decode(key_b64)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def is_encrypted(data: bytes) -> bool:
    return bool(data) and data[0] == ENCRYPTION_VERSION
