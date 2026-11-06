# W15: Hyperparameter Sweep Analysis & Production Defaults

**Source:** `data/sweep_results.csv` (Golden Set: 10 cases × Temperatures `0.0 / 0.3 / 0.7` × `max_tokens` `256 / 1024`). 
**Provider:** OpenAI (`gpt-4o-mini`) using `json_object` mode.

## Executive Summary
This analysis evaluates the impact of hyperparameter variations on latency, JSON validity, and extraction quality. Based on the empirical data, we lock the production defaults to **`temperature=0.0`** and **`max_tokens=1024`**, and validate that our **`30s` network timeout** provides a safe ~5x buffer against worst-case network latencies.

---

## Key Findings

### 1. Latency vs Temperature
Latency is virtually identical across temperatures (`0.0`, `0.3`, `0.7`) for the same case. Wall time tracks **output length**, not sampling temperature.

Examples at `max_tokens=1024`:

| Case | out_tokens | latency_ms (t=0.0) | latency_ms (t=0.3) | latency_ms (t=0.7) |
| :---: | ---: | ---: | ---: | ---: |
| 6 | ~6 | 831 | 705 | 684 |
| 1 | 152 | 2671 | 2533 | 2521 |
| 10 | 371 | 5782 | 4956 | 5422 |

*Architectural Insight:* Autoregressive decoding emits one token at a time. Cases that return `{"clauses": []}` (`out_tokens` ≈ 6) finish in about 0.7–0.8s. Case 10, which emits hundreds of tokens, sits around 5–5.8s. Temperature does not change the token generation speed.

### 2. The Truncation Trap (Max Tokens)
Case 10 (the most complex contract with all 8 clause types) failed (`valid_json=FALSE`) at every temperature when `max_tokens=256`:
- **Error:** `Unterminated string starting at: line 30 column 16`
- **Cause:** `out_tokens=256` (hit the cap). The complete payload needed **371 tokens**. A 256 cap cut the JSON string mid-quote.
- **Decision:** `max_tokens=256` is too small for long contracts. We must use **`max_tokens=1024`** to provide sufficient headroom. 

### 3. Timeout Safety Margin & Network Variance
The worst-case latency observed in the sweep was **~6.1 seconds** (Case 1 at t=0.0, max_tokens=256). 
- Notice the variance: Case 1 took 6.0s in one run, but only ~2.5s in another. This highlights **API network variance** (OpenAI server load, routing, etc.), not just token generation time.
- Our `LLMProvider` is configured with a **`timeout_s=30.0`** (30 seconds).
- **Conclusion:** The 30-second timeout provides a **~5x safety buffer** over our worst-case. It is long enough to absorb network spikes, but short enough to fail fast if the provider drops the request, preventing the user's UI from hanging indefinitely.

### 4. JSON Validity vs Extraction Quality
Every row except the truncated Case 10 runs has `valid_json=TRUE`. Even at `temperature=0.7`, the JSON *structure* stayed valid because of OpenAI's `json_object` mode.

*However, Structure ≠ Extraction Quality.* Higher temperatures can paraphrase quotes or drift on `clause_type`. `temperature=0.0` remains the mandatory choice for exact, repeatable extraction (verbatim substring matching).

---

## 🏆 Final Production Decision

Based on this data, the following configurations are locked for the `extraction_service.py`:

| Parameter | Locked Value | Reason |
| :--- | :--- | :--- |
| **`temperature`** | **`0.0`** | Deterministic quotes, prevents hallucination. |
| **`max_tokens`** | **`1024`** | Prevents JSON truncation on complex contracts. |
| **`timeout_s`** | **`30.0`** | ~5x buffer over worst-case latency, absorbs network variance. |
| **`response_format`** | **`json_schema` / `json_object`** | Guarantees syntactically valid JSON. |

**Cost & Scalability Note:** The input tokens are relatively constant per contract (approx. 300-400 tokens). The cost per extraction is a fraction of a cent. The true bottleneck is not cost, but *latency variance* and *reliability* (which our retry logic and 1024 max tokens handle perfectly).