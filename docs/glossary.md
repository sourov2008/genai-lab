# ClauseDesk - Master Glossary (W1 to W24)

This glossary contains all the technical terms, architectural concepts, and AI-specific vocabulary covered throughout the 24-week syllabus.

## Module 1 & 2: Foundations, Backend & Core Concepts (W1 - W8)

### 1. Token
**Definition:** The basic unit of text (a word, part of a word, or punctuation) that an LLM reads, processes, and bills for.
**Why it matters:** Models don't read characters or words; they read tokens. Cost and context limits are calculated in tokens.

### 2. Embedding
**Definition:** A numerical vector representation of text that captures its semantic meaning.
**Why it matters:** Used for semantic search, clustering, and RAG to find texts with similar meanings, even if they don't share exact keywords.

### 3. Transformer
**Definition:** The neural network architecture (using attention mechanisms) that powers modern LLMs like GPT and Gemini.
**Why it matters:** It allows models to process all tokens in parallel and understand deep contextual relationships.

### 4. Attention
**Definition:** The mechanism where a model weighs the importance of surrounding words to understand the context of a specific word (e.g., distinguishing "river bank" from "financial bank").
**Why it matters:** It is the core reason why LLMs understand context rather than just looking at words in isolation.

### 5. Context Window
**Definition:** The maximum number of tokens (input + output combined) a model can process in a single request.
**Why it matters:** Everything must fit in this window. Exceeding it causes errors, and larger inputs increase cost and latency.

### 6. Hallucination
**Definition:** When an LLM confidently generates plausible-sounding but factually incorrect or fabricated information.
**Why it matters:** LLMs predict the next token; they don't verify truth. This requires us to use grounding (RAG) and validation.

### 7. System Prompt
**Definition:** The initial set of instructions given to an LLM that dictates its persona, rules, and constraints before the user interacts with it.
**Why it matters:** It is the primary way developers control the model's behavior and safety boundaries.

### 8. Prompt Injection
**Definition:** A security vulnerability where malicious instructions are hidden inside data (like a document) that the LLM processes, causing it to ignore its original instructions.
**Why it matters:** As AI agents get more power (like sending emails), prompt injection becomes a critical security risk.

### 9. PII (Personally Identifiable Information)
**Definition:** Any data that could potentially identify a specific individual (names, emails, SSNs, etc.).
**Why it matters:** Sending unneeded PII to LLM APIs or storing it in logs violates privacy laws (GDPR) and creates security risks.

### 10. ORM (Object-Relational Mapping)
**Definition:** A technique (like SQLAlchemy) that maps Python classes to database tables.
**Why it matters:** It allows developers to interact with databases using Python objects instead of raw SQL, preventing SQL injection and improving maintainability.

### 11. Alembic
**Definition:** A database migration tool for SQLAlchemy.
**Why it matters:** It tracks changes to your database schema over time, ensuring local and production databases stay in sync without losing data.

### 12. Dependency Injection (DI)
**Definition:** A design pattern (used heavily in FastAPI) where components (like DB sessions or User auth) are injected into routes rather than instantiated inside them.
**Why it matters:** It makes code highly testable (by allowing mock overrides) and decouples business logic from infrastructure.

### 13. Pydantic
**Definition:** A data validation library in Python.
**Why it matters:** It guarantees that incoming API data and outgoing LLM JSON outputs match the exact schema expected by the application.

### 14. Async/Await
**Definition:** A programming pattern that allows the server to handle other requests while waiting for a slow operation (like an LLM call or DB query) to finish.
**Why it matters:** Essential for FastAPI performance. Without it, one slow AI request would block all other users.

---

## Module 3 & 4: LLM Integration, UI & Deployment (W9 - W16)

### 15. Temperature
**Definition:** A parameter (0.0 to 1.0+) that controls the randomness of LLM outputs.
**Why it matters:** 0.0 is deterministic (best for data extraction and JSON). Higher values are creative (best for brainstorming or stories).

### 16. Max Tokens
**Definition:** The hard limit on how many tokens the model is allowed to generate in its response.
**Why it matters:** If the output exceeds this limit, it gets truncated (cut off). For JSON extraction, too low of a limit breaks the pipeline.

### 17. Few-Shot Prompting
**Definition:** Providing a few examples of the desired input/output in the prompt.
**Why it matters:** It teaches the model the exact format, tone, or logic you want without needing to fine-tune it.

### 18. JSON Mode / Strict Schema
**Definition:** An API feature (like OpenAI's `strict: true`) that forces the LLM to output valid JSON matching a specific schema.
**Why it matters:** It prevents parsing errors. The LLM cannot invent fields or miss required ones.

### 19. Rate Limit
**Definition:** A restriction on how many requests you can send to an API per minute/day (e.g., 429 Too Many Requests).
**Why it matters:** Exceeding it crashes the app if unhandled. Requires implementing exponential backoff retry logic.

### 20. Retry (with Exponential Backoff)
**Definition:** Automatically re-sending a failed request after waiting a short time, with the wait time increasing after each failure.
**Why it matters:** Handles temporary network glitches or rate limits gracefully without crashing the app.

### 21. Provider Adapter Pattern
**Definition:** An architectural interface (like `LLMProvider`) that wraps different APIs (OpenAI, Groq) behind a single, unified interface.
**Why it matters:** It allows switching from OpenAI to Groq by changing one line in `.env`, without rewriting any business logic.

### 22. Fallback Strategy
**Definition:** Automatically switching to a secondary provider (e.g., Groq) if the primary provider (e.g., OpenAI) fails or hits a rate limit.
**Why it matters:** It ensures high availability. The user doesn't see an error even if OpenAI goes down.

### 23. TTFT (Time to First Token)
**Definition:** The time it takes for the model to generate the very first token of its response.
**Why it matters:** It is the most critical metric for perceived UX in streaming applications. Lower TTFT feels faster.

### 24. Latency
**Definition:** The total time taken from sending a request to receiving the complete response.
**Why it matters:** High latency ruins UX. It dictates whether a task can be synchronous (blocking) or must be asynchronous.

### 25. Human-in-the-Loop (HITL)
**Definition:** A system design where AI outputs are reviewed and approved by a human before taking irreversible actions.
**Why it matters:** Critical for high-stakes domains (like Legal or Healthcare) to prevent AI mistakes from causing harm.

---

## Module 5: Agents, Security & Observability (W17 - W20)

### 26. Agent
**Definition:** An AI system that doesn't just answer questions, but autonomously decides which actions (tools) to take to achieve a goal.
**Why it matters:** It moves AI from passive reading to active problem-solving (e.g., querying a DB, then searching the web).

### 27. ReAct Loop (Reason + Act)
**Definition:** The core loop of an agent: Think -> Call a Tool -> Observe the Result -> Think Again -> Repeat.
**Why it matters:** It allows the LLM to break down complex tasks step-by-step instead of trying to answer everything in one prompt.

### 28. Tool Calling
**Definition:** Giving the LLM a list of Python functions (with JSON schemas) that it is allowed to execute.
**Why it matters:** It connects the LLM to the real world (databases, APIs), allowing it to fetch real data instead of guessing.

### 29. Max-Step Cap
**Definition:** A hard limit on how many times an agent can loop before it is forced to stop.
**Why it matters:** Prevents infinite loops, runaway API costs, and latency spikes if the agent gets confused.

### 30. JWT (JSON Web Token)
**Definition:** A secure, stateless token used to authenticate users.
**Why it matters:** It allows the server to verify who the user is without needing to store session data in memory or a database.

### 31. Password Hashing (Bcrypt)
**Definition:** Converting a plain-text password into a one-way cryptographic hash.
**Why it matters:** Security best practice. If a database is breached, hackers cannot read the actual passwords.

### 32. IDOR (Insecure Direct Object Reference)
**Definition:** A security vulnerability where a user can access another user's data by manipulating an ID in the URL.
**Why it matters:** Requires strict authorization checks (e.g., verifying `user_id` matches the requested resource) to prevent data leaks.

### 33. CI/CD (Continuous Integration)
**Definition:** Automating the testing and deployment of code whenever it is pushed to GitHub.
**Why it matters:** It ensures that broken code never reaches production by automatically running Pytest before a merge.

### 34. pgvector
**Definition:** A PostgreSQL extension that adds a `vector` data type and similarity search operators (like cosine distance).
**Why it matters:** It allows you to store embeddings alongside relational data in Postgres, avoiding the need for a separate vector database.

### 35. Tracing (Observability)
**Definition:** Recording the exact path, latency, and cost of every step an LLM or Agent takes.
**Why it matters:** LLMs are black boxes. Tracing (via Langfuse) reveals exactly where time is spent and how much money each step costs.

### 36. Webhook
**Definition:** A mechanism where an app automatically sends real-time data to another app when an event occurs.
**Why it matters:** It enables automation. For example, sending an alert to n8n immediately when an error happens.

### 37. n8n
**Definition:** An open-source visual workflow automation tool.
**Why it matters:** It handles external logic (like sending emails, scheduling daily reports, or connecting to Google Drive) without cluttering the core AI code.

---

## Module 6: RAG & Finalization (W21 - W24)

### 38. RAG (Retrieval-Augmented Generation)
**Definition:** A technique where relevant documents are retrieved from a database and added to the prompt, so the LLM can answer based on specific data.
**Why it matters:** It solves the context window limit and hallucination by giving the model exact, real-world facts to base its answer on.

### 39. Chunking
**Definition:** The process of breaking large documents into smaller, manageable pieces (chunks) before embedding them.
**Why it matters:** LLMs have limited context windows. Smaller chunks (e.g., 500 tokens) ensure that only the most relevant information is retrieved.

### 40. Cosine Similarity
**Definition:** A mathematical metric used to measure how similar two vectors are by calculating the cosine of the angle between them.
**Why it matters:** It is the standard way to find how closely a user's query matches the documents in a vector database.

### 41. Reranking
**Definition:** A secondary sorting step that uses a more powerful model to re-order the top results retrieved by a vector search.
**Why it matters:** Vector search is fast but sometimes inaccurate. Reranking ensures the absolute best chunks are placed at the top.

### 42. Faithfulness
**Definition:** An evaluation metric measuring whether the AI's answer is entirely grounded in the provided source text, without hallucinating.
**Why it matters:** It proves the RAG system is actually citing facts, rather than just making things up.

### 43. LLM-as-a-Judge
**Definition:** Using a powerful LLM (like GPT-5) to grade the outputs of another, cheaper LLM based on a rubric.
**Why it matters:** It scales evaluation. Humans cannot manually read 1,000 outputs, but an LLM can score them for relevance and accuracy.

### 44. Fine-Tuning
**Definition:** Taking a pre-trained model and training it further on a specific, custom dataset to adapt its behavior.
**Why it matters:** It is powerful for niche tasks, but expensive and easily overrun. Usually, better prompting and RAG are preferred first.