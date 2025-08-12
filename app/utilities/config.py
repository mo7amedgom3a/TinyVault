from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application configuration settings."""
    
    db_url: str = "sqlite+aiosqlite:///./data/tinyvault.db"
    
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "test_token")

    admin_api_key: str = os.getenv("ADMIN_API_KEY", "test_admin_key")
    
    webhook_secret: Optional[str] = os.getenv("WEBHOOK_SECRET")
    
    app_name: str = "TinyVault"

    class Config:
        env_file = ".env"
        case_sensitive = False
        
        env_prefix = ""
        
        extra = "ignore"

settings = Settings()