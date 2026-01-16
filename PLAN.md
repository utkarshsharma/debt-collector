# Debt Collector Voice AI - System Plan

**Last Updated**: 2026-01-17

---

## Overview

Voice AI system for personal finance companies to collect debt across three stages:
1. **Pre-delinquency** - Reminder calls before payment due
2. **Early delinquency** - ~1 week past due
3. **Late delinquency** - ~3+ weeks past due

---

## Technology Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Voice AI Platform** | ElevenLabs Agents | All-in-one: STT + LLM + TTS + call handling |
| **Telephony** | Twilio (via ElevenLabs) | Phone number linked to ElevenLabs agent |
| **SMS** | Twilio SMS API | Agent webhook tool calls Twilio directly |
| **LLM** | GPT-5.2 (via ElevenLabs) | Configured in ElevenLabs agent |
| **Backend** | Python/FastAPI | AI/ML ecosystem, async support |
| **Cloud** | GCP | Better AI/ML services |
| **Database** | Supabase (PostgreSQL) | Managed PostgreSQL, JSONB support |
| **Cache** | Memorystore (Redis) | Sessions, rate limiting |
| **Queue** | Cloud Pub/Sub | Reliable async messaging |
| **Storage** | Cloud Storage (GCS) | Call recordings |

### Architecture Pivot (2026-01-14)
Originally planned custom voice orchestrator with separate STT/LLM/TTS integration.
Pivoted to **ElevenLabs Agents Platform** which handles:
- Twilio phone integration
- Speech-to-text (built-in)
- LLM conversation (GPT-5.2)
- Text-to-speech (ElevenLabs voices)
- Interruption handling
- Call state management

### Estimated Cost Per Call (~3 min)
- ElevenLabs Agent: ~$0.20 (includes STT, LLM, TTS)
- Twilio telephony: $0.042
- Twilio SMS: $0.0079
- **Total: ~$0.25/call**

At 1,000 calls/day = ~$7,500/month

---

## Architecture

### Simplified Design (ElevenLabs Agents)

```
┌─────────────────┐    ┌─────────────────────────────────────┐    ┌─────────────────┐
│  CLIENT API     │    │         ELEVENLABS AGENT            │    │  CALL SCHEDULER │
│  SERVICE        │    │                                     │    │     SERVICE     │
│                 │    │  ┌─────────────────────────────┐    │    │                 │
│ • Debtor CRUD   │    │  │  Debt Collection Agent      │    │    │ • Job queue     │
│ • Campaign CRUD │    │  │  • GPT-5.2 LLM              │    │    │ • TCPA hours    │
│ • Call history  │    │  │  • Built-in STT/TTS         │    │    │ • Retry logic   │
│                 │    │  │  • Twilio phone linked      │    │    │                 │
│ Cloud Run       │    │  │  • send_sms webhook tool    │    │    │ Cloud Run Jobs  │
│                 │    │  │  • end_call system tool     │    │    │                 │
└────────┬────────┘    │  └──────────────┬──────────────┘    │    └────────┬────────┘
         │             │                 │                    │             │
         │             │                 │ (SMS webhook)      │             │
         │             │                 ▼                    │             │
         │             │         Twilio SMS API              │             │
         │             └─────────────────────────────────────┘             │
         │                                                                 │
         └─────────────────────────┬───────────────────────────────────────┘
                                   │
                       ┌───────────▼───────────┐
                       │    Cloud Pub/Sub      │
                       │                       │
                       │ • call.schedule       │
                       │ • call.completed      │
                       │ • call.failed         │
                       │ • webhook.send        │
                       └───────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
       Cloud SQL              Memorystore           Cloud Storage
      (PostgreSQL)             (Redis)                 (GCS)
```

### Key Components

| Component | Description |
|-----------|-------------|
| **ElevenLabs Agent** | Handles entire voice conversation (STT→LLM→TTS) |
| **Twilio Phone** | Linked to agent, handles inbound/outbound calls |
| **SMS Webhook Tool** | Agent calls Twilio SMS API directly during calls |
| **Auth Connection** | Twilio Basic Auth stored securely in ElevenLabs |
| **end_call Tool** | Agent terminates calls automatically when done |

### Repository Structure

```
debt-collector/
├── services/
│   ├── client-api/           # REST API for clients
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── voice-orchestrator/   # Real-time call handling
│   │   ├── src/
│   │   │   ├── twilio/
│   │   │   ├── deepgram/
│   │   │   ├── llm/
│   │   │   └── elevenlabs/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── call-scheduler/       # Background job processing
│       ├── src/
│       ├── Dockerfile
│       └── requirements.txt
│
├── shared/                   # Shared code
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic schemas
│   └── prompts/              # LLM prompts
│
├── infra/                    # Terraform for GCP
│
├── TASKS.md                  # Task tracker
├── PLAN.md                   # This file
└── docker-compose.yml        # Local development
```

---

## Voice Call Flow

### ElevenLabs Agent Handles Everything

```
Debtor ←→ Twilio Phone ←→ ElevenLabs Agent (STT + GPT-5.2 + TTS)
                                    │
                                    ├── send_sms tool → Twilio SMS API
                                    └── end_call tool → Terminate call
```

### Agent Configuration
- **Voice**: ElevenLabs voice (configurable)
- **LLM**: GPT-5.2 (via ElevenLabs)
- **Prompts**: Stage-specific (pre/early/late delinquency)
- **Tools**: send_sms webhook, end_call system tool
- **Dynamic Variables**: debtor_name, company_name, amount_owed, due_date, account_number

### Latency
Handled by ElevenLabs platform - optimized for real-time conversation with built-in interruption handling.

---

## SMS Messaging

### Architecture (Agent-Initiated)
```
ElevenLabs Agent → send_sms webhook tool → Twilio SMS API → Debtor
```

The agent sends SMS **during the call** before ending, based on conversation outcome.

### When SMS is Sent
| Outcome | SMS Content |
|---------|-------------|
| Payment commitment | "Confirms your commitment to pay $X by [date]" |
| Callback scheduled | "We'll call you back as discussed" |
| Dispute raised | "We've noted your concern, team will follow up" |
| Hardship claimed | "Contact info for payment options" |
| General follow-up | "Thank you for speaking with us" |

### When SMS is NOT Sent
- Wrong number confirmed
- Third party answered (not the debtor)
- Debtor explicitly opted out

### Agent Tool Configuration
```python
# SMS webhook tool uses ElevenLabs Auth Connection
{
    "type": "webhook",
    "name": "send_sms",
    "api_schema": {
        "url": "https://api.twilio.com/.../Messages.json",
        "method": "POST",
        "auth_connection": {"auth_connection_id": "..."}
    }
}
```

### No-Call Test (Simulate Conversation)
Test that the agent attempts the `send_sms` tool call without placing any phone calls:
```bash
python scripts/local_testing/simulate_sms_tool.py --to +15551234567 --body "Test SMS from simulation"
```

To actually send the SMS via Twilio (use a test number):
```bash
python scripts/local_testing/simulate_sms_tool.py --to +15551234567 --body "Real SMS from simulation" --real
```

### Files
```
shared/
├── twilio_sms/
│   ├── __init__.py      # Client initialization (for standalone use)
│   └── messages.py      # send_sms() function
├── elevenlabs_integration/
│   └── tools.py         # SMS tool configuration
├── schemas/
│   └── sms.py           # SMSMessage, SMSResponse
└── prompts/
    ├── debt_collection.py  # Includes SMS instructions
    └── sms_templates.py    # Message templates

scripts/
└── add_sms_tool_to_agent.py  # Configure agent with SMS tool
```

---

## Data Model

### Core Tables
| Table | Purpose |
|-------|---------|
| `clients` | Finance companies |
| `debtors` | People who owe money |
| `campaigns` | Call campaigns |
| `campaign_debtors` | Links debtors to campaigns |
| `calls` | Call records with transcripts |
| `prompt_versions` | Versioned LLM prompts |
| `payment_promises` | Promises made during calls |
| `payments` | Actual payments received |

### Key Enums
- `delinquency_stage`: pre_delinquency, early_delinquency, late_delinquency
- `call_outcome`: promised_to_pay, disputed, hardship, hung_up, etc.
- `promise_status`: pending, overdue, partial, fulfilled, broken

---

## Delinquency Stage Prompts

### AI Disclosure Policy
- **Approach**: Disclose only if asked
- If asked "Are you a robot?", answer honestly

### Stage Comparison

| Aspect | Pre-Delinquency | Early (1 week) | Late (3+ weeks) |
|--------|-----------------|----------------|-----------------|
| **Timing** | 3-7 days before | 1-14 days past | 21+ days past |
| **Tone** | Warm, friendly | Concerned, helpful | Serious, professional |
| **Goal** | Reminder | Understand & resolve | Secure commitment |
| **Key phrase** | "Quick reminder" | "Let's figure out what works" | "Important we resolve this" |

### Call State Machine
```
GREETING → VERIFICATION → PURPOSE → NEGOTIATION → COMMITMENT → CLOSING
                ↓                       ↓
           WRONG_NUMBER            HARDSHIP/CALLBACK
```

### Objection Handling
| Objection | Response |
|-----------|----------|
| "I forgot" | Offer payment link or set date |
| "No money" | Ask about partial/payment plan |
| "I dispute" | Document, offer callback |
| "Already paid" | Get details, note for review |
| "Stop calling" | Respect, offer online option |

---

## Client API

### Authentication
- API key in header: `X-API-Key: <key>`
- Rate limit: 1000 req/min

### Core Endpoints
| Resource | Operations |
|----------|------------|
| `/debtors` | CRUD + bulk import |
| `/campaigns` | Create, start/pause, add debtors |
| `/calls` | List, details, manual trigger |
| `/payments` | Report payments |
| `/webhooks` | Configure callbacks |

### Webhook Events
- `call.completed` - Call finished
- `promise.created` - Payment promise made
- `promise.broken` - Promise not fulfilled
- `debtor.opted_out` - No more calls requested

---

## Implementation Phases

### Phase 1: Project Setup ✅
- Monorepo structure
- Docker Compose for local dev
- Shared Python package with schemas

### Phase 2: Voice Agent (ElevenLabs) ✅
- ElevenLabs Agent created with GPT-5.2
- Twilio phone number linked to agent
- Stage-specific prompts (pre/early/late delinquency)
- Test calls working (NL + India)

### Phase 2.5: SMS Messaging ✅ (Pending Verification)
- SMS webhook tool configured with Auth Connection
- Agent prompts include mandatory SMS instructions
- end_call system tool enabled
- **Status**: Configured, needs live call verification

### Phase 3: Client API (In Progress)
- FastAPI + SQLAlchemy ✅
- Database models (5 tables) ✅
- Supabase PostgreSQL connected ✅
- Test data seeded (4 debtors) ✅
- CRUD endpoints (pending)
- Authentication (pending)

### Phase 4: Call Scheduler (Not Started)
- Cloud Pub/Sub integration
- TCPA compliance
- Retry logic

### Phase 5: Integration (Not Started)
- Connect services
- Webhooks
- Testing

### Phase 6: Deployment (Not Started)
- Dockerfiles
- Cloud Run
- Monitoring

---

## Open Questions

1. ~~Technology stack~~ → Decided (ElevenLabs Agents + Twilio)
2. ~~Monolith vs microservices~~ → Microservices
3. ~~Data model~~ → Complete
4. ~~API design~~ → Complete
5. ~~Voice orchestration approach~~ → ElevenLabs Agents (not custom)
6. ~~SMS approach~~ → Agent webhook tool (not separate service)

**Voice + SMS configured. Client API database ready (Supabase). Next: Implement CRUD endpoints.**
