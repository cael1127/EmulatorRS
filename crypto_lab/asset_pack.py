"""Educational encrypted asset container using AES-GCM."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # pragma: no cover - environment dependent
    AESGCM = None


MAGIC = b"PLG1"
VERSION = 1
SALT_LEN = 16
NONCE_LEN = 12
KEY_LEN = 32


class IntegrityError(Exception):
    """Raised when ciphertext authentication fails."""


class ReplayError(Exception):
    """Raised when nonce reuse is detected by a tracker."""


def _require_crypto() -> None:
    if AESGCM is None:
        raise RuntimeError(
            "cryptography package is required for AES-GCM demo: pip install cryptography"
        )


def hkdf_sha256(key_material: bytes, salt: bytes, info: bytes, length: int = KEY_LEN) -> bytes:
    """Tiny HKDF implementation for educational purposes."""
    if length <= 0:
        raise ValueError("length must be > 0")
    prk = hmac.new(salt, key_material, hashlib.sha256).digest()
    okm = bytearray()
    prev = b""
    counter = 1
    while len(okm) < length:
        prev = hmac.new(prk, prev + info + bytes([counter]), hashlib.sha256).digest()
        okm.extend(prev)
        counter += 1
    return bytes(okm[:length])


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a stable AES key from a passphrase."""
    if len(salt) != SALT_LEN:
        raise ValueError(f"salt must be {SALT_LEN} bytes")
    stretched = hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return hkdf_sha256(stretched, salt=salt, info=b"asset-pack-aesgcm", length=KEY_LEN)


@dataclass
class NonceTracker:
    """Tracks seen nonces to detect replayed containers."""

    seen: set[bytes]

    def __init__(self) -> None:
        self.seen = set()

    def check_and_store(self, nonce: bytes) -> None:
        if nonce in self.seen:
            raise ReplayError("nonce has already been used")
        self.seen.add(nonce)


def _serialize_assets(assets: dict[str, bytes]) -> bytes:
    payload = {
        "version": VERSION,
        "assets": {name: base64.b64encode(data).decode("ascii") for name, data in assets.items()},
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _deserialize_assets(payload: bytes) -> dict[str, bytes]:
    obj = json.loads(payload.decode("utf-8"))
    if obj.get("version") != VERSION:
        raise ValueError("unsupported asset payload version")
    raw = obj.get("assets", {})
    return {name: base64.b64decode(data.encode("ascii")) for name, data in raw.items()}


def create_asset_pack(
    assets: dict[str, bytes],
    passphrase: str,
    *,
    salt: bytes | None = None,
    nonce: bytes | None = None,
) -> bytes:
    """Encrypt asset map into a compact authenticated container."""
    _require_crypto()
    salt = os.urandom(SALT_LEN) if salt is None else salt
    nonce = os.urandom(NONCE_LEN) if nonce is None else nonce
    if len(salt) != SALT_LEN:
        raise ValueError(f"salt must be {SALT_LEN} bytes")
    if len(nonce) != NONCE_LEN:
        raise ValueError(f"nonce must be {NONCE_LEN} bytes")

    key = derive_key(passphrase, salt)
    aes = AESGCM(key)
    plaintext = _serialize_assets(assets)
    ciphertext = aes.encrypt(nonce, plaintext, associated_data=MAGIC)
    return MAGIC + bytes([VERSION]) + salt + nonce + len(ciphertext).to_bytes(4, "big") + ciphertext


def load_asset_pack(
    blob: bytes,
    passphrase: str,
    *,
    nonce_tracker: NonceTracker | None = None,
) -> dict[str, bytes]:
    """Decrypt and authenticate an asset pack."""
    _require_crypto()
    minimum = len(MAGIC) + 1 + SALT_LEN + NONCE_LEN + 4
    if len(blob) < minimum:
        raise ValueError("blob too small")
    if blob[:4] != MAGIC:
        raise ValueError("invalid asset pack header")
    version = blob[4]
    if version != VERSION:
        raise ValueError("unsupported asset pack version")
    salt_start = 5
    salt_end = salt_start + SALT_LEN
    nonce_end = salt_end + NONCE_LEN
    salt = blob[salt_start:salt_end]
    nonce = blob[salt_end:nonce_end]
    ct_len = int.from_bytes(blob[nonce_end : nonce_end + 4], "big")
    ciphertext = blob[nonce_end + 4 : nonce_end + 4 + ct_len]
    if len(ciphertext) != ct_len:
        raise ValueError("malformed ciphertext length")

    if nonce_tracker is not None:
        nonce_tracker.check_and_store(nonce)

    key = derive_key(passphrase, salt)
    aes = AESGCM(key)
    try:
        plaintext = aes.decrypt(nonce, ciphertext, associated_data=MAGIC)
    except Exception as exc:  # pragma: no cover - exact exception type library-specific
        raise IntegrityError("authentication failed for asset pack") from exc
    return _deserialize_assets(plaintext)
