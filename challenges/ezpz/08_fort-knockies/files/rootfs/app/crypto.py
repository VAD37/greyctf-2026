import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def derive_key(password: str, salt: bytes, iterations: int) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    ).derive(password.encode("utf-8"))


def encrypt_blob(data: bytes, password: str, filename: str = "upload.bin") -> bytes:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    iterations = 250000
    key = derive_key(password, salt, iterations)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    return json.dumps(
        {
            "version": "FKENC1",
            "filename": filename,
            "kdf": "PBKDF2-HMAC-SHA256",
            "iterations": iterations,
            "cipher": "AES-256-GCM",
            "salt_b64": b64e(salt),
            "nonce_b64": b64e(nonce),
            "ciphertext_b64": b64e(ciphertext),
        },
        indent=2,
    ).encode("utf-8")
