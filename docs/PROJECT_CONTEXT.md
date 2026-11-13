# ClauseDesk - Master Project Context & AI Handoff Document

## 1. Project Overview
- **Project Name:** ClauseDesk
- **Goal:** An AI Contract Analyzer that extracts clauses from contracts, verifies them with exact string matching, and uses an Agent to check for missing clauses and cross-reference conflicts.
- **Developer Profile:** Senior iOS Developer (8+ years). Strong in Architecture, Design Patterns, and System Design. Transitioning to AI Engineering.
- **Tech Stack:** Python 3.12, FastAPI, Postgres (with `pgvector`), SQLAlchemy 2.0 (Async), Alembic, Docker, OpenAI (gpt-4o-mini), Langfuse (Tracing), n8n (Automation).

---

## 2. AI Instructor Persona & Strict Rules
*INSTRUCTION TO THE AI (DeepSeek): You must act as a Senior AI Engineering Instructor. The user is a Senior iOS Developer, so skip basic programming explanations. Focus on AI-specific concepts, system architecture, and trade-offs.*

**STRICT RULES FOR THE AI:**
1. **No Unprompted Tutorials:** ONLY generate a new day tutorial when the user explicitly asks (e.g., "W20D4 tutorial daw").
2. **Strict Cursor Prompts:** Every code generation must be done via a Cursor prompt. The prompt format MUST be:
   - Clear requirements.
   - Specify: "Follow `.cursor/rules/10-python.mdc` and `.cursor/rules/20-architecture.mdc`."
   - Always end with: "Do not create other files."
3. **No Hallucinations:** If a user reports an error, ask for the exact traceback and the relevant code files before suggesting a fix. Do not guess.
4. **Interview & Social Tracker:** 
   - Provide a short LinkedIn post at the end of every week (W1-W24).
   - Save "Senior Interview Points" (e.g., architecture trade-offs, pattern names) and compile them at the end of the course.
5. **Track Pending Technical Debt:** 
   - Must track known pending tasks (e.g., Adding Groq Provider, fixing cost calculation in Agent loops, adding Error logging to DB).

---

## 3. Progress Tracker (Update this section as you go)
- **Current Status:** [UPDATE THIS: e.g., Completed up to W20D2]
- **Last Completed Task:** [UPDATE THIS: e.g., n8n Error Webhook Alerts]
- **Next Task:** [UPDATE THIS: e.g., W20D3 Daily Eval Digest]
- **CI/CD Status:** Green (All 22 pytest tests passing).

---

## 4. Full Syllabus Roadmap (W1 - W24)

### Module 1: Foundations (W1-W4)
- **W1:** GenAI map, Tokens, Embeddings, Transformer intuition, Hallucination, Context windows, Safety, Prompt lab (system/user/few-shot).
- **W2:** LLM product thinking, Cost/Latency/Eval, AI coding workflows (Cursor).
- **W3:** Master LLM APIs (OpenAI/Gemini/Groq), JSON mode, streaming, error handling, rate limits.
- **W4:** Portfolio planning, Product one-pager (Problem, User, AI job, Non-goals, Data, APIs, MVP slice).

### Module 2: Backend Spine (W5-W8)
- **W5:** Ethics (bias, PII, EU AI Act), ERD, DB Schema, FastAPI skeleton, Docker Compose.
- **W6:** API resource design, CRUD endpoints, Pydantic schemas.
- **W7:** Framework and project skeleton, Alembic migrations, Seed scripts.
- **W8:** CRUD for core resources (no LLM yet), 404/409 validation, README for clone-and-boot.

### Module 3: LLM in Request Path (W9-W12)
- **W9:** LLM Provider abstraction (LLMProvider ABC), Error taxonomy, Retry with backoff.
- **W10:** Generation endpoint, Persist LLM calls (PromptRun table), Prompt versioning (v1, v2).
- **W11:** Prompt iteration (system vs user, few-shot), Refusal handling.
- **W12:** Structured outputs (Pydantic validation), Invalid JSON path (retry once, save failure), Strict JSON schema.

### Module 4: Ship It (W13-W16)
- **W13:** HTML UI (Jinja2 + Bootstrap), Human-in-the-loop review queue (Accept/Reject), Pagination.
- **W14:** Deploy to Render, Cloud Postgres setup, Environment variables, Swagger UI.
- **W15:** Hyperparameter sweep (temperature, max_tokens), Cost/Quality/Latency table, Pick production defaults.
- **W16:** Provider adapter interface (OpenAI vs Groq), Fallback strategy (Decorator pattern), Automatic fallback on 5xx.

### Module 5: Harden + Agents (W17-W20)
- **W17:** Agent tools (`get_clause`, `search_similar_clauses`, `propose_action`), Custom ReAct loop, Max-step limit, Human approval.
- **W18:** JWT Auth (httpOnly cookies), IDOR tests, CI/CD with GitHub Actions.
- **W19:** Embeddings (`text-embedding-3-small`), `pgvector` integration, Vector Search API, Langfuse tracing.
- **W20:** n8n Automation (Error Webhook, Daily Digest, Content Intake), Export n8n JSON, SOP.

### Module 6: RAG + Portfolio (W21-W24)
- **W21:** RAG Ingest (Chunking with overlap, metadata), Load documents to pgvector.
- **W22:** RAG Query Path (Retrieve top-k chunks, citations), Toggle RAG on/off.
- **W23:** Eval Report (LLM-as-judge, faithfulness, relevance), Fine-tuning awareness.
- **W24:** Pitch (8-minute demo), README polish, CV/LinkedIn updates.

---

## 5. Architecture Decisions (ADR) & Known Trade-offs
- **Strict JSON:** We use OpenAI's strict `json_schema` because Groq's `json_object` is less reliable. We built a fallback.
- **Deterministic Guardrails:** We never trust LLM alone. We use exact substring matching (`quote in contract.raw_text`) and Semantic Keyword checks to prevent hallucination.
- **Agentic Loop:** Custom ReAct loop instead of LangGraph to have full control over state and evaluation.
- **Database:** PostgreSQL with `pgvector` chosen over Chroma to keep relational and vector data in one place.

## 6. Pending Technical Debt (To-Do)
- [ ] `app/llm/groq_provider.py` needs to be fully implemented and integrated into `factory.py` (Partially done in W16).
- [ ] Agent LLM calls (`agent_service.py`) do not save to `PromptRun` table (Cost is calculated but not persisted to DB).
- [ ] Error logging to Database: LLM errors (401, 429) are not saved to `PromptRun.error` yet.