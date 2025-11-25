"""Conversation management service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.models import Conversation, Message, ConversationStatus, SenderType
from src.core.logging import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """Manages user conversations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create(
        self, telegram_user_id: int, telegram_username: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one"""
        
        # Try to find existing active conversation
        stmt = select(Conversation).where(
            Conversation.telegram_user_id == telegram_user_id,
            Conversation.status == ConversationStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            logger.info("Found existing conversation", conversation_id=str(conversation.id))
            return conversation
        
        # Create new conversation
        conversation = Conversation(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            status=ConversationStatus.ACTIVE,
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        logger.info(
            "Created new conversation",
            conversation_id=str(conversation.id),
            user_id=telegram_user_id,
        )
        
        return conversation
    
    async def add_message(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        telegram_message_id: Optional[int] = None,
        llm_metadata: Optional[dict] = None,
    ) -> Message:
        """Add message to conversation"""
        
        message = Message(
            conversation_id=conversation_id,
            sender_type=SenderType(sender_type),
            content=content,
            telegram_message_id=telegram_message_id,
        )
        
        # Add LLM metadata if provided
        if llm_metadata:
            message.llm_used = True
            message.llm_model = llm_metadata.get("model")
            message.llm_tokens_used = llm_metadata.get("tokens")
            message.llm_confidence = llm_metadata.get("confidence")
            message.llm_latency_ms = llm_metadata.get("latency_ms")
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(
            "Added message",
            conversation_id=conversation_id,
            sender_type=sender_type,
            llm_used=message.llm_used,
        )
        
        return message
    
    async def get_messages(
        self, conversation_id: str, limit: int = 20
    ) -> list[Message]:
        """Get recent messages from conversation"""
        
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        
        # Return in chronological order
        return list(reversed(messages))
