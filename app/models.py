from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth Models


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    plan_type: str
    tokens_used: int
    token_limit: int
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Bot Models


class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    welcome_message: Optional[str] = "Hello! How can I help you?"
    primary_color: Optional[str] = "#3B82F6"


class BotResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    api_key: str
    welcome_message: str
    primary_color: str
    created_at: datetime


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    primary_color: Optional[str] = None

# Document Models


class DocumentResponse(BaseModel):
    id: str
    bot_id: str
    file_name: str
    file_type: str
    file_size: int
    processed: bool
    uploaded_at: datetime


class DocumentUploadResponse(BaseModel):
    id: str
    file_name: str
    chunks_created: int
    message: str

# Embedding Models


class EmbedCodeResponse(BaseModel):
    bot_id: str
    iframe: str
    script: str
    instructions: str

# Chat Models


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str

# Dashboard Stats


class DashboardStats(BaseModel):
    total_bots: int
    total_documents: int
    total_conversations: int
    total_messages: int
    tokens_used: int
    token_limit: int
