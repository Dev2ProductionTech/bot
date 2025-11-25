# Phase 4 — Human Handoff & Agent Tools

## Task 33: Telegram Agent Group & Conversation Routing

### Agent Group Setup

**Create Private Telegram Group for Agents:**
```
1. Create a new Telegram group: "Dev2Production Support Agents"
2. Add the bot to the group
3. Make the bot an admin with permissions:
   - Read all messages
   - Send messages
   - Delete messages
   - Pin messages
4. Get the group chat ID using getUpdates API
5. Store group chat ID in environment: AGENT_GROUP_CHAT_ID
```

### Implementation: services/escalation_service.py

```python
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime
from src.services.telegram import TelegramClient
from src.services.conversation_manager import ConversationManager
from src.db.models.conversation import Conversation, ConversationStatus
from src.db.models.agent import Agent
from src.core.config import settings
from src.utils.cache import cache
import structlog

logger = structlog.get_logger()

@dataclass
class EscalationRequest:
    conversation_id: str
    user_id: int
    username: str
    reason: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    summary: str
    lead_score: Optional[str] = None

class EscalationService:
    """Handle conversation escalation to human agents"""
    
    def __init__(self):
        self.telegram = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        self.conversation_manager = ConversationManager()
        self.agent_group_id = settings.AGENT_GROUP_CHAT_ID
    
    async def escalate_conversation(
        self,
        escalation_request: EscalationRequest
    ) -> dict:
        """
        Escalate conversation to agent group
        
        Returns status dict with escalation details
        """
        
        # Update conversation status
        await self.conversation_manager.update_status(
            conversation_id=escalation_request.conversation_id,
            status=ConversationStatus.ESCALATED,
            escalated_at=datetime.utcnow()
        )
        
        # Build escalation message for agent group
        escalation_msg = self._format_escalation_message(escalation_request)
        
        # Create inline keyboard for agent actions
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✋ Claim Conversation",
                        "callback_data": f"agent:claim:{escalation_request.conversation_id}"
                    }
                ],
                [
                    {
                        "text": "📋 View Full History",
                        "callback_data": f"agent:history:{escalation_request.conversation_id}"
                    },
                    {
                        "text": "🤖 Return to Bot",
                        "callback_data": f"agent:unassign:{escalation_request.conversation_id}"
                    }
                ]
            ]
        }
        
        # Send to agent group
        agent_message = await self.telegram.send_message(
            chat_id=self.agent_group_id,
            text=escalation_msg,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Store escalation metadata in Redis
        await self._store_escalation_metadata(
            conversation_id=escalation_request.conversation_id,
            agent_message_id=agent_message.message_id,
            priority=escalation_request.priority
        )
        
        # Notify user about escalation
        await self._notify_user_escalated(escalation_request)
        
        logger.info(
            "Conversation escalated",
            conversation_id=escalation_request.conversation_id,
            reason=escalation_request.reason,
            priority=escalation_request.priority
        )
        
        return {
            "success": True,
            "conversation_id": escalation_request.conversation_id,
            "agent_message_id": agent_message.message_id,
            "status": "escalated"
        }
    
    def _format_escalation_message(self, request: EscalationRequest) -> str:
        """Format escalation message for agent group"""
        
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }
        
        emoji = priority_emoji.get(request.priority, "⚪")
        
        message_parts = [
            f"{emoji} **NEW ESCALATION** {emoji}\n",
            f"**Priority:** {request.priority.upper()}",
            f"**Reason:** {request.reason}",
            f"**User:** @{request.username} (ID: {request.user_id})",
        ]
        
        if request.lead_score:
            message_parts.append(f"**Lead Score:** {request.lead_score.upper()} 🔥" if request.lead_score == "hot" else f"**Lead Score:** {request.lead_score}")
        
        message_parts.extend([
            f"\n**Conversation Summary:**",
            f"{request.summary}",
            f"\n**Conversation ID:** `{request.conversation_id}`",
            f"\n_Click 'Claim Conversation' to take ownership_"
        ])
        
        return "\n".join(message_parts)
    
    async def _notify_user_escalated(self, request: EscalationRequest):
        """Notify user that conversation has been escalated"""
        
        user_message = (
            "✅ **Connected to Human Support**\n\n"
            "I've transferred you to our team. A human agent will respond shortly.\n\n"
            "**Expected Response Time:** Within 4 business hours\n"
            "_(Usually much faster during business hours)_\n\n"
            "Feel free to continue the conversation here, and our agent will see your messages."
        )
        
        await self.telegram.send_message(
            chat_id=request.user_id,
            text=user_message,
            parse_mode="Markdown"
        )
    
    async def _store_escalation_metadata(
        self,
        conversation_id: str,
        agent_message_id: int,
        priority: str
    ):
        """Store escalation metadata in Redis"""
        key = f"escalation:{conversation_id}"
        data = {
            "agent_message_id": agent_message_id,
            "priority": priority,
            "escalated_at": datetime.utcnow().isoformat()
        }
        await cache.set(key, data, ttl=86400 * 7)  # 7 days
    
    async def check_agent_availability(self) -> dict:
        """
        Check if any agents are available
        
        Returns availability status
        """
        # Get online agents from database
        # For now, we'll assume agents are available during business hours
        
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.UTC)
        hour = now.hour
        
        # Business hours: 9 AM - 6 PM UTC (adjust for your timezone)
        is_business_hours = 9 <= hour < 18
        
        # In production, query Agent table for online agents
        # online_agents = await agent_repository.get_online_agents()
        
        return {
            "available": is_business_hours,  # Simplified for now
            "business_hours": is_business_hours,
            "message": "Agents available" if is_business_hours else "Outside business hours"
        }
```

---

## Task 34: Agent Reply Mapping (Bidirectional Communication)

### Implementation: services/agent_messaging_service.py

```python
from src.services.telegram import TelegramClient
from src.services.conversation_manager import ConversationManager
from src.db.models.message import Message, SenderType
from src.utils.cache import cache
from src.core.config import settings
import structlog

logger = structlog.get_logger()

class AgentMessagingService:
    """Handle bidirectional messaging between agents and users"""
    
    def __init__(self):
        self.telegram = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        self.conversation_manager = ConversationManager()
        self.agent_group_id = settings.AGENT_GROUP_CHAT_ID
    
    async def handle_agent_message(
        self,
        message_text: str,
        agent_telegram_id: int,
        agent_username: str,
        reply_to_message_id: Optional[int] = None
    ) -> dict:
        """
        Handle message from agent in group chat
        
        Determines which user conversation to route to based on context
        """
        
        # Get conversation ID from context
        conversation_id = await self._get_conversation_from_context(
            agent_telegram_id,
            reply_to_message_id
        )
        
        if not conversation_id:
            return {
                "success": False,
                "error": "No active conversation found. Please claim a conversation first."
            }
        
        # Get conversation details
        conversation = await self.conversation_manager.get_by_id(conversation_id)
        
        if not conversation:
            return {
                "success": False,
                "error": "Conversation not found"
            }
        
        # Forward agent message to user
        await self.telegram.send_message(
            chat_id=conversation.telegram_user_id,
            text=f"**{agent_username}:** {message_text}",
            parse_mode="Markdown"
        )
        
        # Save message to database
        await self.conversation_manager.add_message(
            conversation_id=conversation_id,
            sender_type=SenderType.AGENT,
            sender_id=agent_telegram_id,
            content=message_text,
            content_type="text"
        )
        
        # Send confirmation in agent group
        await self.telegram.send_message(
            chat_id=self.agent_group_id,
            text=f"✅ Message sent to user @{conversation.telegram_username}",
            reply_to_message_id=reply_to_message_id
        )
        
        logger.info(
            "Agent message forwarded to user",
            conversation_id=conversation_id,
            agent_id=agent_telegram_id
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "user_id": conversation.telegram_user_id
        }
    
    async def handle_user_message_during_escalation(
        self,
        message_text: str,
        user_id: int,
        conversation_id: str
    ):
        """
        Forward user message to agent group during escalation
        """
        
        conversation = await self.conversation_manager.get_by_id(conversation_id)
        
        # Get assigned agent (if any)
        agent_name = "Unassigned"
        if conversation.escalated_to_agent_id:
            agent = await self._get_agent_by_id(conversation.escalated_to_agent_id)
            if agent:
                agent_name = f"@{agent.telegram_username}"
        
        # Format message for agent group
        agent_notification = (
            f"💬 **New message from user**\n"
            f"**User:** @{conversation.telegram_username}\n"
            f"**Assigned to:** {agent_name}\n"
            f"**Conversation ID:** `{conversation_id}`\n\n"
            f"**Message:**\n{message_text}"
        )
        
        # Send to agent group
        await self.telegram.send_message(
            chat_id=self.agent_group_id,
            text=agent_notification,
            parse_mode="Markdown"
        )
        
        # Save to database
        await self.conversation_manager.add_message(
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            content=message_text,
            telegram_message_id=user_id,
            content_type="text"
        )
    
    async def _get_conversation_from_context(
        self,
        agent_telegram_id: int,
        reply_to_message_id: Optional[int]
    ) -> Optional[str]:
        """
        Get conversation ID from agent's context
        
        Checks:
        1. If replying to escalation message - extract conversation ID
        2. If agent has claimed conversation - get from Redis
        """
        
        # Check if agent has active claimed conversation
        active_conv = await cache.get(f"agent:{agent_telegram_id}:active_conversation")
        if active_conv:
            return active_conv
        
        # TODO: If replying to message, parse conversation ID from original message
        # This requires storing message mappings in Redis
        
        return None
    
    async def _get_agent_by_id(self, agent_id: str):
        """Get agent from database"""
        # TODO: Implement database query
        return None
```

---

## Task 35: Minimal Web Dashboard

### Implementation: api/admin.py

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.services.conversation_manager import ConversationManager
from src.db.models.conversation import ConversationStatus
from typing import List
import structlog

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")
logger = structlog.get_logger()

conversation_manager = ConversationManager()

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Render admin dashboard showing active conversations"""
    
    # Get active conversations
    active_conversations = await conversation_manager.get_conversations_by_status(
        status=ConversationStatus.ACTIVE,
        limit=50
    )
    
    # Get escalated conversations
    escalated_conversations = await conversation_manager.get_conversations_by_status(
        status=ConversationStatus.ESCALATED,
        limit=50
    )
    
    # Get recent leads
    recent_leads = await conversation_manager.get_recent_leads(limit=20)
    
    # Calculate stats
    stats = {
        "active_count": len(active_conversations),
        "escalated_count": len(escalated_conversations),
        "leads_today": len([l for l in recent_leads if l.created_at.date() == datetime.utcnow().date()]),
        "total_conversations": await conversation_manager.get_total_count()
    }
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "active_conversations": active_conversations,
            "escalated_conversations": escalated_conversations,
            "recent_leads": recent_leads
        }
    )

@router.get("/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: str):
    """Get detailed conversation information"""
    
    conversation = await conversation_manager.get_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = await conversation_manager.get_messages(
        conversation_id=conversation_id,
        limit=100
    )
    
    # Get lead data if exists
    lead = await conversation_manager.get_lead_by_conversation(conversation_id)
    
    return {
        "conversation": {
            "id": str(conversation.id),
            "user_id": conversation.telegram_user_id,
            "username": conversation.telegram_username,
            "status": conversation.status.value,
            "lead_score": conversation.lead_score.value if conversation.lead_score else None,
            "created_at": conversation.created_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
        },
        "messages": [
            {
                "id": str(msg.id),
                "sender_type": msg.sender_type.value,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "llm_used": msg.llm_used,
                "confidence": msg.llm_confidence
            }
            for msg in messages
        ],
        "lead": {
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "project_type": lead.project_type.value if lead.project_type else None,
            "budget_range": lead.budget_range.value,
            "timeline": lead.timeline.value if lead.timeline else None,
            "lead_score": lead.lead_score,
            "lead_stage": lead.lead_stage.value
        } if lead else None
    }

@router.post("/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str):
    """Close a conversation"""
    
    await conversation_manager.update_status(
        conversation_id=conversation_id,
        status=ConversationStatus.CLOSED
    )
    
    return {"success": True, "conversation_id": conversation_id}
```

### Dashboard HTML Template (src/templates/dashboard.html)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Dev2Production Bot - Admin Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #2196F3;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .conversations {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            text-align: left;
            padding: 12px;
            background: #f5f5f5;
            font-weight: 600;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        .badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-hot { background: #ff5722; color: white; }
        .badge-warm { background: #ff9800; color: white; }
        .badge-cold { background: #2196F3; color: white; }
        .badge-escalated { background: #f44336; color: white; }
        .badge-active { background: #4CAF50; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Dev2Production Bot Dashboard</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.active_count }}</div>
                <div class="stat-label">Active Conversations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.escalated_count }}</div>
                <div class="stat-label">Escalated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.leads_today }}</div>
                <div class="stat-label">Leads Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_conversations }}</div>
                <div class="stat-label">Total Conversations</div>
            </div>
        </div>
        
        <div class="conversations">
            <h2>🔥 Escalated Conversations</h2>
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Lead Score</th>
                        <th>Status</th>
                        <th>Escalated At</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for conv in escalated_conversations %}
                    <tr>
                        <td>@{{ conv.telegram_username }}</td>
                        <td>
                            {% if conv.lead_score %}
                            <span class="badge badge-{{ conv.lead_score.value }}">{{ conv.lead_score.value.upper() }}</span>
                            {% endif %}
                        </td>
                        <td><span class="badge badge-escalated">ESCALATED</span></td>
                        <td>{{ conv.escalated_at.strftime('%Y-%m-%d %H:%M') if conv.escalated_at else '-' }}</td>
                        <td>
                            <a href="/admin/conversations/{{ conv.id }}">View</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="conversations">
            <h2>💬 Active Conversations</h2>
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Lead Score</th>
                        <th>Last Message</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for conv in active_conversations %}
                    <tr>
                        <td>@{{ conv.telegram_username }}</td>
                        <td>
                            {% if conv.lead_score %}
                            <span class="badge badge-{{ conv.lead_score.value }}">{{ conv.lead_score.value.upper() }}</span>
                            {% endif %}
                        </td>
                        <td>{{ conv.last_message_at.strftime('%Y-%m-%d %H:%M') if conv.last_message_at else '-' }}</td>
                        <td>
                            <a href="/admin/conversations/{{ conv.id }}">View</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
```

---

## Task 36: Agent Claim/Takeover System

### Implementation: services/agent_assignment_service.py

```python
from typing import Optional
from datetime import datetime
from src.db.models.conversation import Conversation
from src.db.models.agent import Agent
from src.utils.cache import cache
from src.services.telegram import TelegramClient
from src.core.config import settings
import structlog

logger = structlog.get_logger()

class AgentAssignmentService:
    """Manage agent assignment to conversations"""
    
    def __init__(self):
        self.telegram = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        self.agent_group_id = settings.AGENT_GROUP_CHAT_ID
    
    async def claim_conversation(
        self,
        conversation_id: str,
        agent_telegram_id: int,
        agent_username: str
    ) -> dict:
        """
        Agent claims ownership of a conversation
        """
        
        # Check if already claimed
        existing_agent = await self._get_assigned_agent(conversation_id)
        
        if existing_agent and existing_agent != agent_telegram_id:
            # Already claimed by another agent
            return {
                "success": False,
                "error": f"Conversation already claimed by @{existing_agent['username']}"
            }
        
        # Assign conversation to agent
        await self._assign_agent(
            conversation_id=conversation_id,
            agent_telegram_id=agent_telegram_id,
            agent_username=agent_username
        )
        
        # Update conversation in database
        # await conversation_repo.update_agent(conversation_id, agent_id)
        
        # Notify agent group
        await self.telegram.send_message(
            chat_id=self.agent_group_id,
            text=f"✅ @{agent_username} claimed conversation `{conversation_id}`",
            parse_mode="Markdown"
        )
        
        logger.info(
            "Conversation claimed",
            conversation_id=conversation_id,
            agent_id=agent_telegram_id
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "agent_username": agent_username
        }
    
    async def release_conversation(
        self,
        conversation_id: str,
        agent_telegram_id: int
    ) -> dict:
        """
        Release conversation back to unassigned pool
        """
        
        # Check if agent owns this conversation
        assigned_agent = await self._get_assigned_agent(conversation_id)
        
        if not assigned_agent or assigned_agent['telegram_id'] != agent_telegram_id:
            return {
                "success": False,
                "error": "You don't own this conversation"
            }
        
        # Remove assignment
        await self._unassign_agent(conversation_id)
        
        # Notify group
        await self.telegram.send_message(
            chat_id=self.agent_group_id,
            text=f"🔓 Conversation `{conversation_id}` released back to pool",
            parse_mode="Markdown"
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id
        }
    
    async def _assign_agent(
        self,
        conversation_id: str,
        agent_telegram_id: int,
        agent_username: str
    ):
        """Store agent assignment in Redis"""
        
        # Store conversation -> agent mapping
        conv_key = f"conversation:{conversation_id}:agent"
        await cache.set(conv_key, {
            "telegram_id": agent_telegram_id,
            "username": agent_username,
            "claimed_at": datetime.utcnow().isoformat()
        }, ttl=86400 * 7)  # 7 days
        
        # Store agent -> active conversation mapping
        agent_key = f"agent:{agent_telegram_id}:active_conversation"
        await cache.set(agent_key, conversation_id, ttl=86400 * 7)
    
    async def _unassign_agent(self, conversation_id: str):
        """Remove agent assignment"""
        
        # Get current agent
        assigned_agent = await self._get_assigned_agent(conversation_id)
        
        if assigned_agent:
            # Remove both mappings
            conv_key = f"conversation:{conversation_id}:agent"
            agent_key = f"agent:{assigned_agent['telegram_id']}:active_conversation"
            
            await cache.delete(conv_key)
            await cache.delete(agent_key)
    
    async def _get_assigned_agent(self, conversation_id: str) -> Optional[dict]:
        """Get agent assigned to conversation"""
        key = f"conversation:{conversation_id}:agent"
        agent_data = await cache.get(key)
        
        if agent_data:
            import json
            return json.loads(agent_data)
        return None
```

---

## Task 37: Canned Agent Reply Templates

### Implementation: services/agent_templates.py

```python
from typing import Dict, List

class AgentReplyTemplates:
    """Pre-written templates for common agent responses"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load canned response templates"""
        return {
            "greeting": (
                "Hi {username}! I'm {agent_name} from Dev2Production. "
                "I've reviewed your conversation with our bot. How can I help you further?"
            ),
            
            "project_review": (
                "Thanks for sharing your project details. Based on what you've described, "
                "I think we can definitely help. Let me ask a few clarifying questions:\n\n"
                "1. {question1}\n"
                "2. {question2}\n"
                "3. {question3}"
            ),
            
            "scheduling": (
                "Great! I'd love to schedule a call to discuss this further.\n\n"
                "📅 You can book a time that works for you here: {calendly_link}\n\n"
                "Or let me know your availability and I'll send over some options."
            ),
            
            "pricing_inquiry": (
                "For a project like yours, we typically see costs in the range of {range}. "
                "The final price depends on:\n"
                "• Specific technical requirements\n"
                "• Timeline and urgency\n"
                "• Integration complexity\n\n"
                "I'd be happy to put together a detailed proposal. "
                "Can we schedule a 30-minute discovery call?"
            ),
            
            "follow_up": (
                "Hi {username}, following up on our conversation from {date}. "
                "Have you had a chance to review the information I sent?\n\n"
                "Let me know if you have any questions or if you'd like to move forward!"
            ),
            
            "closing": (
                "Perfect! Here are the next steps:\n\n"
                "1. {step1}\n"
                "2. {step2}\n"
                "3. {step3}\n\n"
                "I'll be in touch within {timeframe}. Feel free to reach out if you need anything in the meantime."
            ),
            
            "not_fit": (
                "Thanks for reaching out! After reviewing your requirements, "
                "I think {reason}. However, I'd be happy to refer you to {alternative}. "
                "Would that be helpful?"
            ),
            
            "technical_answer": (
                "Great question about {topic}! Here's how we typically approach this:\n\n"
                "{explanation}\n\n"
                "In your case, I'd recommend {recommendation}. "
                "Want me to elaborate on any specific aspect?"
            )
        }
    
    def get_template(self, template_name: str) -> str:
        """Get template by name"""
        return self.templates.get(template_name, "")
    
    def format_template(self, template_name: str, **kwargs) -> str:
        """Get and format template with variables"""
        template = self.get_template(template_name)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Error: Missing template variable {e}"
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates"""
        return [
            {"name": name, "preview": content[:100] + "..."}
            for name, content in self.templates.items()
        ]
```

### Telegram Command for Templates

```python
async def handle_agent_template_command(callback_query):
    """Show agent template picker"""
    
    agent_templates = AgentReplyTemplates()
    templates = agent_templates.list_templates()
    
    # Build inline keyboard with template options
    keyboard = {
        "inline_keyboard": [
            [{"text": f"📝 {t['name'].title()}", "callback_data": f"template:{t['name']}"}]
            for t in templates[:10]  # Show first 10
        ]
    }
    
    await telegram.send_message(
        chat_id=callback_query.message.chat.id,
        text="**📝 Select a template:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
```

---

## Task 38: Role-Based Access Control

### Implementation: src/db/models/agent.py (Enhanced)

```python
from sqlalchemy import String, Enum, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base, TimestampMixin
import uuid
import enum

class AgentRole(str, enum.Enum):
    AGENT = "agent"  # Basic support agent
    SENIOR_AGENT = "senior_agent"  # Can handle escalations
    ADMIN = "admin"  # Full system access
    SUPER_ADMIN = "super_admin"  # Can manage agents

class AgentStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    AWAY = "away"

class Agent(Base, TimestampMixin):
    __tablename__ = "agents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    telegram_username: Mapped[str] = mapped_column(String(255))
    
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    
    role: Mapped[AgentRole] = mapped_column(
        Enum(AgentRole),
        default=AgentRole.AGENT
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus),
        default=AgentStatus.OFFLINE
    )
    
    # Stats
    conversations_handled: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_time_seconds: Mapped[float | None] = mapped_column(nullable=True)
    customer_satisfaction_score: Mapped[float | None] = mapped_column(nullable=True)
    
    # Permissions
    can_escalate: Mapped[bool] = mapped_column(Boolean, default=False)
    can_close_conversations: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_agents: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Activity tracking
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### RBAC Middleware

```python
from functools import wraps
from src.db.models.agent import AgentRole

class PermissionDeniedError(Exception):
    pass

def require_role(*allowed_roles: AgentRole):
    """Decorator to require specific agent roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(agent_telegram_id: int, *args, **kwargs):
            # Get agent from database
            agent = await get_agent_by_telegram_id(agent_telegram_id)
            
            if not agent:
                raise PermissionDeniedError("Agent not found")
            
            if agent.role not in allowed_roles:
                raise PermissionDeniedError(
                    f"Requires role: {', '.join(r.value for r in allowed_roles)}"
                )
            
            return await func(agent_telegram_id, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_role(AgentRole.ADMIN, AgentRole.SUPER_ADMIN)
async def delete_conversation(agent_telegram_id: int, conversation_id: str):
    """Only admins can delete conversations"""
    pass

@require_role(AgentRole.SENIOR_AGENT, AgentRole.ADMIN, AgentRole.SUPER_ADMIN)
async def handle_critical_escalation(agent_telegram_id: int, escalation_id: str):
    """Only senior agents and above can handle critical escalations"""
    pass
```

---

## Implementation Checklist for Phase 4

- [ ] Create Telegram agent group and add bot
- [ ] Get agent group chat ID and store in config
- [ ] Implement escalation service with priority routing
- [ ] Build bidirectional message forwarding
- [ ] Create agent claim/release system
- [ ] Develop minimal web dashboard with Jinja2 templates
- [ ] Implement canned reply templates for agents
- [ ] Set up agent database schema with roles
- [ ] Add RBAC middleware for sensitive operations
- [ ] Test end-to-end escalation flow
- [ ] Train agents on bot usage and workflows

**Next Steps:** Move to Phase 5 - Quality, Testing & Security
