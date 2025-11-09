"""
DEVELOPMENT-ONLY AUTHENTICATION MODULE

⚠️ WARNING: This authentication system is for DEVELOPMENT and TESTING purposes only.
It is NOT suitable for production use due to security limitations:

- Sessions stored in memory (lost on restart)
- No encryption of session data
- Simple plaintext password comparison  
- No rate limiting or brute force protection
- Basic session management without proper security

For production, implement:
- Database-backed session storage
- Encrypted/hashed passwords  
- JWT tokens or OAuth2
- Proper session security
- Rate limiting and monitoring
"""

from fastapi import HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Auth configuration
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin123")
SESSION_DURATION_HOURS = int(os.getenv("SESSION_DURATION_HOURS", "24"))

# Simple session storage (in production, use Redis or database)
active_sessions = {}

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def create_session(username: str) -> str:
    """Create a new session and return the session token"""
    session_token = generate_session_token()
    active_sessions[session_token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    }
    return session_token

def validate_session(session_token: str) -> bool:
    """Validate if a session token is active and not expired"""
    if not session_token or session_token not in active_sessions:
        return False
    
    session = active_sessions[session_token]
    if datetime.now() > session["expires_at"]:
        # Remove expired session
        del active_sessions[session_token]
        return False
    
    return True

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials"""
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

async def get_current_user(request: Request) -> Optional[str]:
    """Get current authenticated user from session cookie"""
    if not AUTH_ENABLED:
        return "anonymous"  # No auth required
    
    session_token = request.cookies.get("session_token")
    if not session_token or not validate_session(session_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    session = active_sessions[session_token]
    return session["username"]

def remove_session(session_token: str):
    """Remove a session (logout)"""
    if session_token in active_sessions:
        del active_sessions[session_token]