"""Chiffrement au repos de la base : AES-256-GCM avec clé dérivée par scrypt.

La clé n'est jamais stockée : elle est recalculée à partir du mot de passe
maître (jamais persisté) et d'un sel aléatoire conservé en clair dans
l'en-tête du fichier chiffré.
"""

import hashlib
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"SPDN"
VERSION = 1
SALT_LEN = 16
NONCE_LEN = 12
KEY_LEN = 32

# Paramètres scrypt : compromis raisonnable (~0,2-0,5s sur un PC de bureau).
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1

_HEADER_LEN = len(MAGIC) + 1 + SALT_LEN + NONCE_LEN


class DecryptionError(Exception):
    """Mot de passe incorrect ou fichier corrompu."""


def derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_LEN,
    )


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(passphrase, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return MAGIC + struct.pack("B", VERSION) + salt + nonce + ciphertext


def decrypt(blob: bytes, passphrase: str) -> bytes:
    if len(blob) < _HEADER_LEN:
        raise DecryptionError("fichier corrompu")
    if blob[: len(MAGIC)] != MAGIC:
        raise DecryptionError("fichier non reconnu")
    offset = len(MAGIC)
    offset += 1  # version, non utilisée pour l'instant
    salt = blob[offset : offset + SALT_LEN]
    offset += SALT_LEN
    nonce = blob[offset : offset + NONCE_LEN]
    offset += NONCE_LEN
    ciphertext = blob[offset:]

    key = derive_key(passphrase, salt)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except Exception as exc:  # tag GCM invalide, etc.
        raise DecryptionError("mot de passe incorrect") from exc
