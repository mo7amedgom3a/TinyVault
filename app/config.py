from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    db_url: str = "sqlite+aiosqlite:///./data/tinyvault.db"
    
    telegram_bot_token: str = "test_token" 

    admin_api_key: str = "test_admin_key"  
    
    webhook_secret: Optional[str] = None
    

    app_name: str = "TinyVault"
    debug: bool = True  
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        env_prefix = ""
        
        extra = "ignore"

settings = Settings() 