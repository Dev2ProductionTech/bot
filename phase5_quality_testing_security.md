# Phase 5 — Quality, Testing & Security

## Task 39: Unit Tests for Core Components

### Test Structure
```
tests/
├── __init__.py
├── conftest.py                      # Pytest fixtures
├── unit/
│   ├── test_webhook_parser.py      # Telegram webhook parsing
│   ├── test_intent_detector.py     # Intent detection & regex
│   ├── test_conversation_manager.py # Conversation CRUD
│   ├── test_llm_adapter.py         # AI adapter & mocking
│   ├── test_project_intake.py      # Multi-step flow logic
│   ├── test_pii_masker.py          # PII redaction
│   ├── test_rate_limiter.py        # Rate limiting logic
│   └── test_file_handler.py        # File validation
├── integration/
│   ├── test_webhook_flow.py        # Full webhook → response
│   ├── test_database.py            # DB operations
│   └── test_escalation_flow.py     # Bot → Agent handoff
└── fixtures/
    ├── telegram_messages.json       # Sample Telegram updates
    └── mock_responses.json          # Sample LLM responses
```

### Implementation: conftest.py
```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.base import Base
from src.utils.cache import RedisCache
from src.core.config import settings

# Override settings for testing
settings.DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_bot"
settings.REDIS_URL = "redis://localhost:6379/1"  # Use DB 1 for tests

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    """Create test database session"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture(scope="function")
async def redis_cache():
    """Create test Redis cache"""
    cache = RedisCache()
    await cache.connect()
    
    # Clear test database
    await cache.redis.flushdb()
    
    yield cache
    
    await cache.disconnect()

@pytest.fixture
def sample_telegram_message():
    """Sample Telegram message fixture"""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "John",
                "username": "johndoe",
                "language_code": "en"
            },
            "chat": {
                "id": 987654321,
                "first_name": "John",
                "username": "johndoe",
                "type": "private"
            },
            "date": 1637001234,
            "text": "/start"
        }
    }

@pytest.fixture
def sample_callback_query():
    """Sample callback query fixture"""
    return {
        "update_id": 123456790,
        "callback_query": {
            "id": "callback123",
            "from": {
                "id": 987654321,
                "username": "johndoe"
            },
            "message": {
                "message_id": 2,
                "chat": {"id": 987654321}
            },
            "data": "action:start_project"
        }
    }
```

### Test: test_intent_detector.py
```python
import pytest
from src.services.intent_detector import IntentDetector

class TestIntentDetector:
    """Test suite for intent detection"""
    
    def setup_method(self):
        self.detector = IntentDetector()
    
    def test_detect_services_inquiry(self):
        """Test detection of service inquiry"""
        queries = [
            "What services do you offer?",
            "Tell me about your services",
            "What can you do for me?"
        ]
        
        for query in queries:
            intent = self.detector.detect_intent(query)
            assert intent.name == "faq_services"
            assert intent.confidence >= 0.8
            assert intent.canned_response is not None
    
    def test_detect_pricing_inquiry(self):
        """Test detection of pricing questions"""
        queries = [
            "How much does it cost?",
            "What are your rates?",
            "Pricing information please"
        ]
        
        for query in queries:
            intent = self.detector.detect_intent(query)
            assert intent.name == "faq_pricing_general"
            assert intent.confidence >= 0.8
    
    def test_detect_escalation_intent(self):
        """Test detection of human escalation request"""
        queries = [
            "I want to talk to a human",
            "Can I speak to an agent?",
            "Connect me to your team"
        ]
        
        for query in queries:
            intent = self.detector.detect_intent(query)
            assert intent.name == "intent_escalate"
    
    def test_unknown_intent(self):
        """Test handling of unknown queries"""
        query = "asdfghjkl random nonsense"
        intent = self.detector.detect_intent(query)
        
        assert intent.name == "unknown"
        assert intent.confidence < 0.5
        assert intent.canned_response is None
    
    def test_should_use_llm(self):
        """Test LLM fallback logic"""
        # Low confidence should trigger LLM
        low_confidence_intent = self.detector.detect_intent("Tell me something vague")
        assert self.detector.should_use_llm(low_confidence_intent) is True
        
        # High confidence with canned response should not use LLM
        high_confidence_intent = self.detector.detect_intent("What services do you offer?")
        assert self.detector.should_use_llm(high_confidence_intent) is False
```

### Test: test_llm_adapter.py
```python
import pytest
from src.services.llm_adapter import (
    LongCatAdapter,
    MockLLMAdapter,
    LLMMessage,
    LLMResponse
)

@pytest.mark.asyncio
class TestLLMAdapter:
    """Test suite for LLM adapters"""
    
    async def test_mock_adapter_response(self):
        """Test mock adapter returns expected format"""
        adapter = MockLLMAdapter()
        
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant"),
            LLMMessage(role="user", content="Hello")
        ]
        
        response = await adapter.generate_response(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.tokens_used > 0
        assert 0 <= response.confidence <= 1
        assert response.model == "mock-model"
    
    async def test_token_estimation(self):
        """Test token counting logic"""
        adapter = MockLLMAdapter()
        
        text = "This is a sample text for token estimation"
        estimated_tokens = adapter.estimate_tokens(text)
        
        # Rough estimate: ~1 token per 4 characters
        expected_range = (len(text) // 5, len(text) // 3)
        assert expected_range[0] <= estimated_tokens <= expected_range[1]
    
    async def test_confidence_check(self):
        """Test confidence scoring"""
        adapter = MockLLMAdapter()
        
        # High confidence response
        confident_response = "This is a clear and complete answer."
        confidence = await adapter.check_confidence(confident_response)
        assert confidence >= 0.7
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Requires LongCat API key"
    )
    async def test_longcat_adapter_integration(self):
        """Integration test with real LongCat API"""
        adapter = LongCatAdapter(
            api_key=pytest.config.getoption("--longcat-key"),
            model="gpt-4o-mini"
        )
        
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant"),
            LLMMessage(role="user", content="What is 2+2?")
        ]
        
        response = await adapter.generate_response(messages, max_tokens=50)
        
        assert "4" in response.content.lower()
        assert response.tokens_used > 0
        assert response.latency_ms > 0
        
        await adapter.close()
```

### Test: test_conversation_manager.py
```python
import pytest
from src.services.conversation_manager import ConversationManager
from src.db.models.conversation import ConversationStatus

@pytest.mark.asyncio
class TestConversationManager:
    """Test suite for conversation management"""
    
    async def test_get_or_create_conversation(self, db_session):
        """Test conversation creation"""
        manager = ConversationManager()
        
        telegram_user_id = 123456
        username = "testuser"
        
        # First call should create
        conv1 = await manager.get_or_create(
            telegram_user_id=telegram_user_id,
            telegram_username=username
        )
        
        assert conv1 is not None
        assert conv1.telegram_user_id == telegram_user_id
        assert conv1.status == ConversationStatus.ACTIVE
        
        # Second call should retrieve existing
        conv2 = await manager.get_or_create(
            telegram_user_id=telegram_user_id,
            telegram_username=username
        )
        
        assert conv1.id == conv2.id
    
    async def test_update_conversation_status(self, db_session):
        """Test status update"""
        manager = ConversationManager()
        
        conv = await manager.get_or_create(
            telegram_user_id=123456,
            telegram_username="testuser"
        )
        
        # Update to escalated
        await manager.update_status(
            conversation_id=str(conv.id),
            status=ConversationStatus.ESCALATED
        )
        
        # Verify update
        updated_conv = await manager.get_by_id(str(conv.id))
        assert updated_conv.status == ConversationStatus.ESCALATED
        assert updated_conv.escalated_at is not None
    
    async def test_add_message(self, db_session):
        """Test message creation"""
        manager = ConversationManager()
        
        conv = await manager.get_or_create(
            telegram_user_id=123456,
            telegram_username="testuser"
        )
        
        # Add user message
        message = await manager.add_message(
            conversation_id=str(conv.id),
            sender_type="user",
            content="Hello, bot!",
            telegram_message_id=1
        )
        
        assert message is not None
        assert message.content == "Hello, bot!"
        assert message.sender_type.value == "user"
    
    async def test_get_conversation_history(self, db_session):
        """Test message retrieval"""
        manager = ConversationManager()
        
        conv = await manager.get_or_create(
            telegram_user_id=123456,
            telegram_username="testuser"
        )
        
        # Add multiple messages
        for i in range(5):
            await manager.add_message(
                conversation_id=str(conv.id),
                sender_type="user",
                content=f"Message {i}",
                telegram_message_id=i
            )
        
        # Get history
        messages = await manager.get_messages(
            conversation_id=str(conv.id),
            limit=3
        )
        
        assert len(messages) == 3
        assert messages[0].content == "Message 4"  # Most recent first
```

### Test: test_pii_masker.py
```python
import pytest
from src.services.pii_masker import PIIMasker

class TestPIIMasker:
    """Test suite for PII masking"""
    
    def setup_method(self):
        self.masker = PIIMasker()
    
    def test_email_masking(self):
        """Test email address masking"""
        text = "My email is john.doe@example.com"
        masked, redactions = self.masker.mask_pii(text)
        
        assert "john.doe@example.com" not in masked
        assert "@example.com" in masked  # Domain preserved
        assert len(redactions) == 1
        assert redactions[0]["type"] == "email"
    
    def test_phone_masking(self):
        """Test phone number masking"""
        texts = [
            "Call me at 555-123-4567",
            "Phone: (555) 123-4567",
            "+1 555 123 4567"
        ]
        
        for text in texts:
            masked, redactions = self.masker.mask_pii(text)
            assert "[PHONE_REDACTED]" in masked
            assert any(r["type"] == "phone" for r in redactions)
    
    def test_ssn_masking(self):
        """Test SSN masking"""
        text = "My SSN is 123-45-6789"
        masked, redactions = self.masker.mask_pii(text)
        
        assert "123-45-6789" not in masked
        assert "XXX-XX-XXXX" in masked
        assert redactions[0]["type"] == "ssn"
    
    def test_multiple_pii_types(self):
        """Test masking multiple PII types"""
        text = "Contact John at john@example.com or 555-1234"
        masked, redactions = self.masker.mask_pii(text)
        
        assert len(redactions) >= 2
        pii_types = [r["type"] for r in redactions]
        assert "email" in pii_types
        assert "phone" in pii_types
    
    def test_no_pii(self):
        """Test text without PII"""
        text = "This is a normal message with no sensitive information"
        masked, redactions = self.masker.mask_pii(text)
        
        assert masked == text
        assert len(redactions) == 0
```

---

## Task 40: Security Hardening

### Implementation: src/core/security.py

```python
import re
from typing import Any
from fastapi import HTTPException, status
import bleach
import structlog

logger = structlog.get_logger()

class SecurityValidator:
    """Input validation and sanitization"""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['b', 'i', 'u', 'a', 'code', 'pre']
    ALLOWED_ATTRIBUTES = {'a': ['href']}
    
    # Max lengths for various inputs
    MAX_MESSAGE_LENGTH = 4096  # Telegram limit
    MAX_USERNAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_FILENAME_LENGTH = 255
    
    # File restrictions
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.txt',
        '.jpg', '.jpeg', '.png', '.gif'
    }
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potentially dangerous HTML"""
        return bleach.clean(
            text,
            tags=SecurityValidator.ALLOWED_TAGS,
            attributes=SecurityValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_message_length(text: str) -> str:
        """Validate message length"""
        if len(text) > SecurityValidator.MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message too long (max {SecurityValidator.MAX_MESSAGE_LENGTH} chars)"
            )
        return text
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        if len(email) > SecurityValidator.MAX_EMAIL_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email too long"
            )
        
        return email.lower().strip()
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Check length
        if len(filename) > SecurityValidator.MAX_FILENAME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long"
            )
        
        # Check extension
        import os
        _, ext = os.path.splitext(filename.lower())
        
        if ext not in SecurityValidator.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(SecurityValidator.ALLOWED_FILE_EXTENSIONS)}"
            )
        
        return filename
    
    @staticmethod
    def validate_file_size(size_bytes: int) -> int:
        """Validate file size"""
        if size_bytes > SecurityValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large (max {SecurityValidator.MAX_FILE_SIZE // 1024 // 1024}MB)"
            )
        
        if size_bytes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file size"
            )
        
        return size_bytes
    
    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """Detect potential SQL injection attempts"""
        sql_keywords = [
            'select', 'insert', 'update', 'delete', 'drop',
            'union', 'exec', 'execute', 'script', '--',
            ';--', '/*', '*/', 'xp_', 'sp_'
        ]
        
        text_lower = text.lower()
        
        for keyword in sql_keywords:
            if keyword in text_lower:
                logger.warning(
                    "Potential SQL injection detected",
                    keyword=keyword,
                    text_preview=text[:50]
                )
                return True
        
        return False
    
    @staticmethod
    def detect_xss(text: str) -> bool:
        """Detect potential XSS attempts"""
        xss_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onload=',
            r'onclick=',
            r'<iframe',
            r'eval\(',
            r'alert\('
        ]
        
        text_lower = text.lower()
        
        for pattern in xss_patterns:
            if re.search(pattern, text_lower):
                logger.warning(
                    "Potential XSS detected",
                    pattern=pattern,
                    text_preview=text[:50]
                )
                return True
        
        return False
    
    @staticmethod
    def validate_and_sanitize_input(text: str, context: str = "message") -> str:
        """
        Comprehensive input validation
        
        Args:
            text: Input text to validate
            context: Context of input (message, email, etc.)
        
        Returns:
            Sanitized text
        
        Raises:
            HTTPException if validation fails
        """
        # Check for injection attempts
        if SecurityValidator.detect_sql_injection(text):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected"
            )
        
        if SecurityValidator.detect_xss(text):
            # Sanitize instead of rejecting for XSS
            text = SecurityValidator.sanitize_html(text)
        
        # Validate length
        if context == "message":
            text = SecurityValidator.validate_message_length(text)
        
        return text.strip()
```

### Security Middleware
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if times[-1] > current_time - 60
        }
        
        # Check rate limit
        if client_ip in self.requests:
            self.requests[client_ip].append(current_time)
            
            if len(self.requests[client_ip]) > self.requests_per_minute:
                return Response(
                    content="Rate limit exceeded",
                    status_code=429
                )
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)
```

---

## Task 41: Secure Secrets Management

### Implementation: src/core/secrets.py

```python
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import structlog

logger = structlog.get_logger()

class Settings(BaseSettings):
    """Application settings with secret management"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    
    # Application
    APP_NAME: str = Field(default="Dev2Production Bot")
    API_VERSION: str = Field(default="v1")
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Database
    DATABASE_URL: str = Field(...)
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    
    # Redis
    REDIS_URL: str = Field(...)
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., min_length=40)
    TELEGRAM_WEBHOOK_SECRET: str = Field(..., min_length=32)
    TELEGRAM_WEBHOOK_URL: str = Field(...)
    AGENT_GROUP_CHAT_ID: int = Field(...)
    
    # LongCat API
    LONGCAT_API_KEY: str = Field(..., min_length=20)
    LONGCAT_BASE_URL: str = Field(default="https://api.longcat.chat/v1")
    LONGCAT_MODEL: str = Field(default="gpt-4o-mini")
    LONGCAT_MAX_TOKENS: int = Field(default=500)
    LONGCAT_TIMEOUT: int = Field(default=30)
    
    # File Storage
    ATTACHMENT_STORAGE_PATH: str = Field(default="./attachments")
    MAX_FILE_SIZE_MB: int = Field(default=10)
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = Field(default=60)
    RATE_LIMIT_PER_DAY: int = Field(default=500)
    
    # LLM Quotas
    LLM_SESSION_LIMIT: int = Field(default=10)
    LLM_DAILY_LIMIT: int = Field(default=50)
    LLM_DAILY_BUDGET_USD: float = Field(default=100.0)
    
    # Security
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])
    ALLOWED_HOSTS: list[str] = Field(default=["*"])
    
    @validator("TELEGRAM_BOT_TOKEN")
    def validate_telegram_token(cls, v):
        """Validate Telegram bot token format"""
        if not v or len(v) < 40:
            raise ValueError("Invalid Telegram bot token")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Ensure secret key is strong"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Redact sensitive values in logs
def get_safe_config() -> dict:
    """Get configuration with secrets redacted"""
    config = settings.model_dump()
    
    sensitive_keys = [
        "SECRET_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_WEBHOOK_SECRET",
        "LONGCAT_API_KEY",
        "DATABASE_URL"
    ]
    
    for key in sensitive_keys:
        if key in config:
            config[key] = "***REDACTED***"
    
    return config

logger.info("Configuration loaded", config=get_safe_config())
```

### .env.example Template
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Application
SECRET_KEY=your-32-char-secret-key-change-this-in-production
APP_NAME="Dev2Production Bot"

# Database
DATABASE_URL=postgresql+asyncpg://botuser:botpass@localhost:5432/dev2prod_bot
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_SECRET=your-random-32-char-webhook-secret
TELEGRAM_WEBHOOK_URL=https://bot.dev2production.tech/webhook/telegram
AGENT_GROUP_CHAT_ID=-1001234567890

# LongCat API
LONGCAT_API_KEY=your-longcat-api-key-here
LONGCAT_BASE_URL=https://api.longcat.chat/v1
LONGCAT_MODEL=gpt-4o-mini
LONGCAT_MAX_TOKENS=500

# File Storage
ATTACHMENT_STORAGE_PATH=./attachments
MAX_FILE_SIZE_MB=10

# Rate Limiting
RATE_LIMIT_PER_HOUR=60
RATE_LIMIT_PER_DAY=500

# LLM Quotas
LLM_SESSION_LIMIT=10
LLM_DAILY_LIMIT=50
LLM_DAILY_BUDGET_USD=100.0

# Security
CORS_ORIGINS=["http://localhost:3000","https://dev2production.tech"]
```

### Secrets Rotation Script
```python
# scripts/rotate_secrets.py
import secrets
import string

def generate_secret_key(length: int = 32) -> str:
    """Generate cryptographically secure random key"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_webhook_secret(length: int = 32) -> str:
    """Generate webhook secret token"""
    return secrets.token_urlsafe(length)

if __name__ == "__main__":
    print("=== Generated Secrets ===")
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"TELEGRAM_WEBHOOK_SECRET={generate_webhook_secret()}")
```

---

## Tasks 42-45: Testing & Debugging Tools

### Task 42: End-to-End Testing Script
```python
# tests/e2e/test_full_workflow.py
import pytest
import asyncio
from src.services.telegram import TelegramClient
from src.core.config import settings

@pytest.mark.e2e
class TestFullWorkflow:
    """End-to-end tests for complete user journeys"""
    
    async def test_onboarding_to_project_intake(self):
        """Test: User starts bot, completes project intake"""
        # Simulate /start command
        # Verify welcome message
        # Click "Start a Project" button
        # Complete 6-step intake flow
        # Verify lead created in database
        pass
    
    async def test_faq_interaction(self):
        """Test: User asks FAQ question, gets canned response"""
        # Send FAQ query
        # Verify canned response returned
        # Verify no LLM call made
        pass
    
    async def test_llm_fallback(self):
        """Test: Unknown query triggers LLM"""
        # Send unknown query
        # Verify LLM called
        # Verify response returned
        # Verify metadata logged
        pass
    
    async def test_escalation_flow(self):
        """Test: User triggers escalation, agent responds"""
        # Request human agent
        # Verify escalation message sent to group
        # Agent claims conversation
        # Agent sends message
        # Verify message reaches user
        pass
```

### Task 43: Load Testing
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class BotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def send_message(self):
        """Simulate webhook message"""
        payload = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {"id": 987654, "username": "testuser"},
                "chat": {"id": 987654},
                "text": "What services do you offer?"
            }
        }
        self.client.post(
            "/webhook/telegram",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
        )
    
    @task(1)
    def health_check(self):
        """Check system health"""
        self.client.get("/health")
```

### Task 44: Data Export Endpoints
```python
# api/data_export.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import io
import csv

router = APIRouter()

@router.get("/export/conversation/{conversation_id}")
async def export_conversation(conversation_id: str):
    """Export conversation as JSON"""
    # Get conversation and messages
    # Return as downloadable JSON
    pass

@router.delete("/conversations/{conversation_id}/gdpr")
async def delete_user_data(conversation_id: str):
    """GDPR-compliant data deletion"""
    # Delete conversation, messages, attachments, lead data
    # Log deletion for audit
    pass
```

### Task 45: Message Replay Tool
```python
# scripts/replay_conversation.py
async def replay_conversation(conversation_id: str):
    """Replay conversation for debugging"""
    messages = await get_conversation_messages(conversation_id)
    
    for msg in messages:
        print(f"\n[{msg.sender_type}] {msg.created_at}")
        print(f"Content: {msg.content}")
        
        if msg.llm_used:
            print(f"LLM: {msg.llm_model} ({msg.llm_tokens_used} tokens, {msg.llm_confidence:.2f} confidence)")
```

---

## Implementation Checklist for Phase 5

- [ ] Write unit tests for all core services (target: 80%+ coverage)
- [ ] Implement security validation and sanitization
- [ ] Set up secrets management with Pydantic Settings
- [ ] Create E2E test suite for major workflows
- [ ] Set up load testing with Locust
- [ ] Implement GDPR data export/deletion endpoints
- [ ] Build message replay debugging tool
- [ ] Run security audit (OWASP checklist)
- [ ] Perform penetration testing
- [ ] Document security best practices

**Next Steps:** Move to Phase 6 - Deployment, Monitoring & Documentation
