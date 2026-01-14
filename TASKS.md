# Debt Collector Voice AI - Task Tracker

**Last Updated**: 2026-01-14

---

## Current Status

**Phase**: Phase 2.5 (SMS Messaging)
**Next Action**: Implement SMS sending capability

---

## Completed Tasks

### Planning & Design
- [x] Define project requirements and scope
- [x] Choose technology stack
  - Twilio (telephony)
  - Deepgram (STT)
  - GPT-5-mini (LLM)
  - ElevenLabs (TTS)
  - Python/FastAPI (backend)
  - GCP (cloud)
- [x] Design high-level architecture
- [x] Choose microservices pattern (3 services + Cloud Pub/Sub)
- [x] Design real-time voice loop (WebSocket-based)
- [x] Design data model (PostgreSQL schema)
- [x] Design delinquency stage prompts (3 stages)
- [x] Design REST API for clients
- [x] Design webhook system

---

## Pending Tasks

### Phase 1: Project Setup
- [x] Initialize monorepo structure
- [ ] Set up GCP project
- [x] Configure development environment
- [x] Set up Docker Compose for local dev
- [x] Create shared Python package structure (13 tests passing)
- [x] Create factory classes for mock data generation (10 tests passing)
- [x] Create seed script for test data (scripts/seed_data.py)

### Phase 2: Voice Agent (ElevenLabs)
- [x] Set up ElevenLabs SDK and client
- [x] Create ElevenLabs agent via API (GPT-5.2)
- [x] Link Twilio phone number to agent
- [x] Implement test_call.py script
- [x] Test end-to-end outbound calls (NL + India)
- [x] Add skip-verification flag for testing
- [x] Create stage-specific prompts (pre/early/late delinquency)

### Phase 2.5: SMS Messaging
- [ ] Add Twilio SDK dependency
- [ ] Create twilio_sms module (client + messages)
- [ ] Add SMS schemas (SMSMessage, SMSResponse)
- [ ] Create SMS templates (reminder, confirmation, follow-up)
- [ ] Build test_sms.py script
- [ ] Test end-to-end SMS sending

### Phase 3: Client API Service
- [ ] Set up FastAPI project structure
- [ ] Implement database models (SQLAlchemy)
- [ ] Implement debtor CRUD endpoints
- [ ] Implement campaign endpoints
- [ ] Implement call history endpoints
- [ ] Implement bulk import endpoint
- [ ] Implement authentication (API keys)

### Phase 4: Call Scheduler Service
- [ ] Implement job queue with Cloud Pub/Sub
- [ ] Implement TCPA compliance checker (calling hours)
- [ ] Implement timezone handling
- [ ] Implement retry logic with backoff
- [ ] Implement campaign executor

### Phase 5: Integration & Testing
- [ ] Connect all services via Pub/Sub
- [ ] Implement webhook delivery
- [ ] End-to-end testing
- [ ] Load testing

### Phase 6: Deployment
- [ ] Create Dockerfiles for each service
- [ ] Set up Cloud Run deployments
- [ ] Configure Cloud SQL (PostgreSQL)
- [ ] Configure Memorystore (Redis)
- [ ] Set up monitoring and logging

---

## Blockers & Notes

*None currently*

---

## Quick Reference

| Service | Purpose | Status |
|---------|---------|--------|
| ElevenLabs Agent | Voice AI (STT + LLM + TTS) | Working |
| twilio_sms | SMS messaging | Planned |
| client-api | REST API for finance companies | Not started |
| call-scheduler | Background job processing | Not started |

---

## Session Log

### 2026-01-14
- Pivoted from custom voice orchestrator to ElevenLabs Agents Platform
- Set up ElevenLabs SDK and created debt collection agent (GPT-5.2)
- Linked Twilio phone number (+3197010225408) to ElevenLabs agent
- Created test_call.py script for outbound calls
- Successfully tested calls to Netherlands and India
- Added skip-verification flag for testing
- Created stage-specific prompts (pre/early/late delinquency)
- Fixed ElevenLabs content policy compliance (removed legal action language)
- Planned SMS messaging capability (Phase 2.5)

### 2026-01-13
- Initial planning session
- Completed full architecture design
- Technology stack finalized
- Data model designed
- API designed
- Prompts designed
- Started implementation:
  - Created monorepo folder structure
  - Created shared Python package with Pydantic schemas (13 tests passing)
  - Set up Docker Compose (PostgreSQL, Redis, service definitions)
  - Created factory classes for mock data generation (10 tests passing)
  - Created seed script (scripts/seed_data.py) for 10-20 mock debtors
  - Total: 23 tests passing
