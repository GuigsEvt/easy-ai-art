from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.auth import authenticate_user, create_session, remove_session, AUTH_ENABLED, get_current_user
from typing import Optional

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    message: str
    authenticated: bool

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """
    Authenticate user and set session cookie
    """
    if not AUTH_ENABLED:
        return LoginResponse(message="Authentication is disabled", authenticated=True)
    
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create session and set cookie
    session_token = create_session(request.username)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=24*60*60  # 24 hours
    )
    
    return LoginResponse(message="Login successful", authenticated=True)

@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout user and clear session cookie
    """
    if not AUTH_ENABLED:
        return {"message": "Authentication is disabled"}
    
    session_token = request.cookies.get("session_token")
    if session_token:
        remove_session(session_token)
    
    response.delete_cookie(key="session_token")
    return {"message": "Logout successful"}

@router.get("/auth-status")
async def auth_status(current_user: str = Depends(get_current_user)):
    """
    Check authentication status
    """
    return {
        "authenticated": True,
        "auth_enabled": AUTH_ENABLED,
        "user": current_user if AUTH_ENABLED else None
    }

@router.get("/auth-config")
async def auth_config():
    """
    Get authentication configuration (public endpoint)
    """
    return {
        "auth_enabled": AUTH_ENABLED
    }