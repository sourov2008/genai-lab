# Deterministic Verification Layer

ClauseDesk does not trust the LLM as the source of truth. The model **reads**; Python **verifies**; a human **decides**.

LLMs invent clause types, paraphrase quotes, and silently “fix” typos. Those behaviors look helpful until a citation no longer matches the contract. The verification layer in `app/services/verification_service.py` is deterministic: same quote and same contract text always produce the same `verified` flag and review `status`.

The pipeline is:

1. **Exact match** — `quote in contract.raw_text`. If the string is not in the source, it cannot be auto-accepted.
2. **Keyword guardrail** — when the quote *is* an exact substring, it must still contain a type-specific keyword (for example `terminat` or `cancel` for `termination`). This blocks labels that do not belong to the quoted sentence.
3. **Fuzzy match (typos)** — if exact match fails, `difflib.SequenceMatcher` scans a sliding window of the contract. A ratio above `0.90` is logged, but `verified` stays `False` so the row goes to review.

`auto_accepted` is set **only** when `verified` is true **and** `confidence >= 0.7`. Every other outcome is `review`.

---

## Case Study 1 (The Semantic Hallucination)

Text: "This agreement may be approved by either party with a 30-day notice. The total liabilty is capped at $10,000. This contract is governed by the laws of Delaware."

- OpenAI Output: Extracted 'termination' clause. (AI assumed "approved" means termination).
- Groq Output: Missed 'termination' completely.
- Our System's Fix: The Keyword Guardrail checks for "terminat" or "cancel". Since neither is present, the system rejects OpenAI's output and sends it to the Human Review Queue.

Why this matters: an exact substring match would have passed if the model quoted “This agreement may be approved…”. The guardrail still fails the clause because “approved” is not a termination keyword. Groq’s miss is a recall error; OpenAI’s hit is a precision error. Code catches the precision error so it never auto-accepts.

---

## Case Study 2 (The Typo Correction)

Text: "This agreement may be termanated by either party with a 30-day notice. The total liabilty is capped at $10,000. This contract is governed by the laws of Delaware."

- Observation: LLM sometimes fixes "liabilty" to "liability".
- Our System's Fix: Exact substring match fails. The system flags it for review instead of auto-accepting, ensuring the user sees the exact text.

Why this matters: a “helpful” spelling fix makes the quote unfindable in the source. Fuzzy matching may notice that the quote is almost in the contract (ratio > 0.90) and log that, but it still will not auto-accept. The reviewer sees the original `termanated` / `liabilty` wording, not a cleaned version the model invented.

---

## Status routing

| Condition | `verified` | `status` |
| --- | --- | --- |
| Quote in source and keyword present, confidence ≥ 0.7 | `True` | `auto_accepted` |
| Quote in source and keyword present, confidence < 0.7 | `True` | `review` |
| Quote in source but keyword missing (Case Study 1) | `False` | `review` |
| Quote not in source, including typo “fixes” (Case Study 2) | `False` | `review` |
