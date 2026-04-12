"""
OS HubLine — Sécurité (JWT, hashing, auth)
Compatible Python 3.9+
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import os
import base64
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

settings = get_settings()

# ── Password Hashing (SHA-256 + salt, compatible Python 3.9) ─
# Note: en production, migrer vers bcrypt avec Python 3.11+

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt + key).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        decoded = base64.b64decode(hashed.encode("utf-8"))
        salt = decoded[:32]
        stored_key = decoded[32:]
        new_key = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(stored_key, new_key)
    except Exception:
        return False


# ── JWT Tokens ──────────────────────────────────────────
security_scheme = HTTPBearer()


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Type de token invalide",
        )
    return payload


def require_roles(*roles: str):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "viewer")
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {', '.join(roles)}",
            )
        return current_user
    return role_checker
