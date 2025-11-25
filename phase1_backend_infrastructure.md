# Phase 1 — Backend & Infrastructure Setup

## Task 7: Initialize FastAPI Project Structure

### Project Structure
```
pythonBot/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Run tests, linting on PR
│       └── deploy.yml                # Deploy to staging/prod
├── alembic/
│   ├── versions/                     # Database migrations
│   ├── env.py
│   └── alembic.ini
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhooks.py               # Telegram webhook endpoint
│   │   ├── admin.py                  # Admin/dashboard endpoints
│   │   └── health.py                 # Health check endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic settings
│   │   ├── security.py               # Token validation, secrets
│   │   ├── logging.py                # Structured logging setup
│   │   └── dependencies.py           # FastAPI dependencies
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                   # SQLAlchemy base
│   │   ├── session.py                # Async session factory
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── conversation.py
│   │       ├── message.py
│   │       ├── lead.py
│   │       ├── attachment.py
│   │       ├── session.py
│   │       └── agent.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── telegram.py               # Telegram API client
│   │   ├── conversation_manager.py   # Conversation CRUD
│   │   ├── message_processor.py      # Message normalization
│   │   ├── intent_detector.py        # Intent/FAQ matching
│   │   ├── llm_adapter.py            # LongCat integration
│   │   ├── lead_manager.py           # Lead qualification
│   │   └── file_handler.py           # File upload/storage
│   ├── workers/
│   │   ├── __init__.py
│   │   └── llm_worker.py             # Background LLM processing
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── telegram.py               # Telegram webhook schemas
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── lead.py
│   └── utils/
│       ├── __init__.py
│       ├── cache.py                  # Redis utilities
│       ├── rate_limit.py             # Rate limiting logic
│       └── metrics.py                # Prometheus metrics
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── unit/
│   │   ├── test_message_processor.py
│   │   ├── test_intent_detector.py
│   │   └── test_conversation_manager.py
│   ├── integration/
│   │   ├── test_webhook.py
│   │   └── test_llm_flow.py
│   └── fixtures/
│       └── telegram_messages.json
├── scripts/
│   ├── setup_dev.sh                  # Dev environment setup
│   └── seed_db.py                    # Seed test data
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
├── pyproject.toml                    # Poetry dependencies
├── pytest.ini
├── .flake8                           # Linting config
├── .pylintrc
├── mypy.ini                          # Type checking
├── README.md
└── main.py                           # FastAPI entry point
```

### pyproject.toml (Poetry)
```toml
[tool.poetry]
name = "dev2production-bot"
version = "0.1.0"
description = "Telegram bot for dev2production.tech services"
authors = ["Dev2Production Team"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0.25"}
alembic = "^1.13.1"
asyncpg = "^0.29.0"
redis = {extras = ["hiredis"], version = "^5.0.1"}
pydantic = {extras = ["email"], version = "^2.5.3"}
pydantic-settings = "^2.1.0"
httpx = "^0.26.0"
python-multipart = "^0.0.6"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
prometheus-client = "^0.19.0"
structlog = "^24.1.0"
tenacity = "^8.2.3"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
pytest-cov = "^4.1.0"
black = "^24.1.1"
flake8 = "^7.0.0"
mypy = "^1.8.0"
isort = "^5.13.2"
pylint = "^3.0.3"
httpx-mock = "^0.7.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

### Docker Setup
```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev packages in prod)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY main.py ./

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: botuser
      POSTGRES_PASSWORD: botpass
      POSTGRES_DB: dev2prod_bot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U botuser"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  bot-api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://botuser:botpass@postgres:5432/dev2prod_bot
      REDIS_URL: redis://redis:6379/0
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      TELEGRAM_WEBHOOK_SECRET: ${TELEGRAM_WEBHOOK_SECRET}
      LONGCAT_API_KEY: ${LONGCAT_API_KEY}
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # Hot reload in dev
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  llm-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://botuser:botpass@postgres:5432/dev2prod_bot
      REDIS_URL: redis://redis:6379/0
      LONGCAT_API_KEY: ${LONGCAT_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src

volumes:
  postgres_data:
  redis_data:
```

### GitHub Actions CI
```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      - name: Install dependencies
        run: poetry install
      - name: Run Black
        run: poetry run black --check src/ tests/
      - name: Run isort
        run: poetry run isort --check-only src/ tests/
      - name: Run Flake8
        run: poetry run flake8 src/ tests/
      - name: Run MyPy
        run: poetry run mypy src/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      - name: Install dependencies
        run: poetry install
      - name: Run tests
        run: poetry run pytest --cov=src --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql+asyncpg://testuser:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379/0
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Task 8: Set up Postgres Schema with SQLAlchemy

### Database Models

#### src/db/base.py
```python
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models"""
    pass

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

#### src/db/models/conversation.py
```python
from sqlalchemy import String, Integer, Enum, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base, TimestampMixin
import uuid
import enum

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ESCALATED = "escalated"
    CLOSED = "closed"
    ARCHIVED = "archived"

class LeadScore(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    telegram_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus),
        default=ConversationStatus.ACTIVE,
        nullable=False
    )
    lead_score: Mapped[LeadScore | None] = mapped_column(
        Enum(LeadScore),
        nullable=True
    )
    
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    escalated_to_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    lead = relationship("Lead", back_populates="conversation", uselist=False)
    attachments = relationship("Attachment", back_populates="conversation")
```

#### src/db/models/message.py
```python
from sqlalchemy import String, Integer, Enum, Text, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base, TimestampMixin
import uuid
import enum

class SenderType(str, enum.Enum):
    USER = "user"
    BOT = "bot"
    AGENT = "agent"

class ContentType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    COMMAND = "command"

class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
    sender_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    telegram_message_id: Mapped[int] = mapped_column(Integer, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType),
        default=ContentType.TEXT
    )
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # LLM tracking
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
```

#### src/db/models/lead.py
```python
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base, TimestampMixin
import uuid
import enum

class ProjectType(str, enum.Enum):
    DEVOPS = "devops"
    CUSTOM_APP = "custom_app"
    CLOUD = "cloud"
    INTEGRATION = "integration"
    OTHER = "other"

class BudgetRange(str, enum.Enum):
    UNDER_10K = "<10k"
    TEN_TO_FIFTY_K = "10k-50k"
    FIFTY_TO_150K = "50k-150k"
    OVER_150K = "150k+"
    UNKNOWN = "unknown"

class Timeline(str, enum.Enum):
    URGENT = "urgent"
    NORMAL = "normal"
    FLEXIBLE = "flexible"
    EXPLORING = "exploring"

class LeadStage(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"

class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Contact info
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Project details
    project_type: Mapped[ProjectType | None] = mapped_column(Enum(ProjectType), nullable=True)
    project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_range: Mapped[BudgetRange] = mapped_column(
        Enum(BudgetRange),
        default=BudgetRange.UNKNOWN
    )
    timeline: Mapped[Timeline | None] = mapped_column(Enum(Timeline), nullable=True)
    
    # Lead scoring
    lead_score: Mapped[str] = mapped_column(String(20), default="cold")
    lead_source: Mapped[str] = mapped_column(String(50), default="telegram_bot")
    lead_stage: Mapped[LeadStage] = mapped_column(
        Enum(LeadStage),
        default=LeadStage.NEW
    )
    
    # Tracking
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="lead")
```

### Alembic Migration
```python
# alembic/versions/001_initial_schema.py
"""Initial schema

Revision ID: 001
Create Date: 2025-01-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('telegram_user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('telegram_username', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('active', 'escalated', 'closed', 'archived', name='conversationstatus'), nullable=False),
        sa.Column('lead_score', sa.Enum('hot', 'warm', 'cold', 'unqualified', name='leadscore'), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_to_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.Enum('user', 'bot', 'agent', name='sendertype'), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('telegram_message_id', sa.Integer(), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Enum('text', 'image', 'document', 'command', name='contenttype'), nullable=False),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('llm_used', sa.Boolean(), default=False),
        sa.Column('llm_model', sa.String(50), nullable=True),
        sa.Column('llm_tokens_used', sa.Integer(), nullable=True),
        sa.Column('llm_latency_ms', sa.Integer(), nullable=True),
        sa.Column('llm_confidence', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE')
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('project_type', sa.Enum('devops', 'custom_app', 'cloud', 'integration', 'other', name='projecttype'), nullable=True),
        sa.Column('project_description', sa.Text(), nullable=True),
        sa.Column('budget_range', sa.Enum('<10k', '10k-50k', '50k-150k', '150k+', 'unknown', name='budgetrange'), nullable=False),
        sa.Column('timeline', sa.Enum('urgent', 'normal', 'flexible', 'exploring', name='timeline'), nullable=True),
        sa.Column('lead_score', sa.String(20), default='cold'),
        sa.Column('lead_source', sa.String(50), default='telegram_bot'),
        sa.Column('lead_stage', sa.Enum('new', 'contacted', 'qualified', 'proposal_sent', 'won', 'lost', name='leadstage'), nullable=False),
        sa.Column('contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE')
    )

def downgrade():
    op.drop_table('leads')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.execute('DROP TYPE IF EXISTS leadscore')
    op.execute('DROP TYPE IF EXISTS conversationstatus')
    op.execute('DROP TYPE IF EXISTS sendertype')
    op.execute('DROP TYPE IF EXISTS contenttype')
    op.execute('DROP TYPE IF EXISTS projecttype')
    op.execute('DROP TYPE IF EXISTS budgetrange')
    op.execute('DROP TYPE IF EXISTS timeline')
    op.execute('DROP TYPE IF EXISTS leadstage')
```

---

## Task 9: Configure Redis for Sessions & Caching

### src/utils/cache.py
```python
import redis.asyncio as redis
from typing import Optional, Any
import json
from src.core.config import settings

class RedisCache:
    """Redis cache wrapper for sessions and rate limiting"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        return await self.redis.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set key with optional TTL (seconds)"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.set(key, value, ex=ttl)
    
    async def delete(self, key: str):
        """Delete key"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        await self.redis.delete(key)
    
    async def increment(self, key: str, ttl: Optional[int] = None) -> int:
        """Increment counter, set TTL on first increment"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        count = await self.redis.incr(key)
        if count == 1 and ttl:
            await self.redis.expire(key, ttl)
        return count
    
    async def get_session(self, user_id: int) -> Optional[dict]:
        """Get user session data"""
        key = f"session:{user_id}"
        data = await self.get(key)
        return json.loads(data) if data else None
    
    async def set_session(self, user_id: int, data: dict, ttl: int = 86400):
        """Set user session data (default 24h TTL)"""
        key = f"session:{user_id}"
        await self.set(key, data, ttl)
    
    async def delete_session(self, user_id: int):
        """Delete user session"""
        key = f"session:{user_id}"
        await self.delete(key)

# Global cache instance
cache = RedisCache()
```

### src/utils/rate_limit.py
```python
from src.utils.cache import cache
from fastapi import HTTPException, status

class RateLimiter:
    """Rate limiting using Redis counters"""
    
    @staticmethod
    async def check_rate_limit(
        user_id: int,
        limit_per_hour: int = 60,
        limit_per_day: int = 500
    ) -> bool:
        """
        Check if user is within rate limits
        Returns True if allowed, raises HTTPException if exceeded
        """
        hour_key = f"rate:hour:{user_id}"
        day_key = f"rate:day:{user_id}"
        
        # Check hourly limit
        hour_count = await cache.increment(hour_key, ttl=3600)
        if hour_count > limit_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Check daily limit
        day_count = await cache.increment(day_key, ttl=86400)
        if day_count > limit_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily rate limit exceeded. Please try again tomorrow."
            )
        
        return True
    
    @staticmethod
    async def get_rate_limit_status(user_id: int) -> dict:
        """Get current rate limit status for user"""
        hour_key = f"rate:hour:{user_id}"
        day_key = f"rate:day:{user_id}"
        
        hour_count = await cache.get(hour_key) or 0
        day_count = await cache.get(day_key) or 0
        
        return {
            "hour_count": int(hour_count),
            "hour_limit": 60,
            "day_count": int(day_count),
            "day_limit": 500
        }
```

---

## Task 10-16: Additional Implementation Files

Due to length constraints, the remaining tasks (10-16) include:

- **Task 10:** FastAPI app factory (`main.py`, `core/config.py`)
- **Task 11:** Telegram webhook endpoint with secret validation
- **Task 12:** Message normalization layer
- **Task 13:** Conversation manager service
- **Task 14:** Background job system (async worker)
- **Task 15:** Pluggable AI adapter interface
- **Task 16:** Structured logging & error monitoring

### Quick Implementation Guide

#### main.py
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.config import settings
from src.core.logging import setup_logging
from src.utils.cache import cache
from src.db.session import init_db
from src.api import webhooks, health, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    setup_logging()
    await cache.connect()
    await init_db()
    yield
    # Shutdown
    await cache.disconnect()

app = FastAPI(
    title="Dev2Production Bot API",
    version="0.1.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(webhooks.router, prefix="/webhook", tags=["webhook"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## Implementation Checklist for Phase 1

- [ ] Initialize project structure with Poetry
- [ ] Set up Docker and docker-compose files
- [ ] Configure GitHub Actions CI/CD
- [ ] Create all SQLAlchemy models
- [ ] Write Alembic migration scripts
- [ ] Implement Redis cache utilities
- [ ] Build FastAPI app factory
- [ ] Create Telegram webhook endpoint
- [ ] Implement message normalization layer
- [ ] Build conversation manager service
- [ ] Set up background worker system
- [ ] Create AI adapter interface
- [ ] Configure structured logging
- [ ] Write unit tests for core services
- [ ] Test local Docker setup

**Next Steps:** Move to Phase 2 - Core Telegram Bot Features
