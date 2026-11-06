# W16: Provider Comparison Decision

Golden-set evaluation at production extraction defaults (`temperature=0.0`, `max_tokens=1024`). Source: `evals/provider_comparison.csv`.

## Comparison

| Provider | Avg Latency (ms) | Avg Out Tokens | JSON Validity |
| :--- | ---: | ---: | ---: |
| Groq | 1441 | 316.5 | 100% |
| OpenAI | 1990 | 105.4 | 100% |

Both providers return valid JSON on every golden case when `response_format` is JSON mode. They differ on **length** and **speed**. Groq finishes about **550 ms** faster on average but emits roughly **3×** as many completion tokens. OpenAI is more concise at a modest latency cost.

## Decision

**Primary provider: OpenAI.** Concise completions cut token cost (output is the expensive side of gpt-4o-mini pricing). Shorter quotes also stay closer to the contract text, which helps exact-match verification. Average latency of ~2.0 s is acceptable for interactive extract-and-review. Production `.env` / Render should keep `LLM_PROVIDER=openai`.

**Fallback provider: Groq.** Lower average latency (and a large gap on long case 10: ~2.3 s vs ~5.4 s) makes Groq the high-availability alternative when OpenAI is slow, rate-limited, or down. The extra tokens are the trade-off for that speed.

Because of the `LLMProvider` ABC, switching between these two is a 1-line `.env` change (`LLM_PROVIDER=openai` or `LLM_PROVIDER=groq`). Routers and extraction services do not import either SDK.
