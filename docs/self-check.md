# ClauseDesk - Master Self-Check & Interview Revision

This file contains the core self-check questions for every module completed so far. Use this for weekly revision and interview preparation. Answers are hidden in collapsible blocks so you can test yourself.

## Module 1: Foundations (W1 - W4)

**W1: GenAI Map & Prompts**
1. What is the difference between Generation and Embeddings?
2. Why do we use few-shot prompting?
3. Why does temperature=0.0 not guarantee 100% identical outputs across different runs?

<details>
<summary>Answers</summary>

1. Generation writes text (outputs tokens). Embeddings map text to numbers (vectors) to measure semantic similarity.
2. To show the model the exact format and pattern you want without fine-tuning. It "teaches by example."
3. Because of floating-point non-determinism in GPU architecture and server-side batching. The model is non-deterministic at a micro-level.
</details>

**W2: Cost, Latency, Eval**
1. Why is TTFT (Time to First Token) more important than total latency for UX?
2. If you have a 3,000-token document attached to every request, which part of the cost dominates?
3. What is a "Golden Set" and why is it needed?

<details>
<summary>Answers</summary>

1. Users feel the app is fast if they see the first word quickly (streaming). Total latency matters less if TTFT is low.
2. The input cost (specifically the fixed document block), because it is multiplied by every single request.
3. A curated dataset of test cases (inputs and expected outputs) used to mathematically measure AI performance and prevent regressions.
</details>

**W3 & W4: APIs & Product Planning**
1. Why should you NOT retry a `401 Unauthorized` error, but SHOULD retry a `429 Too Many Requests`?
2. What is a "Non-goal" in a product one-pager?

<details>
<summary>Answers</summary>

1. `401` means your API key is permanently wrong (retrying wastes time). `429` means temporary rate limit (retrying with backoff will succeed).
2. A feature or capability that you explicitly decide NOT to build, to protect the scope and focus of the MVP.
</details>

---

## Module 2: Backend Spine (W5 - W8)

**W5 & W6: Database & FastAPI**
1. Why do we use Dependency Injection (`Depends`) in FastAPI?
2. Why is async/await essential for LLM applications?
3. What is the purpose of Pydantic in our API?

<details>
<summary>Answers</summary>

1. For testability (allowing dependency overrides with mocks) and to decouple infrastructure (DB sessions, Auth) from business logic.
2. LLM calls take 2-10 seconds. Without async, one user's request would block the server from handling other users.
3. To strictly validate incoming JSON data and ensure outgoing API responses match the exact expected schema.
</details>

**W7 & W8: Docker & CRUD**
1. Why do we use Alembic for database migrations?
2. What is the difference between `403 Forbidden` and `404 Not Found` in the context of IDOR (security)?

<details>
<summary>Answers</summary>

1. To track database schema changes over time and ensure local, CI, and production databases have the exact same table structures without data loss.
2. `403` reveals that the resource exists but you can't access it. `404` hides the existence of the resource entirely, which is more secure against hackers guessing IDs.
</details>

---

## Module 3: LLM Integration & Abstraction (W9 - W12)

**W9 & W10: Provider Abstraction & Extraction**
1. What is the benefit of the `LLMProvider` Abstract Base Class?
2. What does the `PromptRun` database table store, and why?

<details>
<summary>Answers</summary>

1. It allows switching from OpenAI to Groq by changing one `.env` variable, without rewriting the application logic (Factory pattern).
2. It stores the exact input tokens, output tokens, cost, latency, and raw response for every LLM call. It is crucial for Observability and debugging.
</details>

**W11 & W12: Prompt Iteration & Strict JSON**
1. What is "Refusal handling" in prompt engineering?
2. Why does `max_tokens=256` cause failures in a JSON extraction pipeline?

<details>
<summary>Answers</summary>

1. Instructing the model to explicitly say "I don't know" or return an empty array `{"clauses": []}` if the information is missing, instead of hallucinating.
2. If the JSON response requires 300 tokens, setting the limit to 256 will truncate the output, resulting in invalid JSON that crashes the parser.
</details>

---

## Module 4: Ship It & UI (W13 - W16)

**W13 & W14: UI, HITL & Deployment**
1. What is a "Semantic Keyword Guardrail" and why did we add it?
2. Why must you rewrite Render's `postgres://` URL to `postgresql+asyncpg://`?

<details>
<summary>Answers</summary>

1. A deterministic code check. Even if the LLM is confident, we check if the quote actually contains expected keywords (e.g., "terminat"). We added it to catch OpenAI hallucinating "approved" as a termination clause.
2. SQLAlchemy requires the explicit `asyncpg` driver declaration to use asynchronous database connections.
</details>

**W15 & W16: Hyperparameters & Providers**
1. Does increasing Temperature increase Latency? Why?
2. In our comparison, why did OpenAI win over Groq despite Groq being faster?

<details>
<summary>Answers</summary>

1. No. Latency is determined by the number of output tokens generated (autoregressive). Temperature only affects randomness, not token count.
2. Groq (using the open-weight model) was 3x more verbose. It generated 3x more tokens, which means it would cost 3x more at scale.
</details>

---

## Module 5: Agents, Security & Observability (W17 - W20)

**W17: Agents & ReAct Loop**
1. What is the difference between a "Workflow" and an "Agent"?
2. Why did we implement a "Max-Step Cap" and "Human-in-the-Loop" (`propose_action`)?

<details>
<summary>Answers</summary>

1. A workflow is deterministic (fixed steps). An agent uses an LLM to dynamically decide which tool to call next.
2. To prevent infinite loops (which cost money) and to prevent the AI from taking irreversible actions (like rejecting a contract) without human approval.
</details>

**W18 & W19: Security, CI & Vectors**
1. Why store JWT in `httpOnly` cookies instead of `localStorage`?
2. What does `pgvector` do, and why is it better than a separate Vector DB for us?
3. What is the difference between `cosine_similarity` (in Python) and `cosine_distance` (in SQL)?

<details>
<summary>Answers</summary>

1. `localStorage` is accessible by JavaScript, making it vulnerable to XSS attacks. `httpOnly` cookies are invisible to JS.
2. It adds vector similarity search directly inside PostgreSQL. It avoids adding a new infrastructure component (like Chroma) since we already use Postgres.
3. Similarity measures how close they are (1.0 is identical). Distance measures how far they are (0.0 is identical). SQL uses `ORDER BY distance ASC`.
</details>

**W20: Automation (n8n)**
1. Why is n8n used instead of writing the automation logic inside FastAPI?
2. How does n8n know when an error occurs in FastAPI?

<details>
<summary>Answers</summary>

1. Separation of concerns. FastAPI handles the core AI logic. n8n handles external tasks like scheduling daily emails, reading Google Drive, and triggering alerts.
2. FastAPI sends an HTTP POST request (Webhook) to n8n with the error details the moment the error occurs.
</details>