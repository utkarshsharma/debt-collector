# Debt Collector Voice AI Agent

We're building an MVP for a voice AI system that helps personal finance companies collect debt through automated outbound phone calls. The AI conducts natural conversations with debtors across three stages of delinquency (pre-delinquency, early, late), handles objections, extracts payment commitments, and reports outcomes to clients via webhooks. We'll scale it up later to add analytics, predictive models, and multi-tenant features. Currently we are building an MVP.

# Technical requirements

1. The system must be microservices-based from the start: three core services (Client API, Voice Orchestrator, Call Scheduler) communicating via Cloud Pub/Sub; no monolithic coupling.

2. The real-time voice loop must be WebSocket-based using Twilio Media Streams: audio flows Twilio → Deepgram (STT) → GPT-5-mini (LLM) → ElevenLabs (TTS) → Twilio; target latency under 1 second end-to-end.

3. The LLM prompt/response is authoritative: the AI's conversation state machine (greeting → verification → negotiation → commitment → closing) must be followed strictly; if the conversation derails, schedule callback rather than force incorrect flow.

4. Speech-to-text must use Deepgram streaming with interim_results for lowest latency; text-to-speech must use ElevenLabs streaming to begin playback before full audio is generated.

5. Interruption handling must stop AI audio immediately when debtor speaks; clear queued audio and resume listening. Never talk over the debtor.

6. The architecture must be modular and future-proof, making it straightforward to add user dashboards, predictive analytics, custom ML models, and horizontal scaling without rewriting core orchestration logic.

7. Backend & orchestration: Python/FastAPI backend for all services; long-running work (call scheduling, webhook delivery) must execute via Cloud Pub/Sub messages, with each step idempotent and restartable.

8. AI & voice (fixed): Conversation must use GPT-5-mini; speech-to-text must use Deepgram; text-to-speech must use ElevenLabs; telephony must use Twilio Media Streams. The backend orchestrates but Twilio handles actual phone connections.

9. Persistence: Use Cloud SQL (PostgreSQL) for all relational data. Persist job/call state, transcripts, outcomes, payment promises, and webhook delivery status. Design for async jobs and retries.

10. Storage: Use Google Cloud Storage (GCS) for call recordings and transcripts. Implement behind a storage interface for potential future migration.

11. Architecture & ops bias: Clean service-layer architecture with isolated external API clients (Twilio, Deepgram, OpenAI, ElevenLabs), explicit data contracts via Pydantic schemas, and a managed-services-first bias (GCP Cloud Run, Cloud SQL, Memorystore). Target container-based deployment.

# Version Roadmap

## MVP (prove the pipeline works)

### Will do
- Microservices architecture (3 services via Cloud Pub/Sub)
- Single outbound call flow: trigger → dial → conversation → outcome
- Twilio Media Streams → WebSocket connection
- Deepgram streaming STT
- GPT-5-mini conversation with state machine
- ElevenLabs streaming TTS
- Interruption handling (stop immediately)
- Persist:
  - call status and outcome
  - full transcript
  - call recording (GCS)
  - payment promises
- REST API for clients:
  - create/list debtors
  - trigger manual call
  - view call history
- Basic webhook delivery (call.completed)
- Three delinquency stage prompts (pre, early, late)
- Docker Compose for local development

### Will NOT do
- User authentication or multi-tenant accounts
- Call scheduling/automation (manual trigger only)
- Campaign management
- Payment tracking/reconciliation
- Advanced analytics or dashboards
- Compliance engine (TCPA calling hours)
- Retry logic for failed calls
- Bulk import
- UI of any kind

---

## V1 (make it usable and robust)

### Will do
- Call Scheduler service (automated outbound campaigns)
- Campaign CRUD and debtor assignment
- TCPA compliance (calling hours by timezone)
- Retry logic with exponential backoff
- Bulk debtor import endpoint
- Payment promise tracking and status updates
- All webhook events (promise.created, promise.broken, debtor.opted_out)
- Better observability (structured logs per call step, failure reasons)
- Prompt versioning for A/B testing
- Opt-out handling (debtor requests no more calls)
- Basic operational controls (retry call, cancel campaign)

### Will NOT do
- User accounts or access control
- Custom dashboards or UI
- Predictive analytics
- Custom ML models
- Real-time monitoring dashboard
- Multi-region deployment
- Advanced compliance (state-by-state rules)

---

## V2 (scale + productize)

### Will do
- User accounts and multi-tenant support
- Client dashboard (campaign stats, call history, promise tracking)
- Predictive models:
  - best time to call
  - likelihood to pay
  - sentiment analysis
- Workflow-style orchestration (step-level retries, resume)
- Horizontal scaling of Voice Orchestrator
- Cost controls and usage quotas per client
- API-first access for integrations
- Advanced analytics (conversion rates, promise fulfillment rates)
- Call sentiment scoring
- AI-generated call summaries

### Will NOT do
- Inbound call handling
- Payment processing
- Custom voice cloning
- Video calls
- Social/community features

---

# One guiding rule (important)

If a feature does not:
- improve call connection rate,
- improve promise-to-payment conversion,
- or reduce cost per successful collection,

it does not belong before V2.
