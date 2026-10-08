from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user
from app.database import db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("dashboard/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("dashboard/register.html", {"request": request})


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, current_user: dict = Depends(get_current_user)):
    """Dashboard home page"""
    # Get user's bots
    bots = db.execute(
        """SELECT b.*, 
           (SELECT COUNT(*) FROM documents WHERE bot_id = b.id) as document_count,
           (SELECT COUNT(*) FROM conversations WHERE bot_id = b.id) as conversation_count
           FROM bots b 
           WHERE b.user_id = %s 
           ORDER BY b.created_at DESC
           LIMIT 5""",
        (current_user['id'],),
        fetch_all=True
    )

    # Get overall stats
    stats = db.execute(
        """SELECT 
            (SELECT COUNT(*) FROM bots WHERE user_id = %s) as total_bots,
            (SELECT COUNT(*) FROM documents d JOIN bots b ON d.bot_id = b.id WHERE b.user_id = %s) as total_documents,
            (SELECT COUNT(*) FROM conversations c JOIN bots b ON c.bot_id = b.id WHERE b.user_id = %s) as total_conversations,
            (SELECT COUNT(*) FROM messages m JOIN conversations c ON m.conversation_id = c.id JOIN bots b ON c.bot_id = b.id WHERE b.user_id = %s) as total_messages,
            (SELECT SUM(tokens_used) FROM messages m JOIN conversations c ON m.conversation_id = c.id JOIN bots b ON c.bot_id = b.id WHERE b.user_id = %s) as total_tokens
        """,
        (current_user['id'], current_user['id'], current_user['id'],
         current_user['id'], current_user['id']),
        fetch_one=True
    )

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "current_user": current_user,
            "bots": bots or [],
            "stats": stats or {}
        }
    )


@router.get("/api/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard stats"""
    stats = db.execute(
        """SELECT 
            (SELECT COUNT(*) FROM bots WHERE user_id = %s) as total_bots,
            (SELECT COUNT(*) FROM documents d JOIN bots b ON d.bot_id = b.id WHERE b.user_id = %s) as total_documents,
            (SELECT COUNT(*) FROM conversations c JOIN bots b ON c.bot_id = b.id WHERE b.user_id = %s) as total_conversations,
            (SELECT COUNT(*) FROM messages m JOIN conversations c ON m.conversation_id = c.id JOIN bots b ON c.bot_id = b.id WHERE b.user_id = %s) as total_messages,
            (SELECT SUM(tokens_used) FROM messages WHERE role = 'assistant') as total_tokens
        """,
        (current_user['id'], current_user['id'],
         current_user['id'], current_user['id']),
        fetch_one=True
    )

    return stats
