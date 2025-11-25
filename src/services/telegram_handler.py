"""Telegram update handler"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import get_logger
from src.services.conversation_manager import ConversationManager
from src.services.telegram_client import TelegramClient

logger = get_logger(__name__)


class TelegramHandler:
    """Handles incoming Telegram updates"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_manager = ConversationManager(db)
        self.telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
    
    async def process_update(self, update: Dict[str, Any]):
        """Process incoming Telegram update"""
        
        # Extract message or callback query
        message = update.get("message")
        callback_query = update.get("callback_query")
        
        if message:
            await self.handle_message(message)
        elif callback_query:
            await self.handle_callback_query(callback_query)
        else:
            logger.warning("Unknown update type", update_id=update.get("update_id"))
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle incoming message"""
        try:
            # Extract message data
            chat_id = message["chat"]["id"]
            telegram_user_id = message["from"]["id"]
            username = message["from"].get("username")
            text = message.get("text", "")
            message_id = message["message_id"]
            
            logger.info(
                "Processing message",
                chat_id=chat_id,
                user_id=telegram_user_id,
                text=text[:50],
            )
            
            # Get or create conversation
            conversation = await self.conversation_manager.get_or_create(
                telegram_user_id=telegram_user_id,
                telegram_username=username,
            )
            
            # Save user message
            await self.conversation_manager.add_message(
                conversation_id=str(conversation.id),
                sender_type="user",
                content=text,
                telegram_message_id=message_id,
            )
            
            # Handle commands
            if text.startswith("/"):
                await self.handle_command(chat_id, text, conversation)
                return
            
            # For now, just acknowledge
            await self.telegram_client.send_message(
                chat_id=chat_id,
                text="Message received! Full bot functionality coming soon.",
            )
            
        except Exception as e:
            logger.error("Error handling message", error=str(e), exc_info=True)
    
    async def handle_command(
        self, chat_id: int, command: str, conversation: Any
    ):
        """Handle bot commands"""
        
        if command == "/start":
            await self.handle_start_command(chat_id)
        elif command == "/help":
            await self.handle_help_command(chat_id)
        else:
            await self.telegram_client.send_message(
                chat_id=chat_id,
                text=f"Unknown command: {command}",
            )
    
    async def handle_start_command(self, chat_id: int):
        """Handle /start command with inline keyboard"""
        
        welcome_message = (
            "👋 Welcome to Dev2Production!\n\n"
            "I'm your AI assistant for DevOps, Cloud Architecture, "
            "and Custom Software Development.\n\n"
            "How can I help you today?"
        )
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 Start a Project", "callback_data": "action:start_project"}],
                [{"text": "💬 Ask Questions", "callback_data": "action:ask_questions"}],
                [{"text": "📚 Learn About Services", "callback_data": "action:services"}],
                [{"text": "👤 Talk to Human", "callback_data": "action:escalate"}],
            ]
        }
        
        await self.telegram_client.send_message(
            chat_id=chat_id,
            text=welcome_message,
            reply_markup=keyboard,
        )
    
    async def handle_help_command(self, chat_id: int):
        """Handle /help command"""
        
        help_text = (
            "🤖 *Bot Commands*\n\n"
            "/start - Start conversation\n"
            "/help - Show this help message\n\n"
            "*What I can do:*\n"
            "• Answer questions about DevOps & Cloud\n"
            "• Help you start a new project\n"
            "• Connect you with our team\n"
            "• Provide pricing information"
        )
        
        await self.telegram_client.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode="Markdown",
        )
    
    async def handle_callback_query(self, callback_query: Dict[str, Any]):
        """Handle inline keyboard button clicks"""
        try:
            query_id = callback_query["id"]
            data = callback_query["data"]
            chat_id = callback_query["message"]["chat"]["id"]
            
            logger.info("Processing callback", data=data, chat_id=chat_id)
            
            # Answer callback query
            await self.telegram_client.answer_callback_query(query_id)
            
            # Handle different actions
            if data == "action:start_project":
                await self.telegram_client.send_message(
                    chat_id=chat_id,
                    text="📋 Project intake flow coming soon! Please describe your project.",
                )
            elif data == "action:ask_questions":
                await self.telegram_client.send_message(
                    chat_id=chat_id,
                    text="💬 Ask me anything about our services!",
                )
            elif data == "action:services":
                await self.telegram_client.send_message(
                    chat_id=chat_id,
                    text=(
                        "📚 *Our Services:*\n\n"
                        "• DevOps & CI/CD Pipeline Setup\n"
                        "• Cloud Architecture (AWS, Azure, GCP)\n"
                        "• Kubernetes & Container Orchestration\n"
                        "• Infrastructure as Code\n"
                        "• Custom Software Development\n"
                        "• System Integration\n\n"
                        "Visit: dev2production.tech"
                    ),
                    parse_mode="Markdown",
                )
            elif data == "action:escalate":
                await self.telegram_client.send_message(
                    chat_id=chat_id,
                    text="👤 Connecting you to our team... (Feature coming soon!)",
                )
            
        except Exception as e:
            logger.error("Error handling callback query", error=str(e), exc_info=True)
