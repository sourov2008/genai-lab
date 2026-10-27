# AI for Developers — Glossary

## 1. Token
**Definition:** The basic unit of text (a word, part of a word, or punctuation) that an LLM reads, processes, and bills for.
**Why it matters:** Models don't read characters or words; they read tokens. Cost and context limits are calculated in tokens.

## 2. Embedding
**Definition:** A numerical vector representation of text that captures its semantic meaning.
**Why it matters:** Used for semantic search, clustering, and RAG to find texts with similar meanings, even if they don't share exact keywords.

## 3. Transformer
**Definition:** The neural network architecture (using attention mechanisms) that powers modern LLMs like GPT and Gemini.
**Why it matters:** It allows models to process all tokens in parallel and understand deep contextual relationships.

## 4. Attention
**Definition:** The mechanism where a model weighs the importance of surrounding words to understand the context of a specific word (e.g., distinguishing "river bank" from "financial bank").
**Why it matters:** It is the core reason why LLMs understand context rather than just looking at words in isolation.

## 5. Context Window
**Definition:** The maximum number of tokens (input + output combined) a model can process in a single request.
**Why it matters:** Everything must fit in this window. Exceeding it causes errors, and larger inputs increase cost and latency.

## 6. Hallucination
**Definition:** When an LLM confidently generates plausible-sounding but factually incorrect or fabricated information.
**Why it matters:** LLMs predict the next token; they don't verify truth. This requires us to use grounding (RAG) and validation.

## 7. RAG (Retrieval-Augmented Generation)
**Definition:** A technique where relevant documents are retrieved from a database and added to the prompt, so the LLM can answer based on specific data.
**Why it matters:** It solves the context window limit and hallucination by giving the model exact, real-world facts to base its answer on.

## 8. Vector Database
**Definition:** A specialised database that stores embeddings (vectors) to enable fast similarity searches.
**Why it matters:** It allows RAG systems to quickly find the most relevant document chunks when a user asks a question.

## 9. Chunking
**Definition:** The process of breaking large documents into smaller, manageable pieces (chunks) before embedding them.
**Why it matters:** LLMs have limited context windows, and smaller chunks ensure that only the most relevant information is retrieved.

## 10. Cosine Similarity
**Definition:** A mathematical metric used to measure how similar two vectors are by calculating the cosine of the angle between them.
**Why it matters:** It is the standard way to find how closely a user's query matches the documents in a vector database.

## 11. Prompt Injection
**Definition:** A security vulnerability where malicious instructions are hidden inside data (like a document) that the LLM processes, causing it to ignore its original instructions.
**Why it matters:** As AI agents get more power (like sending emails or moving money), prompt injection becomes a critical security risk.

## 12. PII (Personally Identifiable Information)
**Definition:** Any data that could potentially identify a specific individual (names, emails, SSNs, etc.).
**Why it matters:** Sending unneeded PII to LLM APIs or storing it in logs violates privacy laws and creates security risks.

## 13. TTFT (Time to First Token)
**Definition:** The time it takes for the model to generate the very first token of its response after receiving a prompt.
**Why it matters:** It is the most critical metric for user experience (UX) in streaming applications, as users feel the app is faster if TTFT is low.

## 14. Latency
**Definition:** The total time taken from sending a request to receiving the complete response.
**Why it matters:** High latency ruins user experience. It determines whether a feature must be synchronous (blocking) or asynchronous (background).

## 15. Eval (Evaluation)
**Definition:** The systematic process of testing and measuring an AI system's performance, accuracy, and safety.
**Why it matters:** "It looks good" is not proof. Eval uses data (like a Golden Set) to mathematically prove if an AI feature works before production.

## 16. Golden Set
**Definition:** A curated, high-quality dataset of test cases (inputs and expected outputs) used to evaluate an AI model.
**Why it matters:** It acts as the "unit test" for AI, allowing developers to detect regressions when changing prompts or models.

## 17. AI Pair Programmer
**Definition:** An AI assistant (like Cursor or Copilot) that suggests code, refactors, or writes tests in real-time as you type.
**Why it matters:** It dramatically increases coding speed, but requires the human (senior) to constantly review and verify the AI's (junior's) output.

## 18. Hallucinated API
**Definition:** When an AI coding assistant invents a function, library, or parameter that does not actually exist.
**Why it matters:** It is one of the most common AI coding errors. Code must always be run and tested, never blindly trusted.

## 19. Edge Case
**Definition:** Unusual or extreme inputs that fall outside normal operating parameters (e.g., empty files, `None` values, massive inputs).
**Why it matters:** AI almost always forgets edge cases. If humans don't test them, production bugs will occur.

## 20. Verification Loop
**Definition:** A 5-step process for handling AI-generated code: Read the diff, Run it, Test happy path, Test edge cases, Check security.
**Why it matters:** It is the only way to safely use AI for coding without introducing hidden bugs or security vulnerabilities.

## 21. Diff Review
**Definition:** The act of reviewing the exact line-by-line changes (additions and deletions) proposed by an AI.
**Why it matters:** Accepting AI changes without reviewing the diff can accidentally delete important code or introduce logic errors.

## 22. Autocomplete (AI Mode)
**Definition:** A mode where the AI suggests the next line or block of code in gray text as you type.
**Why it matters:** Best for boilerplate and repetitive tasks; dangerous for complex logic or security-sensitive code.

## 23. Inline Edit (AI Mode)
**Definition:** A mode where you select a block of existing code and ask the AI to modify or refactor it in place.
**Why it matters:** Ideal for quick, localized changes without leaving the current file.

## 24. System Prompt
**Definition:** The initial set of instructions given to an LLM that dictates its persona, rules, and constraints before the user interacts with it.
**Why it matters:** It is the primary way developers control the model's behavior and safety boundaries.

## 25. JSON Mode
**Definition:** A feature in LLM APIs that guarantees the model will output a valid JSON object instead of plain text.
**Why it matters:** It is essential for connecting LLMs to code, as applications can reliably parse structured JSON data.
