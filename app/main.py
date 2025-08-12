from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import admin, telegram, diagnostics_router
from app.utilities.dependencies import get_db
from app.utilities.database import init_db, close_db
from app.utilities.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting TinyVault application...")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TinyVault application...")
    await close_db()
    logger.info("Database connections closed")


def custom_openapi():
    """Custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TinyVault API",
        version="1.0.0",
        description="""
        # TinyVault API
        
        A service for storing and retrieving short notes and links via Telegram bot.
        
        ## Authentication
        
        ### Admin API
        The admin endpoints require authentication using an API key in the `X-API-Key` header.
        
        **Example:**
        ```
        X-API-Key: your_admin_api_key_here
        ```
        
        ### Telegram Webhook
        Telegram webhook endpoints handle bot updates automatically.
        
        ## Getting Started
        
        1. Set your bot's webhook URL
        2. Use the admin API with your API key for administrative operations
        3. Monitor system health and statistics
        """,
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create FastAPI application
app = FastAPI(
    title="TinyVault",
    description="A service for storing and retrieving short notes and links via Telegram bot",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Set custom OpenAPI schema
app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(admin.router)
app.include_router(telegram.router)
app.include_router(diagnostics_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TinyVault",
        "version": "1.0.0",
        "description": "A service for storing and retrieving short notes and links via Telegram bot",
        "endpoints": {
            "admin": "/admin",
            "telegram": "/telegram",
            "webhook_setup": "/telegram/set-webhook",
            "webhook_info": "/telegram/webhook-info",
            "test_webhook": "/telegram/test-webhook",
            "db": "/db/ping",
            "docs": "/docs",
            "health": "/health"
        },
        "authentication": {
            "admin_api": "X-API-Key header required for /admin endpoints"
        }
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        from sqlalchemy import text
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-08-12T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.get("/info")
async def get_info():
    """Get application configuration information."""
    return {
        "app_name": settings.app_name,
        "database_url": settings.db_url.replace(settings.db_url.split('@')[0].split(':')[-1], '***') if '@' in settings.db_url else settings.db_url,
        "telegram_bot_configured": bool(settings.telegram_bot_token),
        "admin_api_configured": bool(settings.admin_api_key),
        "webhook_secret_configured": bool(settings.webhook_secret)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 