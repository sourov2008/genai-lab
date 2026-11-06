# Architecture Decision Record: LLM Provider Selection

Golden-set evaluation at production extraction defaults (`temperature=0.0`, `max_tokens=1024`). Metrics: `evals/provider_comparison.csv`.

## Comparison

| Provider | Model | Avg Latency (ms) | Avg Out Tokens | JSON Validity |
| :--- | :--- | ---: | ---: | ---: |
| Groq | `openai/gpt-oss-120b` | 1441 | 316.5 | 100% |
| OpenAI | `gpt-4o-mini` | 1990 | 105.4 | 100% |

## Model & Instruction-Following Differences

The Groq provider is running `openai/gpt-oss-120b` (an open-weight model). It generated about **3× more tokens** (more verbose) than the proprietary OpenAI `gpt-4o-mini` API (316.5 vs 105.4 average completion tokens). OpenAI stayed concise, which lowers output cost and keeps quotes closer to the contract text.

Both achieved **100% JSON validity**. That comes from our structured output contract (`json_object` / strict JSON schema), not from either model being inherently better at free-form JSON.

## Decision

- **Primary Provider: OpenAI (`gpt-4o-mini`).** Chosen for concise output, lower token cost at scale, and high precision.
- **Fallback Provider: Groq (`openai/gpt-oss-120b`).** Chosen for ultra-low latency to handle OpenAI rate limits or downtime (about 550 ms faster on average; much faster on long generations).

## Implementation

Because of the `LLMProvider` adapter interface and the Factory pattern (`make_llm_provider`), switching between these two in production is a 1-line `.env` change (`LLM_PROVIDER=openai` or `LLM_PROVIDER=groq`). Routers and extraction services never import the vendor SDKs.
