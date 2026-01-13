# Debt Collector Voice AI - System Plan

**Last Updated**: 2026-01-13

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
| **Telephony** | Twilio | Best docs, largest ecosystem |
| **Speech-to-Text** | Deepgram | Lowest latency (~100ms), streaming |
| **LLM** | GPT-5-mini | Fast, cost-effective |
| **Text-to-Speech** | ElevenLabs | Most natural voice |
| **Backend** | Python/FastAPI | AI/ML ecosystem, async support |
| **Cloud** | GCP | Better AI/ML services |
| **Database** | Cloud SQL (PostgreSQL) | Relational, JSONB support |
| **Cache** | Memorystore (Redis) | Sessions, rate limiting |
| **Queue** | Cloud Pub/Sub | Reliable async messaging |
| **Storage** | Cloud Storage (GCS) | Call recordings |

### Estimated Cost Per Call (~3 min)
- Twilio: $0.042
- Deepgram: $0.013
- GPT-5-mini: ~$0.01
- ElevenLabs: $0.15
- **Total: ~$0.22/call**

At 1,000 calls/day = ~$6,600/month

---

## Architecture

### Microservices Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  CLIENT API     │    │     VOICE       │    │  CALL SCHEDULER │
│  SERVICE        │    │  ORCHESTRATOR   │    │     SERVICE     │
│                 │    │                 │    │                 │
│ • Debtor CRUD   │    │ • Twilio WS     │    │ • Job queue     │
│ • Campaign CRUD │    │ • Deepgram STT  │    │ • TCPA hours    │
│ • Call history  │    │ • GPT-5 LLM     │    │ • Retry logic   │
│                 │    │ • ElevenLabs TTS│    │                 │
│ Cloud Run       │    │ Cloud Run       │    │ Cloud Run Jobs  │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
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

## Real-Time Voice Loop

### Connection Type
- **WebSocket-based** (Twilio Media Streams)
- **Interruption handling**: Stop immediately when debtor speaks

### Call Flow

```
Debtor → Twilio → Server → Deepgram (STT) → GPT-5 (LLM) → ElevenLabs (TTS) → Twilio → Debtor
```

### Latency Budget (Target: <1 second)
| Stage | Target |
|-------|--------|
| Network | 50ms |
| Deepgram STT | 200ms |
| GPT-5-mini | 300ms |
| ElevenLabs TTS | 200ms |
| Buffer | 250ms |
| **Total** | **<1000ms** |

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

### Phase 1: Project Setup
- Monorepo structure
- GCP project
- Docker Compose for local dev

### Phase 2: Voice Orchestrator MVP
- Twilio WebSocket
- Deepgram streaming
- GPT-5 conversation
- ElevenLabs TTS
- State machine
- Single call test

### Phase 3: Client API
- FastAPI + SQLAlchemy
- All CRUD endpoints
- Authentication

### Phase 4: Call Scheduler
- Cloud Pub/Sub integration
- TCPA compliance
- Retry logic

### Phase 5: Integration
- Connect services
- Webhooks
- Testing

### Phase 6: Deployment
- Dockerfiles
- Cloud Run
- Monitoring

---

## Open Questions

1. ~~Technology stack~~ → Decided
2. ~~Monolith vs microservices~~ → Microservices
3. ~~Data model~~ → Complete
4. ~~API design~~ → Complete

**All planning complete. Ready to build.**
