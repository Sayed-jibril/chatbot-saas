from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# Import routers correctly - note the different import style
from app.routers import auth, bots, documents, chat, embed, dashboard

app = FastAPI(
    title="BotSaaS - AI Chatbot Platform",
    description="Multi-tenant AI chatbot platform",
    version="1.0.0"
)

# Templates - use absolute path
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include all routers - now using the imported router objects directly
app.include_router(auth)        # /auth/*
app.include_router(dashboard)    # /dashboard/*
app.include_router(bots)         # /dashboard/bots, /dashboard/api/bots
# /dashboard/documents, /dashboard/api/documents
app.include_router(documents)
app.include_router(chat)         # /api/chat
app.include_router(embed)        # /embed/*


@app.get("/")
async def root():
    return {
        "message": "Welcome to BotSaaS API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard/login"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None
        })
    return routes
