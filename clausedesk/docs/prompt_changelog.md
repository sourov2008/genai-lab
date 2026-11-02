# Prompt changelog (extraction A/B)

Compare `prompts/extract_v1.md` and `prompts/extract_v2.md` against `data/golden_set.json`.

Fill **Pass**, **Fail**, or short notes after running:

```bash
python scripts/run_ab_test.py
```

A case **Passes** when extracted `clause_type` values match `expected_clause_types` (order ignored; no extra invented types). Quotes must be verbatim substrings of the source text.

## Results

| Case ID | Expected Clauses | v1 Output (Pass/Fail/Notes) | v2 Output (Pass/Fail/Notes) |
| --- | --- | --- | --- |
| 1 | termination, liability_cap, governing_law | Pass | Pass |
| 2 | termination | Pass | Pass |
| 3 | liability_cap | Pass | Pass (Perfect verbatim quote) |
| 4 | *(none)* | Pass | Pass |
| 5 | termination, confidentiality | Pass | Pass |
| 6 | termination | **Fail** (missed short text) | **Fail** (missed short text) |
| 7 | termination | Pass | Pass |
| 8 | payment_terms, termination, ip_ownership, non_compete | **Fail** (hallucinated `governing_law`) | **Pass** (correctly omitted) |
| 9 | *(none)* | Pass | Pass |
| 10 | all 8 v1 types | Pass | Pass |

## Final Decision
Which prompt is better and why:
- **Winner:** v2

- **Why:** v2 successfully prevented hallucination in Case 8 by strictly adhering to the refusal rule (omitting `governing_law` when it wasn't explicitly defined). While both failed the extreme edge case (Case 6), v2 proved to be more reliable and realistic with its confidence scores (0.88 - 0.95 vs v1's overconfident 1.0).

- **Follow-up:** Set `PROMPT_VERSION=v2` in `.env` for production.
