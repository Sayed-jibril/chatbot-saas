import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'chatbot_saas')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Models
    CHAT_MODEL = os.getenv('CHAT_MODEL', 'gpt-4o-mini')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

    # App
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    APP_URL = os.getenv('APP_URL', 'http://localhost:8000')

    # Plan limits
    PLAN_LIMITS = {
        'free': {'bots': 1, 'documents': 5, 'tokens': 10000},
        'pro': {'bots': 5, 'documents': 100, 'tokens': 100000},
        'business': {'bots': 100, 'documents': 1000, 'tokens': 1000000}
    }
