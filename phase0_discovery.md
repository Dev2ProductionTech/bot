# Phase 0 — Discovery & Planning

## Task 1: Bot Persona & Behavior Guidelines

### Company Profile (dev2production.tech)
**Brand Voice:** Professional, confident, results-oriented  
**Tagline:** "Ship Quality Products Faster Than Ever"  
**Core Promise:** Production-ready applications, not prototypes

### Services Offered
1. **Custom Software Development** - Tailored applications built to exact specifications
2. **System Integration** - Connect existing tools and platforms, automate workflows
3. **Performance & Reliability** - Applications engineered for speed and uptime
4. **Continuous Delivery Pipeline** - Automated workflow from code to production
5. **DevOps Automation** - Streamlined deployment pipelines
6. **Cloud Engineering** - Cloud infrastructure and optimization
7. **CI/CD Pipelines** - Build → Test → Deploy automation
8. **Infrastructure as Code** - Modern infrastructure management

### Key Differentiators
- 100+ projects delivered successfully
- 50+ happy clients worldwide
- 98% client satisfaction rating
- 24/7 support availability
- Remote-first, global reach
- Free technical consultation and project assessment
- Typical response time: within 4 business hours

### Bot Persona: "DevBot"

**Character Traits:**
- **Professional yet approachable** - Technical expertise without jargon overload
- **Solution-oriented** - Focuses on business outcomes, not just tech specs
- **Efficient** - Respects user's time, gets to the point
- **Helpful guide** - Educates while solving problems
- **Confident but humble** - "We've done 100+ projects" not "We're the best"

**Tone Guidelines:**
- ✅ **DO:** Use clear, concise language
- ✅ **DO:** Lead with business value, then technical details
- ✅ **DO:** Acknowledge complexity and offer to help navigate it
- ✅ **DO:** Provide specific examples and case studies when relevant
- ❌ **DON'T:** Oversell or use hyperbolic marketing language
- ❌ **DON'T:** Use excessive emojis (max 2-3 per message)
- ❌ **DON'T:** Provide vague "contact sales" responses without value
- ❌ **DON'T:** Ignore user questions or deflect to generic answers

**Sample Interactions:**

```
User: "What do you do?"
DevBot: "We build production-ready software that actually works in the real world. 
Our focus areas include:
• Custom applications tailored to your needs
• DevOps automation & CI/CD pipelines
• Cloud engineering & infrastructure
• System integration

We've delivered 100+ projects with 98% client satisfaction. What kind of project are you working on?"
```

```
User: "How much does a CI/CD pipeline cost?"
DevBot: "CI/CD pipeline costs depend on your tech stack, deployment frequency, and infrastructure complexity. 

Typical ranges:
• Basic setup (small team): $5K-$15K
• Mid-scale (multiple environments): $15K-$40K
• Enterprise (complex workflows): $40K+

I can help narrow this down. Could you share:
1. Your current tech stack?
2. Team size and deployment frequency?
3. Any specific requirements (security, compliance, etc.)?"
```

---

## Task 2: Primary Bot Objectives

### 1. **FAQ Handler**
- Answer common questions about services, pricing, process
- Provide instant responses for 80% of informational queries
- Fallback to LLM for nuanced questions

### 2. **Project Intake & Lead Qualification**
- Collect structured project requirements (budget, timeline, scope)
- Qualify leads based on project fit and urgency
- Score leads: Hot (ready to start), Warm (exploring), Cold (research phase)

### 3. **DevOps/Cloud Consultation**
- Provide initial technical guidance on DevOps best practices
- Recommend approaches for CI/CD, cloud architecture, automation
- Escalate complex consulting to human experts

### 4. **Lead Capture & CRM Integration**
- Capture contact details (name, email, company)
- Tag and categorize leads for sales follow-up
- Trigger notifications for high-value opportunities

### 5. **Content Discovery**
- Guide users to relevant blog articles and case studies
- Share success stories matching user's industry/use case
- Build authority and trust through educational content

### 6. **Human Escalation**
- Detect when bot is out of depth and trigger handoff
- Route urgent requests to on-call agents
- Maintain conversation context during handoff

---

## Task 3: Top 40 Expected User Queries

### Category A: General Service Inquiries (10 queries)
1. "What services do you offer?"
2. "Tell me about your company"
3. "How much experience do you have?"
4. "What makes you different from other dev shops?"
5. "Do you work with startups/enterprises?"
6. "What industries do you serve?"
7. "How long have you been in business?"
8. "Can I see your portfolio/case studies?"
9. "What technologies do you work with?"
10. "Are you available for new projects?"

**Canned Response Template (Query 1):**
```
We specialize in production-ready software development:
• Custom Software Development - Tailored applications
• DevOps Automation - CI/CD pipelines & deployment
• Cloud Engineering - Infrastructure & optimization
• System Integration - Connect & automate your tools

We've delivered 100+ projects with 98% satisfaction. What brings you here today?
```

---

### Category B: DevOps & Cloud (8 queries)
11. "What is DevOps?"
12. "How can DevOps help my startup?"
13. "What is a CI/CD pipeline?"
14. "Do you offer cloud migration services?"
15. "Can you help with AWS/Azure/GCP?"
16. "What is Infrastructure as Code?"
17. "How do you handle deployment automation?"
18. "Can you optimize our cloud costs?"

**Canned Response Template (Query 13):**
```
A CI/CD (Continuous Integration/Continuous Deployment) pipeline automates your software delivery:

🔄 Code → Build → Test → Deploy

Benefits:
• Deploy faster (multiple times per day vs. weekly)
• Fewer bugs (automated testing catches issues early)
• Less manual work (automation handles repetitive tasks)

We've built pipelines that reduced deployment time by 70% for clients. Want to explore this for your project?
```

---

### Category C: Pricing & Budget (7 queries)
19. "How much does a project cost?"
20. "What's your hourly rate?"
21. "Do you offer fixed-price projects?"
22. "What payment terms do you offer?"
23. "Is there a minimum project size?"
24. "Can you work within my budget?"
25. "Do you provide free estimates?"

**Canned Response Template (Query 19):**
```
Project costs vary based on scope and complexity. Here are typical ranges:

• CI/CD Pipeline Setup: $5K-$40K
• Custom Web Application: $20K-$150K
• Cloud Migration: $15K-$80K
• System Integration: $10K-$60K

We offer free technical consultations to provide accurate estimates. 

To give you a ballpark, I need:
1. Project type (DevOps, custom app, integration, etc.)
2. Rough timeline
3. Any specific requirements

What kind of project are you planning?
```

---

### Category D: Process & Timeline (6 queries)
26. "How long does a project take?"
27. "What is your development process?"
28. "Do you work in sprints?"
29. "How often will I get updates?"
30. "Can you meet tight deadlines?"
31. "What happens after project delivery?"

**Canned Response Template (Query 27):**
```
Our process ensures predictable results:

1️⃣ Understand - Deep dive into your business needs
2️⃣ Design - Technical blueprints + user prototypes
3️⃣ Build - Focused sprints with regular demos
4️⃣ Deploy - Launch, monitoring, training & ongoing support

You'll see progress continuously and provide feedback that shapes the final product. Typical projects range from 6 weeks to 6 months depending on complexity.

What kind of timeline are you working with?
```

---

### Category E: Technical Questions (5 queries)
32. "What programming languages do you use?"
33. "Do you use React/Node/Python/etc.?"
34. "Can you integrate with our existing systems?"
35. "Do you handle both frontend and backend?"
36. "What about mobile app development?"

**Canned Response Template (Query 33):**
```
Yes! We work with modern tech stacks including React, Node.js, Python, and more. 

Our approach is technology-agnostic - we choose the best tools for your specific needs:
• Frontend: React, Vue, Angular, Next.js
• Backend: Node.js, Python (FastAPI, Django), .NET
• DevOps: Docker, Kubernetes, Terraform, GitHub Actions
• Cloud: AWS, Azure, GCP

What's your current tech stack, or are you starting fresh?
```

---

### Category F: Support & Maintenance (4 queries)
37. "Do you provide ongoing support?"
38. "What if something breaks after launch?"
39. "Can you maintain existing projects?"
40. "Do you offer 24/7 support?"

**Canned Response Template (Query 37):**
```
Yes! We offer comprehensive post-launch support:

• 24/7 monitoring and issue response
• Ongoing optimization and updates
• Bug fixes and security patches
• Performance tuning
• Feature enhancements

Support can be structured as:
• Retainer agreements (monthly hours)
• On-demand (hourly billing)
• Dedicated team extension

Most clients start with a 3-month post-launch support package. Want to discuss your needs?
```

---

## Task 4: Conversation Flow Diagrams

### Flow 1: Onboarding Flow (/start)
```
[User: /start]
    ↓
[Bot: Welcome Message]
"👋 Hi! I'm DevBot from Dev2Production.
We build production-ready software that actually works.

I can help you with:
• Project estimates & consultation
• DevOps & cloud questions
• Service information
• Connecting with our team

What brings you here today?"
    ↓
[Quick Reply Options]
[🚀 Start a Project] [💬 Ask Questions] [📚 Learn About Services] [👤 Talk to Human]
    ↓
[Route based on selection]
```

### Flow 2: FAQ Flow
```
[User: General Question]
    ↓
[Intent Detection]
- Check canned responses (40 queries)
- Keyword/regex matching
    ↓
├─[Match Found] → [Return Canned Response] → [Follow-up Prompt]
│
└─[No Match] → [LLM Fallback]
                    ↓
                [Confidence Check]
                    ↓
                ├─[High Confidence >0.8] → [LLM Response] → [Follow-up]
                │
                └─[Low Confidence <0.8] → [Escalation Offer]
                    "I'm not 100% sure about this. Would you like to:
                    • Rephrase your question
                    • Talk to a human expert"
```

### Flow 3: Project Intake Flow
```
[User: "I want to start a project" or selects 🚀]
    ↓
[Step 1: Project Type]
"Great! Let's get started. What type of project?"
[DevOps/CI-CD] [Custom App] [Cloud Engineering] [System Integration] [Not Sure]
    ↓
[Step 2: Brief Description]
"Could you briefly describe what you're trying to build or achieve? (2-3 sentences is fine)"
    ↓
[User Input: Free Text]
    ↓
[Step 3: Timeline]
"What's your ideal timeline?"
[Urgent (<1 month)] [Normal (1-3 months)] [Flexible (3+ months)] [Just Exploring]
    ↓
[Step 4: Budget Range]
"To provide the best recommendations, what's your approximate budget?"
[<$10K] [$10K-$50K] [$50K-$150K] [$150K+] [Not Sure Yet]
    ↓
[Step 5: Contact Info]
"Perfect! To send you a detailed proposal, I'll need:
• Your name
• Email address
• Company name (optional)"
    ↓
[Collect: name, email, company]
    ↓
[Lead Scoring & Storage]
- Calculate lead score (Hot/Warm/Cold)
- Store in database
- Trigger notification to sales team
    ↓
[Confirmation]
"✅ Thanks! I've passed your details to our team.
You'll hear back within 4 business hours.

In the meantime:
• Check out our case studies: [link]
• Read our DevOps guide: [link]
• Follow our progress: [GitHub/LinkedIn]"
```

### Flow 4: File Upload Flow
```
[User: Sends file attachment]
    ↓
[File Type Detection]
    ↓
├─[Document/PDF/Image] → [Valid Format]
│   ↓
│   [File Size Check]
│   ├─[<10MB] → [Download & Store]
│   │              ↓
│   │          [Store in: /attachments/{conversation_id}/{filename}]
│   │              ↓
│   │          [Update DB: attachment record]
│   │              ↓
│   │          [Confirmation]
│   │          "✅ Got your file: {filename}
│   │           I've attached it to your conversation.
│   │           Our team will review it when they respond."
│   │
│   └─[>10MB] → "⚠️ File too large (max 10MB).
│                Can you:
│                • Split into smaller files
│                • Share via Google Drive/Dropbox link"
│
└─[Invalid Type] → "⚠️ Unsupported file type.
                    Please send: PDF, DOC, PNG, JPG, or TXT files."
```

### Flow 5: Human Escalation Flow
```
[Trigger Conditions]
├─ User types: "talk to human", "speak to agent", "escalate"
├─ LLM confidence < 0.7 (3 times in a row)
├─ User expresses frustration: "this is not helpful", "you don't understand"
├─ High-value lead detected (budget >$50K)
└─ Explicit request in project intake
    ↓
[Escalation Decision]
"I understand you'd like to speak with someone from our team."
    ↓
[Check: Agent Availability]
    ↓
├─[Agent Online] → "🟢 Connecting you now...
│                   {Agent Name} will take over this chat."
│                      ↓
│                   [Notify agent in Telegram group]
│                   [Send context: conversation history, lead score]
│                      ↓
│                   [Agent claims conversation]
│                      ↓
│                   [Agent-User Direct Chat]
│
└─[No Agent Available] → "Our team is currently helping other clients.
                          
                          Options:
                          1️⃣ Leave your email for priority callback (within 4hrs)
                          2️⃣ Schedule a call: [Calendly link]
                          3️⃣ Continue with me for now
                          
                          What works best for you?"
```

---

## Task 5: Data Models & Schema

### 1. **Conversation Model**
```python
class Conversation:
    id: UUID (PK)
    telegram_user_id: int (indexed)
    telegram_username: str (nullable)
    status: enum ['active', 'escalated', 'closed', 'archived']
    lead_score: enum ['hot', 'warm', 'cold', 'unqualified'] (nullable)
    created_at: timestamp
    updated_at: timestamp
    last_message_at: timestamp
    escalated_at: timestamp (nullable)
    escalated_to_agent_id: UUID (FK → Agent, nullable)
    metadata: jsonb {
        'language': str,
        'timezone': str,
        'source_campaign': str
    }
    
    # Retention: Archive after 90 days of inactivity
    # Hard delete after 2 years (GDPR compliance)
```

### 2. **Message Model**
```python
class Message:
    id: UUID (PK)
    conversation_id: UUID (FK → Conversation, indexed)
    sender_type: enum ['user', 'bot', 'agent']
    sender_id: UUID (nullable, FK → Agent if sender_type='agent')
    telegram_message_id: int (indexed)
    content: text
    content_type: enum ['text', 'image', 'document', 'command']
    intent: str (nullable) # e.g., 'faq_pricing', 'project_intake'
    
    # LLM tracking
    llm_used: boolean (default False)
    llm_model: str (nullable) # e.g., 'longcat-gpt-4'
    llm_tokens_used: int (nullable)
    llm_latency_ms: int (nullable)
    llm_confidence: float (nullable, 0-1)
    
    timestamp: timestamp
    metadata: jsonb {
        'edited': bool,
        'replied_to_message_id': UUID
    }
    
    # Retention: Keep messages for conversation lifetime + 90 days
```

### 3. **Lead Model**
```python
class Lead:
    id: UUID (PK)
    conversation_id: UUID (FK → Conversation, unique)
    
    # Contact info
    name: str (nullable)
    email: str (nullable, indexed)
    company: str (nullable)
    phone: str (nullable)
    
    # Project details
    project_type: enum ['devops', 'custom_app', 'cloud', 'integration', 'other']
    project_description: text (nullable)
    budget_range: enum ['<10k', '10k-50k', '50k-150k', '150k+', 'unknown']
    timeline: enum ['urgent', 'normal', 'flexible', 'exploring']
    
    # Lead scoring
    lead_score: enum ['hot', 'warm', 'cold', 'unqualified']
    lead_source: str (default 'telegram_bot')
    lead_stage: enum ['new', 'contacted', 'qualified', 'proposal_sent', 'won', 'lost']
    
    # Tracking
    created_at: timestamp
    updated_at: timestamp
    contacted_at: timestamp (nullable)
    converted_at: timestamp (nullable)
    
    # Retention: Keep indefinitely (CRM data)
    # Allow manual export/deletion on request
```

### 4. **Attachment Model**
```python
class Attachment:
    id: UUID (PK)
    conversation_id: UUID (FK → Conversation, indexed)
    message_id: UUID (FK → Message)
    
    telegram_file_id: str
    filename: str
    file_type: str # mime type
    file_size_bytes: int
    storage_path: str # e.g., 's3://bucket/conversations/{id}/file.pdf'
    
    uploaded_at: timestamp
    scanned_for_malware: boolean (default False)
    scan_result: enum ['clean', 'suspicious', 'malicious'] (nullable)
    
    # Retention: Delete after 180 days or when conversation is deleted
```

### 5. **Session Model**
```python
class Session:
    id: UUID (PK)
    conversation_id: UUID (FK → Conversation, indexed)
    telegram_user_id: int (indexed)
    
    # Session state (stored in Redis for speed)
    redis_key: str # format: 'session:{telegram_user_id}'
    
    # Rate limiting
    message_count_last_hour: int (default 0)
    message_count_last_day: int (default 0)
    llm_calls_today: int (default 0)
    
    # Flow state
    current_flow: enum ['onboarding', 'faq', 'project_intake', 'escalated', 'idle']
    flow_step: int (default 0)
    flow_data: jsonb {} # temporary state for multi-step flows
    
    # Timestamps
    created_at: timestamp
    expires_at: timestamp # TTL: 24 hours
    last_activity_at: timestamp
    
    # Retention: Auto-expire after 24 hours (Redis TTL)
    # Backup to Postgres for analytics (keep 30 days)
```

### 6. **Agent Model**
```python
class Agent:
    id: UUID (PK)
    telegram_user_id: int (unique, indexed)
    telegram_username: str
    
    name: str
    email: str
    role: enum ['agent', 'senior_agent', 'admin']
    status: enum ['online', 'offline', 'busy']
    
    # Stats
    conversations_handled: int (default 0)
    avg_response_time_seconds: float (nullable)
    last_active_at: timestamp
    
    created_at: timestamp
    
    # Retention: Keep indefinitely (employee data)
```

### Retention Summary
| Model | Retention Policy | Rationale |
|-------|-----------------|-----------|
| Conversation | Archive after 90 days inactive, delete after 2 years | GDPR compliance, historical analysis |
| Message | Keep for conversation lifetime + 90 days | Audit trail, model training |
| Lead | Indefinite (with export option) | CRM/sales data |
| Attachment | Delete after 180 days | Storage costs, privacy |
| Session | Expire after 24 hours | Temporary state only |
| Agent | Indefinite | Employee records |

---

## Task 6: Bot KPIs & Success Metrics

### Primary KPIs

#### 1. **Lead Conversion Rate**
- **Definition:** % of conversations that result in qualified lead capture (email collected)
- **Target:** ≥25% conversion rate
- **Measurement:** `(Leads Created / Total Conversations) × 100`
- **Dashboard:** Daily trend + weekly average
- **Alert:** If drops below 20% for 3 consecutive days

#### 2. **Lead Quality Score Distribution**
- **Definition:** Breakdown of Hot/Warm/Cold leads
- **Target:** 
  - Hot leads: ≥15%
  - Warm leads: ≥40%
  - Cold leads: ≤45%
- **Measurement:** Count by `lead_score` field
- **Dashboard:** Pie chart + weekly trend

#### 3. **LLM Usage & Cost**
- **Metrics:**
  - Total LLM calls per day
  - Total tokens consumed per day
  - Average tokens per conversation
  - Estimated cost per conversation
- **Targets:**
  - LLM usage: <50% of total messages (prefer canned responses)
  - Cost per conversation: <$0.15
  - Average tokens: <2,000 per conversation
- **Dashboard:** Daily cost tracker, token consumption graph
- **Alert:** If daily cost exceeds $50 or single conversation uses >10K tokens

#### 4. **Human Handoff Rate**
- **Definition:** % of conversations escalated to human agents
- **Target:** 10-20% (sweet spot)
  - <10% = bot might be overconfident
  - >20% = bot needs better training
- **Measurement:** `(Escalated Conversations / Total Conversations) × 100`
- **Dashboard:** Weekly trend + escalation reasons breakdown
- **Alert:** If exceeds 30% for 2 consecutive days

#### 5. **Response Latency**
- **Metrics:**
  - Canned response time: <300ms (p95)
  - LLM response time: <3s (p95)
  - End-to-end user response time: <5s (p95)
- **Targets:**
  - Median: <1s
  - p95: <5s
  - p99: <10s
- **Dashboard:** Latency histogram, real-time p95 tracker
- **Alert:** If p95 exceeds 8s for 10 minutes

---

### Secondary KPIs

#### 6. **User Engagement**
- Messages per conversation (avg)
  - Target: 5-12 messages (indicates engagement without frustration)
- Conversation duration (avg)
  - Target: 3-8 minutes
- Repeat user rate
  - Target: ≥20% of users return within 30 days

#### 7. **Bot Effectiveness**
- Intent detection accuracy
  - Target: ≥85% correct intent classification
  - Measure via manual review of 100 conversations/week
- FAQ resolution rate (no escalation needed)
  - Target: ≥80% of FAQ queries resolved without human
- Project intake completion rate
  - Target: ≥60% of users who start intake flow complete all steps

#### 8. **Technical Performance**
- Webhook processing success rate
  - Target: ≥99.5%
- Database query latency (p95)
  - Target: <100ms
- Redis cache hit rate
  - Target: ≥80%
- Error rate (5xx errors)
  - Target: <0.1%

#### 9. **Business Impact**
- Time to first response (bot vs human baseline)
  - Target: <30 seconds (vs 4 hours human avg)
- Support ticket deflection rate
  - Target: ≥40% of inquiries handled without human intervention
- Lead response time improvement
  - Target: 90% of leads captured within 5 minutes of inquiry

#### 10. **User Satisfaction**
- Feedback score (thumbs up/down after conversation)
  - Target: ≥75% positive
- Escalation request reasons (breakdown)
  - Track: "not helpful", "too slow", "need expert", "prefer human"
- Conversation abandonment rate
  - Target: <25% (users who stop mid-conversation)

---

### KPI Dashboard Structure

```
┌─────────────────────────────────────────────────────┐
│  Dev2Production Bot - Performance Dashboard         │
├─────────────────────────────────────────────────────┤
│  Today  │  This Week  │  This Month  │  [Filters▾]  │
├─────────────────────────────────────────────────────┤
│  📊 PRIMARY METRICS                                  │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │ Conversations│ Leads Created│ Conversion │       │
│  │     47      │      13      │   27.7%   │       │
│  │  ↑ +12%     │   ↑ +8%      │  ↑ +3.2%  │       │
│  └─────────────┴─────────────┴─────────────┘       │
│                                                      │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │ LLM Cost    │ Handoff Rate │  P95 Latency│       │
│  │   $4.32     │    14.9%     │   2.1s     │       │
│  │  ✓ Target   │  ✓ Target    │  ✓ Target  │       │
│  └─────────────┴─────────────┴─────────────┘       │
│                                                      │
│  📈 LEAD QUALITY                                     │
│  [████ 18% Hot] [████████ 45% Warm] [███ 37% Cold] │
│                                                      │
│  💬 RECENT CONVERSATIONS                             │
│  • @john_dev - Project Intake (Warm) - 2m ago       │
│  • @sarah_cto - FAQ: CI/CD - 5m ago                │
│  • @mike_startup - Escalated to Agent - 12m ago    │
│                                                      │
│  ⚠️ ALERTS                                           │
│  • None - All systems normal ✓                      │
└─────────────────────────────────────────────────────┘
```

---

### Monitoring & Alerting Rules

```python
# Alert Configuration
ALERTS = {
    'lead_conversion_drop': {
        'condition': 'conversion_rate < 0.20 for 3 days',
        'severity': 'warning',
        'notify': ['product_team', 'slack_bot_channel']
    },
    'high_llm_cost': {
        'condition': 'daily_llm_cost > $50 OR single_conversation_cost > $2',
        'severity': 'critical',
        'notify': ['engineering_team', 'finance_team']
    },
    'high_handoff_rate': {
        'condition': 'handoff_rate > 0.30 for 2 days',
        'severity': 'warning',
        'notify': ['product_team', 'support_team']
    },
    'latency_spike': {
        'condition': 'p95_latency > 8s for 10 minutes',
        'severity': 'critical',
        'notify': ['engineering_team', 'pagerduty']
    },
    'webhook_failures': {
        'condition': 'webhook_error_rate > 1% for 5 minutes',
        'severity': 'critical',
        'notify': ['engineering_team', 'pagerduty']
    }
}
```

---

## Implementation Checklist for Phase 0

- [ ] **Task 1:** Document bot persona and create response templates
- [ ] **Task 2:** Define and document primary bot objectives
- [ ] **Task 3:** Create canned response library for top 40 queries
- [ ] **Task 4:** Design and validate conversation flow diagrams with stakeholders
- [ ] **Task 5:** Create database schema and set up Alembic migrations
- [ ] **Task 6:** Set up KPI tracking infrastructure (Prometheus + Grafana)

**Next Steps:** Move to Phase 1 - Backend & Infrastructure Setup
