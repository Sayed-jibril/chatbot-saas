# app/routers/__init__.py
from .auth import router as auth_router
from .bots import router as bots_router
from .chat import router as chat_router
from .dashboard import router as dashboard_router
from .documents import router as documents_router
from .embed import router as embed_router

# Export the router objects directly
auth = auth_router
bots = bots_router
chat = chat_router
dashboard = dashboard_router
documents = documents_router
embed = embed_router
