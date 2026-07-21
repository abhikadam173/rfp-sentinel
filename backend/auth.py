"""
Minimal v1 login: a single hardcoded buyer credential (env-configured),
JWT issued on success. No password hashing, no `users` table -- a
documented shortcut for tonight's demo, not production-grade auth. Real
multi-user credential auth (Postgres `users`, hashed passwords, roles) is
v1.1 scope per the plan; this exists only so the buyer dashboard has a
real login round-trip to show, not a client-side fake.
"""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "dev-only-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

BUYER_EMAIL = os.getenv("BUYER_EMAIL", "buyer@rfpsentinel.local")
BUYER_PASSWORD = os.getenv("BUYER_PASSWORD", "changeme")

_bearer = HTTPBearer()


def authenticate_buyer(email: str, password: str) -> bool:
    return email == BUYER_EMAIL and password == BUYER_PASSWORD


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_buyer(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
    return payload["sub"]
