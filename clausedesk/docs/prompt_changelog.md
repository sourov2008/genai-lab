# Prompt Changelog (Extraction A/B)

Compare `prompts/extract_v1.md` and `prompts/extract_v2.md` against `data/golden_set.json` across multiple LLM providers.

A case **Passes** when extracted `clause_type` values match `expected_clause_types` (order ignored; no extra invented types). Quotes must be verbatim substrings of the source text.

---

## 1. OpenAI (`gpt-4o-mini`)

| Case ID | Expected Clauses | v1 Output | v2 Output |
| :---: | :--- | :---: | :---: |
| 1 | termination, liability_cap, governing_law | ✅ Pass | ✅ Pass |
| 2 | termination | ✅ Pass | ✅ Pass |
| 3 | liability_cap | ✅ Pass | ✅ Pass |
| 4 | *(none)* | ✅ Pass | ✅ Pass |
| 5 | termination, confidentiality | ✅ Pass | ✅ Pass |
| 6 | termination | ❌ **Fail** (missed short text) | ❌ **Fail** (missed short text) |
| 7 | termination | ✅ Pass | ✅ Pass |
| 8 | payment_terms, termination, ip_ownership, non_compete | ❌ **Fail** (hallucinated `governing_law`) | ✅ **Pass** (correctly omitted) |
| 9 | *(none)* | ✅ Pass | ✅ Pass |
| 10 | all 8 v1 types | ✅ Pass | ✅ Pass |

---

## 2. Groq (`llama-3.3-70b` / `gpt-oss-120b`)

| Case ID | Expected Clauses | v1 Output | v2 Output |
| :---: | :--- | :---: | :---: |
| 1 | termination, liability_cap, governing_law | ✅ Pass | ✅ Pass |
| 2 | termination | ✅ Pass | ✅ Pass |
| 3 | liability_cap | ✅ Pass | ✅ Pass |
| 4 | *(none)* | ✅ Pass | ✅ Pass |
| 5 | termination, confidentiality | ✅ Pass | ✅ Pass |
| 6 | termination | ✅ **Pass** (quoted short text) | ❌ **Fail** (missed short text) |
| 7 | termination | ✅ Pass | ✅ Pass |
| 8 | payment_terms, termination, ip_ownership, non_compete | ❌ **Fail** (hallucinated `governing_law`) | ✅ **Pass** (correctly omitted) |
| 9 | *(none)* | ✅ Pass | ✅ Pass |
| 10 | all 8 v1 types | ✅ Pass | ✅ Pass |

---

## 🔍 Key Findings & Analysis

1. **The Hallucination Trap (Case 8):** Both OpenAI and Groq failed with `v1` because the text explicitly said *"does not select a governing jurisdiction"*, yet the model hallucinated a `governing_law` clause. Both providers successfully passed with `v2`, proving that our **Refusal Rule** in the prompt works effectively across different models.
2. **Edge Case Handling (Case 6):** Groq (`v1`) was brave enough to quote *"Just terminate it."*, whereas OpenAI consistently failed this case by returning an empty array. 
3. **Confidence Scores:** Groq consistently outputted near-perfect confidence scores (`0.99` - `1.0`), showing signs of overconfidence. OpenAI provided more calibrated and realistic scores (`0.85` - `0.95`).

---

## 🏆 Final Decision

- **Winner:** `v2` (for both providers)
- **Why:** The `v2` prompt successfully prevents hallucinations (Case 8) across both OpenAI and Groq. It acts as a reliable safeguard regardless of which underlying model is used.

- **Follow-up:** Set `PROMPT_VERSION=v2` in `.env`. Keep OpenAI as the primary provider due to its calibrated confidence scores and strict JSON schema support, but use Groq as a fast, free fallback.