import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param
from app.config import Config
from app.database import db

# Security
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle it
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: str, email: str) -> str:
    """Create JWT token"""
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }

    return jwt.encode(payload, Config.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from request (header or cookie)"""
    # Check Authorization header first
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, param = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer":
            return param

    # Check cookie
    token = request.cookies.get("access_token")
    if token:
        return token

    return None


async def get_current_user(request: Request) -> dict:
    """Get current user from token (works with both header and cookie)"""
    token = await get_token_from_request(request)

    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    # Get user from database
    user = db.execute(
        "SELECT id, name, email, plan_type, tokens_used, token_limit FROM users WHERE id = %s",
        (payload['sub'],),
        fetch_one=True
    )

    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    return user

# For Swagger UI compatibility


async def get_current_user_swagger(token: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from token (for Swagger UI)"""
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    user = db.execute(
        "SELECT id, name, email, plan_type, tokens_used, token_limit FROM users WHERE id = %s",
        (payload['sub'],),
        fetch_one=True
    )

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def generate_api_key() -> str:
    """Generate unique API key for bots"""
    return secrets.token_urlsafe(32)


def check_token_limit(user_id: str, tokens_to_add: int) -> bool:
    """Check if user has enough tokens"""
    user = db.execute(
        "SELECT tokens_used, token_limit FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )

    if not user:
        return False

    return (user['tokens_used'] + tokens_to_add) <= user['token_limit']


def update_token_usage(user_id: str, tokens_used: int):
    """Update user's token usage"""
    db.execute(
        "UPDATE users SET tokens_used = tokens_used + %s WHERE id = %s",
        (tokens_used, user_id)
    )
