"""POST /auth/login -- minimal v1 auth, see backend/auth.py for the shortcut this takes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.auth import authenticate_buyer, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    if not authenticate_buyer(body.email, body.password):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(body.email)
    return {"access_token": token, "token_type": "bearer"}
