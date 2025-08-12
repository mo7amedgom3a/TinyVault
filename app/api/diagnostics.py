from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.utilities.dependencies import get_db

router = APIRouter(prefix="/db", tags=["diagnostics"])


@router.get("/ping")
async def db_ping(db: AsyncSession = Depends(get_db)):
    """Simple endpoint to verify database connectivity.
    Executes `SELECT 1` and returns the result.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        return {"ok": True, "result": value}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connectivity failed: {str(e)}"
        ) 