# Phase 2 — Core Telegram Bot Features

## Task 17: Register Telegram Bot & Set Webhook

### Bot Registration Steps

1. **Create Bot with BotFather**
```
1. Open Telegram and search for @BotFather
2. Send /newbot
3. Choose bot name: "Dev2Production Assistant"
4. Choose username: dev2production_bot (or similar)
5. Save the API token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

2. **Configure Bot Settings**
```
/setdescription - "Professional software development assistant for dev2production.tech. Get project estimates, DevOps consultation, and connect with our team."

/setabouttext - "We build production-ready software: Custom apps, DevOps automation, Cloud engineering, System integration. 100+ projects delivered with 98% satisfaction."

/setcommands
start - Begin conversation
help - Show available commands
services - View our services
pricing - Get pricing information
contact - Talk to a human agent
cancel - Cancel current operation
```

3. **Set Webhook URL**
```python
# Script: scripts/set_webhook.py
import httpx
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://bot.dev2production.tech/webhook/telegram
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")  # Generate random 32-char string

async def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {
        "url": WEBHOOK_URL,
        "secret_token": WEBHOOK_SECRET,
        "allowed_updates": ["message", "callback_query", "inline_query"],
        "drop_pending_updates": True,
        "max_connections": 40
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        print(response.json())

if __name__ == "__main__":
    import asyncio
    asyncio.run(set_webhook())
```

4. **Verify Webhook**
```python
# Check webhook info
import httpx

async def get_webhook_info():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(response.json())
```

### Environment Variables (.env.example)
```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_SECRET=your-random-32-char-secret
WEBHOOK_URL=https://bot.dev2production.tech/webhook/telegram

# Database
DATABASE_URL=postgresql+asyncpg://botuser:botpass@localhost:5432/dev2prod_bot

# Redis
REDIS_URL=redis://localhost:6379/0

# LongCat API
LONGCAT_API_KEY=your-longcat-api-key
LONGCAT_BASE_URL=https://api.longcat.chat/v1

# App Config
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=your-fastapi-secret-key
```

---

## Task 18: Onboarding Flow (/start)

### Implementation: api/webhooks.py
```python
from fastapi import APIRouter, Request, Header, HTTPException, status
from src.services.conversation_manager import ConversationManager
from src.services.telegram import TelegramClient
from src.core.config import settings
from src.schemas.telegram import Update
import structlog

router = APIRouter()
logger = structlog.get_logger()

telegram = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
conversation_manager = ConversationManager()

@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """Handle incoming Telegram updates"""
    
    # Validate secret token
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    # Parse update
    data = await request.json()
    update = Update(**data)
    
    # Route to appropriate handler
    if update.message:
        await handle_message(update.message)
    elif update.callback_query:
        await handle_callback_query(update.callback_query)
    
    return {"ok": True}

async def handle_message(message):
    """Process incoming message"""
    user_id = message.from_user.id
    text = message.text or ""
    
    # Get or create conversation
    conversation = await conversation_manager.get_or_create(
        telegram_user_id=user_id,
        telegram_username=message.from_user.username
    )
    
    # Handle commands
    if text.startswith("/start"):
        await handle_start_command(message, conversation)
    elif text.startswith("/help"):
        await handle_help_command(message)
    elif text.startswith("/services"):
        await handle_services_command(message)
    elif text.startswith("/pricing"):
        await handle_pricing_command(message)
    elif text.startswith("/contact"):
        await handle_contact_command(message, conversation)
    else:
        # Regular message - process with intent detection
        await handle_regular_message(message, conversation)
```

### Onboarding Flow Handler
```python
async def handle_start_command(message, conversation):
    """Handle /start command with welcome message"""
    
    welcome_text = (
        "👋 Hi! I'm DevBot from Dev2Production.\n\n"
        "We build production-ready software that actually works:\n"
        "• Custom applications tailored to your needs\n"
        "• DevOps automation & CI/CD pipelines\n"
        "• Cloud engineering & infrastructure\n"
        "• System integration\n\n"
        "We've delivered 100+ projects with 98% client satisfaction.\n\n"
        "How can I help you today?"
    )
    
    # Quick reply keyboard
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚀 Start a Project", "callback_data": "action:start_project"},
                {"text": "💬 Ask Questions", "callback_data": "action:ask_questions"}
            ],
            [
                {"text": "📚 Learn About Services", "callback_data": "action:services"},
                {"text": "👤 Talk to Human", "callback_data": "action:escalate"}
            ]
        ]
    }
    
    await telegram.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        reply_markup=keyboard
    )
    
    # Log interaction
    await conversation_manager.add_message(
        conversation_id=conversation.id,
        sender_type="bot",
        content=welcome_text,
        content_type="text",
        intent="onboarding"
    )
```

### Callback Query Handler
```python
async def handle_callback_query(callback_query):
    """Handle button clicks from inline keyboards"""
    
    action = callback_query.data  # e.g., "action:start_project"
    user_id = callback_query.from_user.id
    
    conversation = await conversation_manager.get_by_telegram_user_id(user_id)
    
    if action == "action:start_project":
        await start_project_intake(callback_query, conversation)
    elif action == "action:ask_questions":
        await prompt_for_question(callback_query)
    elif action == "action:services":
        await show_services_menu(callback_query)
    elif action == "action:escalate":
        await initiate_escalation(callback_query, conversation)
    
    # Acknowledge callback
    await telegram.answer_callback_query(callback_query.id)
```

---

## Task 19: FAQ Routing with Canned Responses

### Implementation: services/intent_detector.py
```python
import re
from typing import Optional, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class Intent:
    name: str
    confidence: float
    canned_response: Optional[str] = None

class IntentDetector:
    """Detect user intent and match to canned responses"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.canned_responses = self._load_canned_responses()
    
    def _load_intent_patterns(self) -> dict:
        """Load regex patterns for intent matching"""
        return {
            # General Service Inquiries
            "faq_services": [
                r"what (do you|services|can you).*offer",
                r"what (do you|can you).*do",
                r"tell me about.*services",
                r"list.*services"
            ],
            "faq_company_info": [
                r"(tell me|info|information).*about.*company",
                r"who are you",
                r"what('s| is) (your )?company"
            ],
            "faq_experience": [
                r"how (much|many).*experience",
                r"how long.*business",
                r"years.*experience"
            ],
            
            # DevOps & Cloud
            "faq_devops_intro": [
                r"what is devops",
                r"explain devops",
                r"devops meaning"
            ],
            "faq_cicd_intro": [
                r"what is (ci/?cd|continuous)",
                r"explain (ci/?cd|pipeline)",
                r"cicd meaning"
            ],
            "faq_cloud_services": [
                r"cloud (migration|services|engineering)",
                r"(aws|azure|gcp|google cloud)",
                r"help.*cloud"
            ],
            
            # Pricing
            "faq_pricing_general": [
                r"how much.*cost",
                r"pricing",
                r"(what('s| is) )?your rate",
                r"how much.*charge"
            ],
            "faq_pricing_hourly": [
                r"hourly rate",
                r"cost per hour",
                r"hour.*rate"
            ],
            
            # Process
            "faq_timeline": [
                r"how long.*take",
                r"timeline",
                r"project duration",
                r"delivery time"
            ],
            "faq_process": [
                r"(development|work|project) process",
                r"how do you work",
                r"methodology"
            ],
            
            # Support
            "faq_support": [
                r"(ongoing|post.?launch) support",
                r"maintenance",
                r"after.*delivery"
            ],
            
            # Intent to escalate
            "intent_escalate": [
                r"(talk|speak|chat).*human",
                r"(talk|speak).*agent",
                r"connect.*team",
                r"representative"
            ],
            
            # Intent to start project
            "intent_start_project": [
                r"(start|begin|initiate).*project",
                r"want to (build|create|develop)",
                r"need (help|assistance).*project",
                r"get (started|quote|estimate)"
            ]
        }
    
    def _load_canned_responses(self) -> dict:
        """Load pre-written responses for common intents"""
        return {
            "faq_services": (
                "We specialize in production-ready software development:\n\n"
                "• **Custom Software Development** - Tailored applications built to your exact specifications\n"
                "• **DevOps Automation** - CI/CD pipelines & deployment streamlining\n"
                "• **Cloud Engineering** - Infrastructure & optimization (AWS, Azure, GCP)\n"
                "• **System Integration** - Connect & automate your existing tools\n\n"
                "We've delivered 100+ projects with 98% client satisfaction.\n\n"
                "What area are you most interested in?"
            ),
            
            "faq_company_info": (
                "Dev2Production is a professional software development firm that builds production-ready applications.\n\n"
                "🎯 **Our Mission:** Ship quality products faster than ever\n"
                "📊 **Track Record:**\n"
                "  • 100+ projects delivered\n"
                "  • 50+ happy clients worldwide\n"
                "  • 98% client satisfaction rating\n"
                "  • 24/7 support available\n\n"
                "We're remote-first with global reach. What brings you here today?"
            ),
            
            "faq_cicd_intro": (
                "A **CI/CD pipeline** automates your software delivery:\n\n"
                "🔄 **Code → Build → Test → Deploy**\n\n"
                "**Benefits:**\n"
                "✅ Deploy faster (multiple times/day vs. weekly)\n"
                "✅ Fewer bugs (automated testing catches issues early)\n"
                "✅ Less manual work (automation handles repetitive tasks)\n"
                "✅ Better reliability (consistent, repeatable deployments)\n\n"
                "We've built pipelines that reduced deployment time by 70% for clients.\n\n"
                "Interested in exploring this for your project?"
            ),
            
            "faq_pricing_general": (
                "Project costs vary based on scope and complexity. Here are typical ranges:\n\n"
                "💰 **Typical Project Ranges:**\n"
                "• CI/CD Pipeline Setup: $5K-$40K\n"
                "• Custom Web Application: $20K-$150K\n"
                "• Cloud Migration: $15K-$80K\n"
                "• System Integration: $10K-$60K\n\n"
                "We offer free technical consultations for accurate estimates.\n\n"
                "To give you a ballpark, I need:\n"
                "1. Project type (DevOps, custom app, integration, etc.)\n"
                "2. Rough timeline\n"
                "3. Any specific requirements\n\n"
                "What kind of project are you planning?"
            ),
            
            "faq_process": (
                "Our process ensures predictable results:\n\n"
                "**1️⃣ Understand** - Deep dive into your business needs & technical environment\n"
                "**2️⃣ Design** - Technical blueprints + user prototypes\n"
                "**3️⃣ Build** - Focused sprints with regular demos\n"
                "**4️⃣ Deploy** - Launch, monitoring, training & ongoing support\n\n"
                "You'll see progress continuously and provide feedback that shapes the final product.\n\n"
                "Projects typically range from 6 weeks to 6 months depending on complexity.\n\n"
                "What kind of timeline are you working with?"
            ),
            
            "faq_support": (
                "Yes! We offer comprehensive post-launch support:\n\n"
                "🛠 **Support Options:**\n"
                "• 24/7 monitoring and issue response\n"
                "• Ongoing optimization and updates\n"
                "• Bug fixes and security patches\n"
                "• Performance tuning\n"
                "• Feature enhancements\n\n"
                "**Pricing Models:**\n"
                "• Retainer agreements (monthly hours)\n"
                "• On-demand (hourly billing)\n"
                "• Dedicated team extension\n\n"
                "Most clients start with a 3-month post-launch support package.\n\n"
                "Want to discuss your specific support needs?"
            )
        }
    
    def detect_intent(self, text: str) -> Intent:
        """
        Detect intent from user message
        Returns Intent object with confidence score
        """
        text_lower = text.lower().strip()
        
        # Check each intent pattern
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    confidence = 0.9  # High confidence for regex match
                    canned_response = self.canned_responses.get(intent_name)
                    
                    logger.info(
                        "Intent detected",
                        intent=intent_name,
                        confidence=confidence,
                        has_canned_response=bool(canned_response)
                    )
                    
                    return Intent(
                        name=intent_name,
                        confidence=confidence,
                        canned_response=canned_response
                    )
        
        # No intent matched
        logger.info("No intent matched", text=text[:50])
        return Intent(name="unknown", confidence=0.0)
    
    def should_use_llm(self, intent: Intent) -> bool:
        """Determine if LLM should be used based on intent confidence"""
        # Use LLM if no canned response or low confidence
        return intent.confidence < 0.7 or not intent.canned_response
```

### FAQ Handler
```python
async def handle_regular_message(message, conversation):
    """Process regular user message with intent detection"""
    
    text = message.text
    user_id = message.from_user.id
    
    # Check rate limiting
    await RateLimiter.check_rate_limit(user_id)
    
    # Detect intent
    intent_detector = IntentDetector()
    intent = intent_detector.detect_intent(text)
    
    # Save user message
    await conversation_manager.add_message(
        conversation_id=conversation.id,
        sender_type="user",
        content=text,
        telegram_message_id=message.message_id,
        intent=intent.name
    )
    
    # Route based on intent
    if intent.canned_response:
        # Use canned response
        await telegram.send_message(
            chat_id=message.chat.id,
            text=intent.canned_response,
            parse_mode="Markdown"
        )
        
        await conversation_manager.add_message(
            conversation_id=conversation.id,
            sender_type="bot",
            content=intent.canned_response,
            intent=intent.name
        )
    
    elif intent.name == "intent_escalate":
        # User wants to talk to human
        await initiate_escalation(message, conversation)
    
    elif intent.name == "intent_start_project":
        # Start project intake flow
        await start_project_intake(message, conversation)
    
    else:
        # Use LLM for nuanced response
        await process_with_llm(message, conversation)
```

---

## Task 20: Project Intake Flow

### Implementation: services/project_intake.py
```python
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from src.utils.cache import cache
import structlog

logger = structlog.get_logger()

class IntakeStep(Enum):
    PROJECT_TYPE = 1
    DESCRIPTION = 2
    TIMELINE = 3
    BUDGET = 4
    CONTACT_INFO = 5
    COMPLETED = 6

@dataclass
class ProjectIntakeState:
    step: IntakeStep
    project_type: Optional[str] = None
    description: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None

class ProjectIntakeFlow:
    """Multi-step project intake conversation flow"""
    
    async def start_intake(self, user_id: int, conversation_id: str):
        """Initialize project intake flow"""
        state = ProjectIntakeState(step=IntakeStep.PROJECT_TYPE)
        await self._save_state(user_id, state)
        return await self._get_step_prompt(state)
    
    async def process_intake_response(
        self,
        user_id: int,
        response: str
    ) -> Tuple[str, bool]:
        """
        Process user response for current intake step
        Returns (next_prompt, is_completed)
        """
        state = await self._load_state(user_id)
        
        if not state:
            return "Session expired. Type /start to begin again.", True
        
        # Process current step
        if state.step == IntakeStep.PROJECT_TYPE:
            state.project_type = response
            state.step = IntakeStep.DESCRIPTION
        
        elif state.step == IntakeStep.DESCRIPTION:
            state.description = response
            state.step = IntakeStep.TIMELINE
        
        elif state.step == IntakeStep.TIMELINE:
            state.timeline = response
            state.step = IntakeStep.BUDGET
        
        elif state.step == IntakeStep.BUDGET:
            state.budget = response
            state.step = IntakeStep.CONTACT_INFO
        
        elif state.step == IntakeStep.CONTACT_INFO:
            # Parse contact info (name, email, company)
            await self._parse_contact_info(state, response)
            state.step = IntakeStep.COMPLETED
        
        # Save updated state
        await self._save_state(user_id, state)
        
        # Get next prompt or completion message
        if state.step == IntakeStep.COMPLETED:
            return await self._complete_intake(state), True
        else:
            return await self._get_step_prompt(state), False
    
    async def _get_step_prompt(self, state: ProjectIntakeState) -> dict:
        """Get prompt and keyboard for current step"""
        
        if state.step == IntakeStep.PROJECT_TYPE:
            return {
                "text": (
                    "🚀 Great! Let's get started.\n\n"
                    "**What type of project are you planning?**"
                ),
                "keyboard": {
                    "inline_keyboard": [
                        [
                            {"text": "DevOps/CI-CD", "callback_data": "intake:devops"},
                            {"text": "Custom App", "callback_data": "intake:custom_app"}
                        ],
                        [
                            {"text": "Cloud Engineering", "callback_data": "intake:cloud"},
                            {"text": "System Integration", "callback_data": "intake:integration"}
                        ],
                        [
                            {"text": "Not Sure", "callback_data": "intake:other"}
                        ]
                    ]
                }
            }
        
        elif state.step == IntakeStep.DESCRIPTION:
            return {
                "text": (
                    f"✅ Got it - **{state.project_type}**\n\n"
                    "Could you briefly describe what you're trying to build or achieve?\n\n"
                    "_2-3 sentences is fine_"
                ),
                "keyboard": None
            }
        
        elif state.step == IntakeStep.TIMELINE:
            return {
                "text": (
                    "📅 **What's your ideal timeline?**"
                ),
                "keyboard": {
                    "inline_keyboard": [
                        [
                            {"text": "Urgent (<1 month)", "callback_data": "intake:urgent"},
                            {"text": "Normal (1-3 months)", "callback_data": "intake:normal"}
                        ],
                        [
                            {"text": "Flexible (3+ months)", "callback_data": "intake:flexible"},
                            {"text": "Just Exploring", "callback_data": "intake:exploring"}
                        ]
                    ]
                }
            }
        
        elif state.step == IntakeStep.BUDGET:
            return {
                "text": (
                    "💰 **To provide the best recommendations, what's your approximate budget?**\n\n"
                    "_This helps us suggest the right approach and scope_"
                ),
                "keyboard": {
                    "inline_keyboard": [
                        [
                            {"text": "< $10K", "callback_data": "intake:<10k"},
                            {"text": "$10K-$50K", "callback_data": "intake:10k-50k"}
                        ],
                        [
                            {"text": "$50K-$150K", "callback_data": "intake:50k-150k"},
                            {"text": "$150K+", "callback_data": "intake:150k+"}
                        ],
                        [
                            {"text": "Not Sure Yet", "callback_data": "intake:unknown"}
                        ]
                    ]
                }
            }
        
        elif state.step == IntakeStep.CONTACT_INFO:
            return {
                "text": (
                    "📧 **Perfect! To send you a detailed proposal, I'll need:**\n\n"
                    "• Your name\n"
                    "• Email address\n"
                    "• Company name (optional)\n\n"
                    "_Please send in this format:_\n"
                    "`John Doe, john@example.com, Acme Corp`"
                ),
                "keyboard": None
            }
    
    async def _parse_contact_info(self, state: ProjectIntakeState, text: str):
        """Parse contact information from user message"""
        parts = [p.strip() for p in text.split(",")]
        
        if len(parts) >= 2:
            state.name = parts[0]
            state.email = parts[1]
            state.company = parts[2] if len(parts) > 2 else None
        else:
            # Fallback: just use the text as name
            state.name = text
    
    async def _complete_intake(self, state: ProjectIntakeState) -> str:
        """Complete intake and create lead record"""
        
        # Calculate lead score
        lead_score = self._calculate_lead_score(state)
        
        # Create lead record (would call lead_manager here)
        logger.info(
            "Project intake completed",
            lead_score=lead_score,
            project_type=state.project_type,
            budget=state.budget
        )
        
        # Return completion message
        return (
            f"✅ **Thanks, {state.name}!**\n\n"
            "I've passed your details to our team. You'll hear back within **4 business hours**.\n\n"
            "**Your Project Summary:**\n"
            f"• Type: {state.project_type}\n"
            f"• Timeline: {state.timeline}\n"
            f"• Budget: {state.budget}\n\n"
            "**In the meantime:**\n"
            "• [Check out our case studies](https://dev2production.tech/#/)\n"
            "• [Read our DevOps guide](https://dev2production.tech/#/articles)\n"
            "• [Follow us on GitHub](https://github.com/dev2productiontech)\n\n"
            "Feel free to ask any other questions!"
        )
    
    def _calculate_lead_score(self, state: ProjectIntakeState) -> str:
        """Calculate lead score based on intake data"""
        score = 0
        
        # Budget scoring
        if state.budget in ["150k+", "50k-150k"]:
            score += 3
        elif state.budget == "10k-50k":
            score += 2
        
        # Timeline scoring
        if state.timeline == "urgent":
            score += 2
        elif state.timeline == "normal":
            score += 1
        
        # Has contact info
        if state.email:
            score += 1
        
        # Determine lead score
        if score >= 5:
            return "hot"
        elif score >= 3:
            return "warm"
        else:
            return "cold"
    
    async def _save_state(self, user_id: int, state: ProjectIntakeState):
        """Save intake state to Redis"""
        key = f"intake:{user_id}"
        await cache.set(key, state.__dict__, ttl=3600)  # 1 hour TTL
    
    async def _load_state(self, user_id: int) -> Optional[ProjectIntakeState]:
        """Load intake state from Redis"""
        key = f"intake:{user_id}"
        data = await cache.get(key)
        if data:
            import json
            data_dict = json.loads(data)
            data_dict['step'] = IntakeStep(data_dict['step'])
            return ProjectIntakeState(**data_dict)
        return None
```

---

## Task 21: File Upload Handling

### Implementation: services/file_handler.py
```python
import httpx
import os
from pathlib import Path
from typing import Optional
import structlog
from src.core.config import settings
from src.db.models.attachment import Attachment

logger = structlog.get_logger()

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/gif",
    "text/plain"
]

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class FileHandler:
    """Handle file uploads from Telegram"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.storage_path = Path(settings.ATTACHMENT_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def handle_file_upload(
        self,
        file_id: str,
        conversation_id: str,
        message_id: str,
        filename: Optional[str] = None
    ) -> dict:
        """
        Download and store file from Telegram
        Returns status dict with success/error info
        """
        
        # Get file info
        file_info = await self._get_file_info(file_id)
        
        if not file_info:
            return {"success": False, "error": "Could not retrieve file info"}
        
        file_size = file_info.get("file_size", 0)
        file_path = file_info.get("file_path")
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large ({file_size/1024/1024:.1f}MB). Maximum: 10MB"
            }
        
        # Download file
        file_content = await self._download_file(file_path)
        
        if not file_content:
            return {"success": False, "error": "Could not download file"}
        
        # Determine storage path
        storage_dir = self.storage_path / conversation_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        local_filename = filename or file_path.split("/")[-1]
        local_path = storage_dir / local_filename
        
        # Save file
        with open(local_path, "wb") as f:
            f.write(file_content)
        
        logger.info(
            "File uploaded successfully",
            conversation_id=conversation_id,
            filename=local_filename,
            size_bytes=file_size
        )
        
        # Create attachment record (would save to DB here)
        attachment_data = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "telegram_file_id": file_id,
            "filename": local_filename,
            "file_size_bytes": file_size,
            "storage_path": str(local_path)
        }
        
        return {
            "success": True,
            "filename": local_filename,
            "size_bytes": file_size,
            "attachment": attachment_data
        }
    
    async def _get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file metadata from Telegram"""
        url = f"{self.base_url}/getFile"
        params = {"file_id": file_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("ok"):
                return data.get("result")
            return None
    
    async def _download_file(self, file_path: str) -> Optional[bytes]:
        """Download file from Telegram servers"""
        url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                return response.content
            return None
```

### Webhook Handler for Files
```python
async def handle_message(message):
    """Process incoming message (including files)"""
    user_id = message.from_user.id
    
    # Check if message contains a document/photo
    if message.document:
        await handle_document_upload(message)
    elif message.photo:
        await handle_photo_upload(message)
    elif message.text:
        # Regular text message
        await handle_text_message(message)

async def handle_document_upload(message):
    """Handle document uploads"""
    document = message.document
    user_id = message.from_user.id
    
    conversation = await conversation_manager.get_by_telegram_user_id(user_id)
    
    # Process file upload
    file_handler = FileHandler(settings.TELEGRAM_BOT_TOKEN)
    result = await file_handler.handle_file_upload(
        file_id=document.file_id,
        conversation_id=str(conversation.id),
        message_id=str(message.message_id),
        filename=document.file_name
    )
    
    if result["success"]:
        await telegram.send_message(
            chat_id=message.chat.id,
            text=(
                f"✅ Got your file: **{result['filename']}**\n\n"
                "I've attached it to your conversation. "
                "Our team will review it when they respond."
            ),
            parse_mode="Markdown"
        )
    else:
        await telegram.send_message(
            chat_id=message.chat.id,
            text=f"⚠️ {result['error']}"
        )
```

---

## Tasks 22-24: Remaining Features

### Task 22: Human Escalation (services/escalation.py)
- Detect escalation triggers (user request, low LLM confidence, frustration)
- Check agent availability in Telegram group
- Route conversation to available agent
- Maintain conversation context during handoff

### Task 23: Intent Detection Enhancement
- Add lightweight NLP with spaCy or transformers
- Implement entity extraction (budget amounts, dates, tech stack)
- Build confidence scoring system
- Create fallback handling for ambiguous queries

### Task 24: Rate Limiting & Anti-Spam
- Implement per-user message limits (60/hour, 500/day)
- Add CAPTCHA challenge for suspicious behavior
- Block users after repeated violations
- Whitelist known good users (completed project intake)

---

## Implementation Checklist for Phase 2

- [ ] Register Telegram bot with BotFather
- [ ] Set webhook URL and secret token
- [ ] Implement onboarding flow with quick reply buttons
- [ ] Build FAQ intent detector with regex patterns
- [ ] Create canned response library (40 responses)
- [ ] Implement project intake state machine
- [ ] Build file upload handler with validation
- [ ] Create human escalation logic
- [ ] Add rate limiting middleware
- [ ] Write integration tests for all flows
- [ ] Test end-to-end user journeys

**Next Steps:** Move to Phase 3 - LongCat.chat LLM Integration
