"""Database models"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class ConversationStatus(str, enum.Enum):
    """Conversation status enum"""
    ACTIVE = "active"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SenderType(str, enum.Enum):
    """Message sender type"""
    USER = "user"
    BOT = "bot"
    AGENT = "agent"


class LeadScore(str, enum.Enum):
    """Lead quality score"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class Conversation(Base):
    """User conversation sessions"""
    __tablename__ = "conversations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus), default=ConversationStatus.ACTIVE, index=True
    )
    lead_score: Mapped[Optional[LeadScore]] = mapped_column(
        Enum(LeadScore), nullable=True
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    leads: Mapped[list["Lead"]] = relationship(
        "Lead", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Chat messages with LLM metadata"""
    __tablename__ = "messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType))
    content: Mapped[str] = mapped_column(Text)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # LLM metadata
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class Lead(Base):
    """Lead/CRM data from project intake"""
    __tablename__ = "leads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    
    # Contact info
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Project details
    project_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timeline: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    budget: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Scoring
    score: Mapped[LeadScore] = mapped_column(Enum(LeadScore), default=LeadScore.COLD)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="leads")
