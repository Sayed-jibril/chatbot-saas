from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import uuid
from app.models import BotCreate, BotResponse, BotUpdate
from app.auth import get_current_user, generate_api_key
from app.database import db
from app.config import Config

router = APIRouter(prefix="/dashboard", tags=["bots"])
templates = Jinja2Templates(directory="app/templates")

# HTML Pages


@router.get("/bots", response_class=HTMLResponse)
async def bots_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Show all bots"""
    bots = db.execute(
        """SELECT b.*, 
           (SELECT COUNT(*) FROM documents WHERE bot_id = b.id) as document_count,
           (SELECT COUNT(*) FROM conversations WHERE bot_id = b.id) as conversation_count
           FROM bots b 
           WHERE b.user_id = %s 
           ORDER BY b.created_at DESC""",
        (current_user['id'],),
        fetch_all=True
    )

    return templates.TemplateResponse(
        "dashboard/bots.html",
        {
            "request": request,
            "bots": bots or [],
            "current_user": current_user
        }
    )


@router.get("/bots/new", response_class=HTMLResponse)
async def new_bot_page(request: Request, current_user: dict = Depends(get_current_user)):
    """Show create bot form"""
    return templates.TemplateResponse(
        "dashboard/bot_create.html",
        {
            "request": request,
            "current_user": current_user
        }
    )


@router.get("/bots/{bot_id}", response_class=HTMLResponse)
async def bot_detail_page(request: Request, bot_id: str, current_user: dict = Depends(get_current_user)):
    """Show bot details"""
    bot = db.execute(
        "SELECT * FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    doc_count = db.execute(
        "SELECT COUNT(*) as count FROM documents WHERE bot_id = %s",
        (bot_id,),
        fetch_one=True
    )

    return templates.TemplateResponse(
        "dashboard/bot_detail.html",
        {
            "request": request,
            "bot": bot,
            "document_count": doc_count['count'] if doc_count else 0,
            "current_user": current_user,
            "app_url": Config.APP_URL
        }
    )

# API Endpoints


@router.post("/api/bots", response_model=BotResponse)
async def create_bot(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    welcome_message: Optional[str] = Form("Hello! How can I help you?"),
    primary_color: Optional[str] = Form("#3B82F6"),
    current_user: dict = Depends(get_current_user)
):
    """Create a new bot"""
    # Check bot limit
    bot_count = db.execute(
        "SELECT COUNT(*) as count FROM bots WHERE user_id = %s",
        (current_user['id'],),
        fetch_one=True
    )

    max_bots = Config.PLAN_LIMITS[current_user['plan_type']]['bots']

    if bot_count['count'] >= max_bots:
        raise HTTPException(
            status_code=400,
            detail=f"Your {current_user['plan_type']} plan allows maximum {max_bots} bots"
        )

    bot_id = str(uuid.uuid4())
    api_key = generate_api_key()

    db.execute(
        """INSERT INTO bots (id, user_id, name, description, api_key, welcome_message, primary_color)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (bot_id, current_user['id'], name, description,
         api_key, welcome_message, primary_color)
    )

    bot = db.execute(
        "SELECT * FROM bots WHERE id = %s",
        (bot_id,),
        fetch_one=True
    )

    return BotResponse(**bot)


@router.get("/api/bots", response_model=list[BotResponse])
async def get_bots(current_user: dict = Depends(get_current_user)):
    """Get all bots"""
    bots = db.execute(
        "SELECT * FROM bots WHERE user_id = %s ORDER BY created_at DESC",
        (current_user['id'],),
        fetch_all=True
    )

    return [BotResponse(**bot) for bot in bots]


@router.get("/api/bots/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific bot"""
    bot = db.execute(
        "SELECT * FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return BotResponse(**bot)


@router.put("/api/bots/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: str, bot_update: BotUpdate, current_user: dict = Depends(get_current_user)):
    """Update a bot"""
    bot = db.execute(
        "SELECT id FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    update_fields = []
    values = []

    if bot_update.name is not None:
        update_fields.append("name = %s")
        values.append(bot_update.name)

    if bot_update.description is not None:
        update_fields.append("description = %s")
        values.append(bot_update.description)

    if bot_update.welcome_message is not None:
        update_fields.append("welcome_message = %s")
        values.append(bot_update.welcome_message)

    if bot_update.primary_color is not None:
        update_fields.append("primary_color = %s")
        values.append(bot_update.primary_color)

    if update_fields:
        query = f"UPDATE bots SET {', '.join(update_fields)} WHERE id = %s"
        values.append(bot_id)
        db.execute(query, tuple(values))

    updated_bot = db.execute(
        "SELECT * FROM bots WHERE id = %s",
        (bot_id,),
        fetch_one=True
    )

    return BotResponse(**updated_bot)


@router.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a bot"""
    bot = db.execute(
        "SELECT id FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    db.execute("DELETE FROM bots WHERE id = %s", (bot_id,))

    return {"message": "Bot deleted successfully"}


@router.post("/api/bots/{bot_id}/reset-key")
async def reset_api_key(bot_id: str, current_user: dict = Depends(get_current_user)):
    """Reset bot API key"""
    bot = db.execute(
        "SELECT id FROM bots WHERE id = %s AND user_id = %s",
        (bot_id, current_user['id']),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    new_api_key = generate_api_key()

    db.execute(
        "UPDATE bots SET api_key = %s WHERE id = %s",
        (new_api_key, bot_id)
    )

    return {"api_key": new_api_key}
