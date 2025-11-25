"""Telegram Bot API client"""
import httpx
from typing import Dict, Any, Optional

from src.core.logging import get_logger

logger = get_logger(__name__)


class TelegramClient:
    """Client for Telegram Bot API"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a text message"""
        
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            response = await self.client.post(
                f"{self.base_url}/sendMessage",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error("Failed to send message", error=str(e), chat_id=chat_id)
            raise
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ):
        """Answer callback query from inline keyboard"""
        
        payload = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert,
        }
        
        if text:
            payload["text"] = text
        
        try:
            response = await self.client.post(
                f"{self.base_url}/answerCallbackQuery",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error("Failed to answer callback query", error=str(e))
            raise
    
    async def set_webhook(self, webhook_url: str, secret_token: str):
        """Set webhook URL"""
        
        payload = {
            "url": webhook_url,
            "secret_token": secret_token,
            "allowed_updates": ["message", "callback_query"],
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/setWebhook",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            logger.info("Webhook set successfully", result=result)
            return result
            
        except Exception as e:
            logger.error("Failed to set webhook", error=str(e))
            raise
    
    async def get_webhook_info(self):
        """Get current webhook information"""
        
        try:
            response = await self.client.get(f"{self.base_url}/getWebhookInfo")
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error("Failed to get webhook info", error=str(e))
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
