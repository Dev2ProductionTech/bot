"""Telegram webhook handlers"""
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import get_logger
from src.db.base import get_db
from src.services.telegram_handler import TelegramHandler

router = APIRouter()
logger = get_logger(__name__)


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str = Header(None),
):
    """
    Telegram webhook endpoint
    
    Receives updates from Telegram Bot API
    """
    # Validate webhook secret
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret received")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Parse incoming update
    try:
        update_data = await request.json()
        logger.info("Received telegram update", update_id=update_data.get("update_id"))
        
        # Process update
        handler = TelegramHandler(db)
        await handler.process_update(update_data)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error("Failed to process webhook", error=str(e), exc_info=True)
        # Always return 200 to Telegram to prevent retries
        return {"ok": True}
