from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import json
from app.database import db
from app.services.openai_service import openai_service
from app.services.embedding_service import embedding_service
from app.database import db  # Add 'app.'
from app.services.openai_service import openai_service  # Add 'app.'
from app.services.embedding_service import embedding_service  # Add 'app.'
router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    bot_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, fastapi_request: Request):
    # Verify bot exists
    bot = db.execute(
        "SELECT id, welcome_message FROM bots WHERE id = %s AND api_key = %s",
        # In production, use separate API key
        (request.bot_id, request.bot_id),
        fetch_one=True
    )

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Create or get session
    session_id = request.session_id or str(uuid.uuid4())

    # Get visitor info
    visitor_ip = fastapi_request.client.host
    user_agent = fastapi_request.headers.get("user-agent", "")

    # Find or create conversation
    conversation = db.execute(
        """SELECT id FROM conversations 
           WHERE bot_id = %s AND session_id = %s""",
        (request.bot_id, session_id),
        fetch_one=True
    )

    if not conversation:
        # New conversation
        conversation_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO conversations (id, bot_id, session_id, visitor_ip, user_agent)
               VALUES (%s, %s, %s, %s, %s)""",
            (conversation_id, request.bot_id, session_id, visitor_ip, user_agent)
        )

        # Save welcome message if first message
        if bot['welcome_message']:
            db.execute(
                """INSERT INTO messages (id, conversation_id, role, content)
                   VALUES (UUID(), %s, 'assistant', %s)""",
                (conversation_id, bot['welcome_message'])
            )
    else:
        conversation_id = conversation['id']

    # Save user message
    db.execute(
        """INSERT INTO messages (id, conversation_id, role, content)
           VALUES (UUID(), %s, 'user', %s)""",
        (conversation_id, request.message)
    )

    # Find relevant context
    context_chunks = embedding_service.find_similar_chunks(
        request.bot_id,
        request.message,
        top_k=3
    )

    # Get conversation history (last 5 messages)
    history = db.execute(
        """SELECT role, content FROM messages 
           WHERE conversation_id = %s 
           ORDER BY created_at DESC LIMIT 5""",
        (conversation_id,),
        fetch_all=True
    )

    # Prepare messages for OpenAI
    messages = []
    for msg in reversed(history):
        messages.append({"role": msg['role'], "content": msg['content']})

    # Generate response
    response = openai_service.generate_chat_response(
        messages=messages,
        context_chunks=context_chunks
    )

    # Save assistant response
    db.execute(
        """INSERT INTO messages (id, conversation_id, role, content, tokens_used)
           VALUES (UUID(), %s, 'assistant', %s, %s)""",
        (conversation_id, response['content'], response['tokens'])
    )

    return ChatResponse(
        reply=response['content'],
        session_id=session_id
    )
