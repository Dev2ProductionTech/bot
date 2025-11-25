# Phase 3 — LongCat.chat LLM Integration

## Task 25: Build LongCat API Client Wrapper

### LongCat.chat API Overview
LongCat.chat is an LLM aggregator platform that provides access to multiple AI models through a unified API interface.

**Key Features:**
- Access to GPT-4, Claude, Llama, and other models
- Usage-based pricing with token tracking
- API key authentication
- Streaming and non-streaming responses
- Conversation context management

### Implementation: services/llm_adapter.py

```python
import httpx
from typing import List, Dict, Optional, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = structlog.get_logger()

@dataclass
class LLMResponse:
    """Standardized LLM response format"""
    content: str
    model: str
    tokens_used: int
    latency_ms: int
    confidence: float
    finish_reason: str

@dataclass
class LLMMessage:
    """Message format for conversation history"""
    role: str  # 'system', 'user', 'assistant'
    content: str

class AIAdapter(ABC):
    """Abstract base class for AI adapters"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Generate response from AI model"""
        pass
    
    @abstractmethod
    async def check_confidence(self, response: str) -> float:
        """Calculate confidence score for response"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        pass

class LongCatAdapter(AIAdapter):
    """LongCat.chat API client adapter"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.longcat.chat/v1",
        model: str = "gpt-4o-mini",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=timeout
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> LLMResponse:
        """
        Generate response from LongCat API
        Includes automatic retries with exponential backoff
        """
        import time
        start_time = time.time()
        
        # Convert messages to API format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            choice = data["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "unknown")
            
            tokens_used = data["usage"]["total_tokens"]
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Calculate confidence (heuristic based on finish_reason and length)
            confidence = await self.check_confidence(content, finish_reason)
            
            logger.info(
                "LLM response generated",
                model=self.model,
                tokens=tokens_used,
                latency_ms=latency_ms,
                confidence=confidence
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                confidence=confidence,
                finish_reason=finish_reason
            )
        
        except httpx.HTTPStatusError as e:
            logger.error(
                "LLM API error",
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        
        except Exception as e:
            logger.error("LLM generation failed", error=str(e), exc_info=True)
            raise
    
    async def check_confidence(
        self,
        response: str,
        finish_reason: str = "stop"
    ) -> float:
        """
        Calculate confidence score for response
        
        Factors:
        - Finish reason (stop = confident, length = cut off)
        - Response length (very short = uncertain)
        - Presence of uncertainty phrases
        - Presence of questions back to user
        """
        confidence = 0.9  # Base confidence
        
        # Penalize non-stop finish reasons
        if finish_reason != "stop":
            confidence -= 0.3
        
        # Penalize very short responses
        if len(response) < 50:
            confidence -= 0.2
        
        # Check for uncertainty phrases
        uncertainty_phrases = [
            "i'm not sure",
            "i don't know",
            "might be",
            "possibly",
            "perhaps",
            "i think",
            "unclear",
            "not certain",
            "could you clarify",
            "can you provide more"
        ]
        
        response_lower = response.lower()
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases
            if phrase in response_lower
        )
        
        confidence -= min(uncertainty_count * 0.1, 0.3)
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Rough approximation: 1 token ≈ 4 characters
        """
        return len(text) // 4
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

class MockLLMAdapter(AIAdapter):
    """Mock adapter for testing without API calls"""
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Return mock response"""
        return LLMResponse(
            content="This is a mock LLM response for testing purposes.",
            model="mock-model",
            tokens_used=20,
            latency_ms=100,
            confidence=0.85,
            finish_reason="stop"
        )
    
    async def check_confidence(self, response: str) -> float:
        return 0.85
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
```

---

## Task 26: System Prompt Templates

### Implementation: services/prompt_templates.py

```python
from typing import Dict
from string import Template

class PromptTemplateManager:
    """Manage system prompts for different bot contexts"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Template]:
        """Load prompt templates"""
        return {
            "base": Template("""You are DevBot, an AI assistant for Dev2Production (dev2production.tech), a professional software development firm.

**Company Profile:**
- We build production-ready applications (not prototypes)
- Services: Custom software, DevOps automation, Cloud engineering, System integration
- Track record: 100+ projects, 50+ clients, 98% satisfaction, 24/7 support
- Remote-first, global reach

**Your Role:**
- Provide helpful, accurate information about our services
- Qualify leads and collect project requirements
- Guide users through our offerings
- Escalate to human agents when appropriate

**Tone:**
- Professional yet approachable
- Solution-oriented and business-focused
- Clear and concise (no jargon overload)
- Confident but humble

**Key Guidelines:**
1. Lead with business value, then technical details
2. Provide specific examples and case studies when relevant
3. Ask clarifying questions to better understand needs
4. Be transparent about capabilities and limitations
5. Offer to connect with human experts for complex queries

**Current Context:**
User's previous messages: $conversation_history

**Your Task:**
Respond to the user's latest message in a helpful, professional manner. If you're uncertain or the query is complex, offer to connect them with a human expert."""),

            "project_consultation": Template("""You are DevBot, providing technical consultation for a potential project.

**Consultation Mode Activated**

The user is exploring a project. Your goals:
1. Understand their technical needs and constraints
2. Recommend appropriate solutions and approaches
3. Provide realistic timelines and complexity estimates
4. Identify potential challenges or considerations

**Available Services:**
- DevOps: CI/CD pipelines, deployment automation, infrastructure as code
- Cloud: AWS/Azure/GCP architecture, migration, optimization
- Custom Development: Web apps, APIs, microservices, integrations
- System Integration: Connect existing tools, automate workflows

**Project Context So Far:**
$project_context

**Instructions:**
- Ask targeted questions to clarify requirements
- Provide 2-3 potential approaches with pros/cons
- Give ballpark estimates when possible (timeline, complexity, budget range)
- Recommend next steps (detailed proposal, technical discovery, etc.)

Respond to the user's question with actionable technical guidance."""),

            "lead_qualification": Template("""You are DevBot in lead qualification mode.

**Goal:** Determine if this is a qualified lead and collect essential information.

**Information to Collect:**
- Project type and scope
- Timeline and urgency
- Budget range
- Technical requirements
- Decision-making authority

**Lead Scoring Criteria:**
- Hot: Budget >$50K, timeline <3 months, decision-maker present
- Warm: Budget $10K-$50K, normal timeline, evaluating options
- Cold: Budget unclear, exploring, no immediate need

**Current Lead Data:**
$lead_data

**Instructions:**
- Ask relevant qualifying questions naturally
- Don't make it feel like an interrogation
- Provide value in every response (education, insights, examples)
- Once qualified, transition to project intake or human handoff

Continue the conversation to gather missing qualification information."""),

            "technical_support": Template("""You are DevBot providing technical support and education.

**Support Mode Activated**

The user has a technical question about:
$topic

**Your Expertise Areas:**
- DevOps practices (CI/CD, containerization, orchestration)
- Cloud architecture (AWS, Azure, GCP)
- Software development best practices
- System integration patterns
- Performance optimization

**Instructions:**
1. Provide clear, actionable explanations
2. Use analogies and examples for complex concepts
3. Offer resources (blog posts, case studies, documentation)
4. Suggest how Dev2Production can help implement the solution
5. If beyond your knowledge, admit it and offer human expert consultation

**Context:**
$conversation_history

Provide a helpful, educational response to the user's technical question."""),

            "escalation_prep": Template("""You are DevBot preparing to escalate this conversation to a human agent.

**Escalation Triggered Because:**
$escalation_reason

**Conversation Summary:**
$conversation_summary

**Your Task:**
1. Acknowledge the need for human expertise
2. Set proper expectations (response time, next steps)
3. Ensure we have contact information
4. Provide a smooth handoff experience

**Response Template:**
- Thank user for their patience
- Explain why human agent is better suited
- Confirm contact details or offer to collect
- Provide estimated response time (within 4 business hours)
- Offer interim resources or information

Prepare a professional escalation message.""")
        }
    
    def get_system_prompt(
        self,
        template_name: str = "base",
        **kwargs
    ) -> str:
        """
        Get formatted system prompt
        
        Args:
            template_name: Name of template to use
            **kwargs: Variables to substitute in template
        """
        template = self.templates.get(template_name, self.templates["base"])
        
        # Provide defaults for missing variables
        defaults = {
            "conversation_history": "No previous conversation",
            "project_context": "No project context yet",
            "lead_data": "No lead data collected",
            "topic": "General inquiry",
            "escalation_reason": "User request",
            "conversation_summary": "No summary available"
        }
        
        # Merge kwargs with defaults
        variables = {**defaults, **kwargs}
        
        return template.safe_substitute(**variables)
```

---

## Task 27: Conversation History Trimming & Token Counting

### Implementation: services/conversation_context.py

```python
from typing import List
from src.services.llm_adapter import LLMMessage
from src.db.models.message import Message
import structlog

logger = structlog.get_logger()

class ConversationContextManager:
    """Manage conversation history for LLM context"""
    
    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens
    
    def build_context(
        self,
        messages: List[Message],
        system_prompt: str,
        adapter
    ) -> List[LLMMessage]:
        """
        Build conversation context for LLM
        
        Args:
            messages: Database message records
            system_prompt: System prompt to use
            adapter: LLM adapter (for token estimation)
        
        Returns:
            List of LLMMessage objects trimmed to fit token budget
        """
        # Start with system prompt
        context = [LLMMessage(role="system", content=system_prompt)]
        system_tokens = adapter.estimate_tokens(system_prompt)
        
        remaining_tokens = self.max_tokens - system_tokens - 500  # Reserve 500 for response
        
        # Convert messages to LLM format (most recent first for trimming)
        llm_messages = []
        for msg in reversed(messages):
            role = self._map_sender_to_role(msg.sender_type)
            content = msg.content
            
            msg_tokens = adapter.estimate_tokens(content)
            
            if remaining_tokens - msg_tokens > 0:
                llm_messages.insert(0, LLMMessage(role=role, content=content))
                remaining_tokens -= msg_tokens
            else:
                # Token budget exhausted
                logger.info(
                    "Conversation history trimmed",
                    included_messages=len(llm_messages),
                    total_messages=len(messages)
                )
                break
        
        # Combine system prompt with conversation history
        context.extend(llm_messages)
        
        return context
    
    def _map_sender_to_role(self, sender_type: str) -> str:
        """Map database sender_type to LLM role"""
        mapping = {
            "user": "user",
            "bot": "assistant",
            "agent": "assistant"
        }
        return mapping.get(sender_type, "user")
    
    def summarize_for_handoff(self, messages: List[Message]) -> str:
        """
        Create a summary of conversation for human agent handoff
        
        Returns concise summary of key points discussed
        """
        if not messages:
            return "No conversation history"
        
        # Extract key information
        user_messages = [m for m in messages if m.sender_type == "user"]
        bot_messages = [m for m in messages if m.sender_type == "bot"]
        
        # Identify intents discussed
        intents = list(set(m.intent for m in messages if m.intent))
        
        summary_parts = [
            f"**Conversation Summary** ({len(messages)} messages)\n",
            f"\n**User Messages:** {len(user_messages)}",
            f"\n**Bot Responses:** {len(bot_messages)}",
        ]
        
        if intents:
            summary_parts.append(f"\n**Topics Discussed:** {', '.join(intents)}")
        
        # Include last 2 user messages for context
        if user_messages:
            summary_parts.append("\n\n**Recent User Messages:**")
            for msg in user_messages[-2:]:
                summary_parts.append(f"\n- {msg.content[:100]}...")
        
        return "".join(summary_parts)
```

---

## Task 28: Low-Confidence Detection & Escalation

### Implementation: services/confidence_checker.py

```python
from typing import Optional, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class ConfidenceCheckResult:
    should_escalate: bool
    reason: str
    confidence_score: float
    recommendation: str

class ConfidenceChecker:
    """Detect when bot should escalate to human"""
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        consecutive_low_threshold: int = 3
    ):
        self.confidence_threshold = confidence_threshold
        self.consecutive_low_threshold = consecutive_low_threshold
        
        # Track consecutive low-confidence responses per user
        self.low_confidence_counts = {}
    
    async def check_escalation_needed(
        self,
        user_id: int,
        llm_confidence: float,
        conversation_id: str,
        additional_context: Optional[dict] = None
    ) -> ConfidenceCheckResult:
        """
        Determine if conversation should be escalated
        
        Args:
            user_id: Telegram user ID
            llm_confidence: Confidence score from LLM (0-1)
            conversation_id: Current conversation ID
            additional_context: Optional context (lead score, frustration detected, etc.)
        
        Returns:
            ConfidenceCheckResult with escalation decision
        """
        additional_context = additional_context or {}
        
        # Check various escalation triggers
        
        # 1. Single very low confidence response
        if llm_confidence < 0.5:
            return ConfidenceCheckResult(
                should_escalate=True,
                reason="Very low confidence response",
                confidence_score=llm_confidence,
                recommendation="Escalate immediately - bot is uncertain"
            )
        
        # 2. Multiple consecutive low confidence
        if llm_confidence < self.confidence_threshold:
            count = self.low_confidence_counts.get(user_id, 0) + 1
            self.low_confidence_counts[user_id] = count
            
            if count >= self.consecutive_low_threshold:
                # Reset counter
                self.low_confidence_counts[user_id] = 0
                
                return ConfidenceCheckResult(
                    should_escalate=True,
                    reason=f"{count} consecutive low-confidence responses",
                    confidence_score=llm_confidence,
                    recommendation="Bot is struggling - human agent needed"
                )
        else:
            # Reset counter on high confidence
            self.low_confidence_counts[user_id] = 0
        
        # 3. High-value lead detection
        if additional_context.get("lead_score") == "hot":
            if additional_context.get("budget_range") in ["50k-150k", "150k+"]:
                return ConfidenceCheckResult(
                    should_escalate=True,
                    reason="High-value lead detected",
                    confidence_score=llm_confidence,
                    recommendation="Priority escalation - potential major project"
                )
        
        # 4. User frustration detected
        if additional_context.get("frustration_detected"):
            return ConfidenceCheckResult(
                should_escalate=True,
                reason="User frustration detected",
                confidence_score=llm_confidence,
                recommendation="Escalate to prevent negative experience"
            )
        
        # 5. Explicit user request
        if additional_context.get("user_requested_human"):
            return ConfidenceCheckResult(
                should_escalate=True,
                reason="User explicitly requested human agent",
                confidence_score=1.0,
                recommendation="Honor user request immediately"
            )
        
        # No escalation needed
        return ConfidenceCheckResult(
            should_escalate=False,
            reason="Confidence within acceptable range",
            confidence_score=llm_confidence,
            recommendation="Continue with bot responses"
        )
    
    def detect_frustration(self, message_text: str) -> bool:
        """
        Detect signs of user frustration in message
        
        Returns True if frustration keywords detected
        """
        frustration_keywords = [
            "not helpful",
            "useless",
            "waste of time",
            "don't understand",
            "you're not listening",
            "terrible",
            "awful",
            "this is ridiculous",
            "not working",
            "give up",
            "frustrated",
            "annoying",
            "stupid bot"
        ]
        
        message_lower = message_text.lower()
        return any(keyword in message_lower for keyword in frustration_keywords)
```

---

## Task 29: PII Masking & Redaction

### Implementation: services/pii_masker.py

```python
import re
from typing import Dict, List
import structlog

logger = structlog.get_logger()

class PIIMasker:
    """Mask personally identifiable information before sending to LLM"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection"""
        return {
            "email": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            "phone": re.compile(
                r'(\+\d{1,3}[-.\s]?)?'
                r'(\(?\d{3}\)?[-.\s]?)?'
                r'\d{3}[-.\s]?\d{4}\b'
            ),
            "ssn": re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b'
            ),
            "credit_card": re.compile(
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            ),
            "ip_address": re.compile(
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ),
            # API keys, tokens (common patterns)
            "api_key": re.compile(
                r'\b[A-Za-z0-9_-]{20,}\b'
            )
        }
    
    def mask_pii(self, text: str) -> tuple[str, List[Dict]]:
        """
        Mask PII in text before sending to LLM
        
        Args:
            text: Original text potentially containing PII
        
        Returns:
            (masked_text, redactions_log)
        """
        masked_text = text
        redactions = []
        
        # Email masking
        for match in self.patterns["email"].finditer(text):
            email = match.group()
            masked_email = self._mask_email(email)
            masked_text = masked_text.replace(email, masked_email)
            redactions.append({
                "type": "email",
                "original": email,
                "masked": masked_email
            })
        
        # Phone masking
        for match in self.patterns["phone"].finditer(text):
            phone = match.group()
            masked_phone = "[PHONE_REDACTED]"
            masked_text = masked_text.replace(phone, masked_phone)
            redactions.append({
                "type": "phone",
                "masked": masked_phone
            })
        
        # SSN masking
        for match in self.patterns["ssn"].finditer(text):
            ssn = match.group()
            masked_ssn = "XXX-XX-XXXX"
            masked_text = masked_text.replace(ssn, masked_ssn)
            redactions.append({
                "type": "ssn",
                "masked": masked_ssn
            })
        
        # Credit card masking
        for match in self.patterns["credit_card"].finditer(text):
            cc = match.group()
            masked_cc = "XXXX-XXXX-XXXX-XXXX"
            masked_text = masked_text.replace(cc, masked_cc)
            redactions.append({
                "type": "credit_card",
                "masked": masked_cc
            })
        
        if redactions:
            logger.info(
                "PII masked before LLM",
                redaction_count=len(redactions),
                types=[r["type"] for r in redactions]
            )
        
        return masked_text, redactions
    
    def _mask_email(self, email: str) -> str:
        """Mask email while keeping domain visible"""
        local, domain = email.split("@")
        if len(local) > 2:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        else:
            masked_local = "*" * len(local)
        return f"{masked_local}@{domain}"
```

---

## Task 30: LLM Usage Quotas

### Implementation: services/llm_quota_manager.py

```python
from src.utils.cache import cache
from typing import Optional
import structlog

logger = structlog.get_logger()

class LLMQuotaManager:
    """Manage per-user and system-wide LLM usage quotas"""
    
    def __init__(
        self,
        per_session_limit: int = 10,
        per_day_limit: int = 50,
        system_daily_budget: float = 100.0,  # USD
        cost_per_1k_tokens: float = 0.002    # $0.002 per 1K tokens
    ):
        self.per_session_limit = per_session_limit
        self.per_day_limit = per_day_limit
        self.system_daily_budget = system_daily_budget
        self.cost_per_1k_tokens = cost_per_1k_tokens
    
    async def check_quota(self, user_id: int) -> dict:
        """
        Check if user is within LLM usage quota
        
        Returns dict with quota status
        """
        session_count = await self._get_session_count(user_id)
        day_count = await self._get_day_count(user_id)
        system_cost = await self._get_system_daily_cost()
        
        quota_status = {
            "allowed": True,
            "session_count": session_count,
            "session_limit": self.per_session_limit,
            "day_count": day_count,
            "day_limit": self.per_day_limit,
            "system_cost_usd": system_cost,
            "system_budget_usd": self.system_daily_budget,
            "reason": None
        }
        
        # Check session limit
        if session_count >= self.per_session_limit:
            quota_status["allowed"] = False
            quota_status["reason"] = "Session LLM quota exceeded"
            logger.warning(
                "Session LLM quota exceeded",
                user_id=user_id,
                count=session_count
            )
            return quota_status
        
        # Check daily limit
        if day_count >= self.per_day_limit:
            quota_status["allowed"] = False
            quota_status["reason"] = "Daily LLM quota exceeded"
            logger.warning(
                "Daily LLM quota exceeded",
                user_id=user_id,
                count=day_count
            )
            return quota_status
        
        # Check system budget
        if system_cost >= self.system_daily_budget:
            quota_status["allowed"] = False
            quota_status["reason"] = "System daily budget exceeded"
            logger.error(
                "System LLM budget exceeded",
                cost=system_cost,
                budget=self.system_daily_budget
            )
            return quota_status
        
        return quota_status
    
    async def increment_usage(self, user_id: int, tokens_used: int):
        """Increment LLM usage counters after successful call"""
        
        # Increment session count
        session_key = f"llm_quota:session:{user_id}"
        await cache.increment(session_key, ttl=86400)  # 24h TTL
        
        # Increment daily count
        day_key = f"llm_quota:day:{user_id}"
        await cache.increment(day_key, ttl=86400)
        
        # Track system cost
        cost = (tokens_used / 1000) * self.cost_per_1k_tokens
        await self._increment_system_cost(cost)
        
        logger.info(
            "LLM usage tracked",
            user_id=user_id,
            tokens=tokens_used,
            cost_usd=cost
        )
    
    async def _get_session_count(self, user_id: int) -> int:
        """Get session LLM call count"""
        key = f"llm_quota:session:{user_id}"
        count = await cache.get(key)
        return int(count) if count else 0
    
    async def _get_day_count(self, user_id: int) -> int:
        """Get daily LLM call count"""
        key = f"llm_quota:day:{user_id}"
        count = await cache.get(key)
        return int(count) if count else 0
    
    async def _get_system_daily_cost(self) -> float:
        """Get total system LLM cost today"""
        key = "llm_quota:system:daily_cost"
        cost = await cache.get(key)
        return float(cost) if cost else 0.0
    
    async def _increment_system_cost(self, cost: float):
        """Increment system-wide daily cost"""
        key = "llm_quota:system:daily_cost"
        current = await self._get_system_daily_cost()
        await cache.set(key, current + cost, ttl=86400)
```

---

## Task 31: Internal Test Harness

### Implementation: tests/llm_test_harness.py

```python
import asyncio
from typing import List, Dict
from src.services.llm_adapter import LongCatAdapter, LLMMessage
from src.services.prompt_templates import PromptTemplateManager
from src.core.config import settings
import structlog

logger = structlog.get_logger()

class LLMTestHarness:
    """Test harness for validating LLM responses"""
    
    def __init__(self):
        self.adapter = LongCatAdapter(
            api_key=settings.LONGCAT_API_KEY,
            model=settings.LONGCAT_MODEL
        )
        self.prompt_manager = PromptTemplateManager()
    
    async def run_test_suite(self):
        """Run comprehensive test suite"""
        print("🧪 LLM Test Harness Starting...\n")
        
        test_scenarios = [
            {
                "name": "General Service Inquiry",
                "user_message": "What services do you offer?",
                "expected_keywords": ["custom software", "devops", "cloud"]
            },
            {
                "name": "Pricing Question",
                "user_message": "How much does a CI/CD pipeline cost?",
                "expected_keywords": ["budget", "range", "depends"]
            },
            {
                "name": "Technical Question",
                "user_message": "What's the difference between Docker and Kubernetes?",
                "expected_keywords": ["container", "orchestration", "docker"]
            },
            {
                "name": "Complex Request",
                "user_message": "I need to migrate a legacy monolith to microservices on AWS",
                "expected_keywords": ["architecture", "migration", "aws", "microservices"]
            },
            {
                "name": "Ambiguous Query",
                "user_message": "Can you help?",
                "expected_keywords": ["project", "service", "what", "need"]
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"📝 Test: {scenario['name']}")
            print(f"   User: {scenario['user_message']}")
            
            result = await self._run_single_test(
                scenario["user_message"],
                scenario["expected_keywords"]
            )
            
            results.append(result)
            
            print(f"   ✅ Confidence: {result['confidence']:.2f}")
            print(f"   ⏱️  Latency: {result['latency_ms']}ms")
            print(f"   🔤 Tokens: {result['tokens']}")
            print(f"   📊 Keywords Found: {result['keywords_found']}/{len(scenario['expected_keywords'])}")
            print(f"   Response: {result['response'][:100]}...\n")
        
        # Summary
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        avg_latency = sum(r['latency_ms'] for r in results) / len(results)
        total_cost = sum(r['cost_usd'] for r in results)
        
        print("=" * 60)
        print("📊 Test Suite Summary")
        print(f"   Tests Run: {len(results)}")
        print(f"   Avg Confidence: {avg_confidence:.2f}")
        print(f"   Avg Latency: {avg_latency:.0f}ms")
        print(f"   Total Cost: ${total_cost:.4f}")
        print("=" * 60)
    
    async def _run_single_test(
        self,
        user_message: str,
        expected_keywords: List[str]
    ) -> Dict:
        """Run single test scenario"""
        
        # Build system prompt
        system_prompt = self.prompt_manager.get_system_prompt(
            template_name="base",
            conversation_history="No previous conversation"
        )
        
        # Create messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_message)
        ]
        
        # Generate response
        response = await self.adapter.generate_response(
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        
        # Check keywords
        response_lower = response.content.lower()
        keywords_found = sum(
            1 for keyword in expected_keywords
            if keyword.lower() in response_lower
        )
        
        # Calculate cost
        cost_usd = (response.tokens_used / 1000) * 0.002
        
        return {
            "response": response.content,
            "confidence": response.confidence,
            "latency_ms": response.latency_ms,
            "tokens": response.tokens_used,
            "cost_usd": cost_usd,
            "keywords_found": keywords_found,
            "expected_keywords": len(expected_keywords)
        }

async def main():
    """Run test harness"""
    harness = LLMTestHarness()
    await harness.run_test_suite()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Task 32: LLM Metadata Logging

### Implementation: services/llm_logger.py

```python
from dataclasses import asdict
from src.services.llm_adapter import LLMResponse
from src.db.models.message import Message
import structlog

logger = structlog.get_logger()

class LLMLogger:
    """Log LLM interactions with privacy safeguards"""
    
    async def log_llm_interaction(
        self,
        user_id: int,
        conversation_id: str,
        message_id: str,
        llm_response: LLMResponse,
        prompt_tokens: int,
        system_prompt_length: int
    ):
        """
        Log LLM interaction metadata
        
        NOTE: Does NOT log actual prompt content for privacy
        """
        
        # Calculate metrics
        total_cost = (llm_response.tokens_used / 1000) * 0.002
        
        # Structured logging (sent to monitoring system)
        logger.info(
            "llm_interaction",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            model=llm_response.model,
            tokens_used=llm_response.tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=llm_response.tokens_used - prompt_tokens,
            latency_ms=llm_response.latency_ms,
            confidence=llm_response.confidence,
            finish_reason=llm_response.finish_reason,
            cost_usd=total_cost,
            system_prompt_length=system_prompt_length,
            # Privacy: DO NOT log actual prompt or response content
        )
        
        # Check for anomalies
        if llm_response.latency_ms > 10000:  # >10s
            logger.warning(
                "llm_high_latency",
                latency_ms=llm_response.latency_ms,
                model=llm_response.model
            )
        
        if llm_response.tokens_used > 2000:  # Unusually high
            logger.warning(
                "llm_high_token_usage",
                tokens=llm_response.tokens_used,
                conversation_id=conversation_id
            )
        
        if llm_response.confidence < 0.5:  # Very low confidence
            logger.warning(
                "llm_low_confidence",
                confidence=llm_response.confidence,
                conversation_id=conversation_id
            )
```

---

## Implementation Checklist for Phase 3

- [ ] Set up LongCat.chat account and get API key
- [ ] Implement `LongCatAdapter` with retry logic
- [ ] Create system prompt templates for different contexts
- [ ] Build conversation context manager with token trimming
- [ ] Implement confidence checker with escalation triggers
- [ ] Add PII masking before sending to LLM
- [ ] Create LLM usage quota system (per-user & system-wide)
- [ ] Build internal test harness for validating responses
- [ ] Implement LLM metadata logging (without sensitive content)
- [ ] Test LLM integration end-to-end
- [ ] Monitor LLM costs and optimize token usage

**Next Steps:** Move to Phase 4 - Human Handoff & Agent Tools
