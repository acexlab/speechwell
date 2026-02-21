"""
File Logic Summary: Authentication utilities. It hashes/verifies passwords and creates/verifies access tokens used by protected API calls.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from jose import JWTError, jwt  # type: ignore
except Exception:
    JWTError = Exception  # type: ignore
    jwt = None

try:
    import bcrypt  # type: ignore
except Exception:
    bcrypt = None


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    """Create a portable PBKDF2 hash that doesn't require passlib."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2_sha256$100000${salt}${digest.hex()}"


def _verify_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, rounds_str, salt, expected_hex = hashed_password.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        rounds = int(rounds_str)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            rounds,
        ).hex()
        return hmac.compare_digest(digest, expected_hex)
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify PBKDF2 hashes and bcrypt hashes when bcrypt is available."""
    if hashed_password.startswith("pbkdf2_sha256$"):
        return _verify_pbkdf2(plain_password, hashed_password)

    if hashed_password.startswith("$2") and bcrypt is not None:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    return False


def _create_fallback_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url(signature)}"


def _decode_fallback_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(expected_sig, _b64url_decode(sig_b64)):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    exp = payload.get("exp")
    if exp is None:
        raise ValueError("Missing exp")

    exp_dt = datetime.fromisoformat(exp)
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    if exp_dt < datetime.now(timezone.utc):
        raise ValueError("Token expired")
    return payload


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire.isoformat()})
    if jwt is not None:
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return _create_fallback_token(to_encode)


def verify_token(token: str) -> Optional[dict]:
    try:
        if jwt is not None:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        else:
            payload = _decode_fallback_token(token)
        email = payload.get("sub")
        if email is None:
            return None
        return {"email": email}
    except (JWTError, ValueError, KeyError, TypeError):
        return None

