from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
from app.models import UserLogin, UserRegister, TokenResponse, UserResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.database import db

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# HTML Pages


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("dashboard/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("dashboard/register.html", {"request": request})


@router.get("/logout")
async def logout():
    """Logout and redirect to login"""
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response

# API Endpoints


@router.post("/api/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user exists
    existing = db.execute(
        "SELECT id FROM users WHERE email = %s",
        (user_data.email,),
        fetch_one=True
    )

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(user_data.password)

    # Set plan limits (free by default)
    plan_type = 'free'
    token_limit = 10000  # 10k tokens for free plan

    db.execute(
        """INSERT INTO users (id, name, email, password_hash, plan_type, token_limit)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, user_data.name, user_data.email,
         password_hash, plan_type, token_limit)
    )

    # Get created user
    user = db.execute(
        "SELECT id, name, email, plan_type, tokens_used, token_limit, created_at FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )

    # Create token
    access_token = create_access_token(user['id'], user['email'])

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(**user)
    )


@router.post("/api/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user"""
    # Find user
    user = db.execute(
        "SELECT id, name, email, password_hash, plan_type, tokens_used, token_limit, created_at FROM users WHERE email = %s",
        (login_data.email,),
        fetch_one=True
    )

    if not user or not verify_password(login_data.password, user['password_hash']):
        raise HTTPException(
            status_code=401, detail="Invalid email or password")

    # Remove password_hash from response
    del user['password_hash']

    # Create token
    access_token = create_access_token(user['id'], user['email'])

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(**user)
    )


@router.get("/api/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(**current_user)
