"""Script to set Telegram webhook"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.services.telegram_client import TelegramClient
from src.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def main():
    """Set webhook for Telegram bot"""
    
    client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
    
    try:
        # Get current webhook info
        logger.info("Getting current webhook info...")
        info = await client.get_webhook_info()
        logger.info("Current webhook", info=info)
        
        # Set new webhook
        logger.info("Setting webhook", url=settings.TELEGRAM_WEBHOOK_URL)
        result = await client.set_webhook(
            webhook_url=settings.TELEGRAM_WEBHOOK_URL,
            secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
        )
        
        logger.info("Webhook set successfully", result=result)
        
        # Verify webhook
        info = await client.get_webhook_info()
        logger.info("Webhook verified", info=info)
        
    except Exception as e:
        logger.error("Failed to set webhook", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
