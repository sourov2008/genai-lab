# Interview Notes

## How I Hardened the LLM Output (Beyond the Wrapper)

A **dumb LLM wrapper** is: send text to an API, parse whatever comes back, and persist it. That is a demo. It has no opinion about whether the model invented a clause type, paraphrased a quote, or “fixed” a typo. When the JSON is malformed, the process crashes or you retry blindly. When the JSON is valid but legally wrong, you still save it.

A **robust system** treats the model as an untrusted reader. ClauseDesk’s rule is: **LLM reads. Code verifies. Human decides.** The API adapter (`OpenAIProvider` / `GroqProvider`) is only the first hop. Hardening lives *after* the completion: schema, deterministic checks, and a review queue. Switching `LLM_PROVIDER` does not change those rules.

### Three layers of defense

1. **Strict JSON Schema (OpenAI `strict: true`)**  
   Extraction asks for a closed JSON schema (`additionalProperties: false`, every property required) with `response_format` `json_schema` and `strict: true` on OpenAI. The goal is to stop free-form prose and missing fields from ever reaching the database. If the body still fails `json.loads` or Pydantic validation, we retry once and then fail the contract rather than storing a half-parsed blob.

2. **Deterministic semantic guardrails (keyword checks)**  
   An exact substring in the contract is not enough. After `quote in contract.raw_text`, we require a type-specific keyword in the quote (for termination: `terminat`, `cancel`, `expire`, `lapse`). That blocks the semantic hallucination where OpenAI sees “approved by either party” and labels it `termination`. The keyword is missing, `verified` becomes `False`, and the clause goes to the human review queue. This check is Python, not another prompt, so it does not drift with the model.

3. **Fuzzy matching (`difflib`)**  
   Models often silently correct typos (`liabilty` → `liability`, `termanated` → `terminated`). The “fixed” quote is no longer in the source, so exact match fails. A sliding `SequenceMatcher` window can still score similarity above `0.90`. We **log** that near-match but keep `verified = False` so the row is never auto-accepted. The reviewer sees the contract’s actual wording, not the model’s cleanup.

`auto_accepted` is allowed only when `verified` is true **and** confidence is at least `0.7`. Everything else is `review` or `rejected` after a human action. We never auto-approve on model confidence alone.

This architecture is essential for LegalTech because the product has **zero tolerance for hallucination**. A wrong clause type, a paraphrased quote, or a polished typo is not a UX issue; it is a false citation. Wrappers optimize for “the model answered.” ClauseDesk optimizes for “the quote is in the contract, the type is justified by the words on the page, and a person still signs off.” That is the only standard that belongs next to a commercial agreement.
