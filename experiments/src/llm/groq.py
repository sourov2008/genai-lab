# src/llm/groq.py
import time
import uuid
from groq import (
    AsyncGroq,
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
)
from .base import LLMProvider, LLMRequest, LLMResponse, LLMUsage, T
from .errors import (
    LLMAuthError, LLMBadRequestError, LLMRateLimitError,
    LLMServerError, LLMTimeoutError, LLMError,
)
from ..config import ModelPricing


class GroqProvider(LLMProvider):
    """
    Uses the official `groq` SDK.

    Capability note:
      - response_format={"type": "json_object"} supported
      - Strict JSON schema: NOT supported on all Groq models
      - So we inject schema into system prompt (portable fallback)
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        pricing: ModelPricing | None = None,
        timeout_s: float = 30.0,
    ):
        self._client = AsyncGroq(api_key=api_key, timeout=timeout_s)
        self._model = model
        self._pricing = pricing or ModelPricing()

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return await self._call(request, schema=None)

    async def complete_json(
        self, request: LLMRequest, schema: type[T]
    ) -> LLMResponse[T]:
        return await self._call(request, schema=schema)

    async def _call(
        self, request: LLMRequest, schema: type[T] | None
    ) -> LLMResponse:
        request_id = uuid.uuid4().hex[:12]
        start = time.monotonic()

        messages = [m.model_dump() for m in request.messages]

        kwargs = {
            "model": self._model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if schema is not None:
            kwargs["response_format"] = {"type": "json_object"}
            # Groq strict-schema support varies by model — inject schema
            kwargs["messages"] = [
                {
                    "role": "system",
                    "content": (
                        f"You MUST output valid JSON matching this schema: "
                        f"{schema.model_json_schema()}"
                    ),
                },
                *messages,
            ]

        try:
            raw = await self._client.chat.completions.create(**kwargs)
        except APIStatusError as e:
            self._translate_status(e)
            raise  # unreachable
        except APITimeoutError as e:
            raise LLMTimeoutError(f"groq: {e}") from e
        except APIConnectionError as e:
            raise LLMTimeoutError(f"groq: {e}") from e

        latency_ms = int((time.monotonic() - start) * 1000)
        text = raw.choices[0].message.content or ""
        usage = raw.usage
        in_tok = usage.prompt_tokens if usage else 0
        out_tok = usage.completion_tokens if usage else 0
        cost = (
            in_tok / 1_000_000 * self._pricing.input_per_1m
            + out_tok / 1_000_000 * self._pricing.output_per_1m
        )

        parsed = None
        if schema is not None:
            try:
                parsed = schema.model_validate_json(text)
            except Exception:
                parsed = None

        
        return LLMResponse(
            text=text, parsed=parsed, model=self._model, provider="groq",
            usage=LLMUsage(input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost), # <--- এভাবে নামসহ দাও
            latency_ms=latency_ms, request_id=request_id,
        )

    def _translate_status(self, e: APIStatusError) -> None:
        status = e.status_code
        if status in (401, 403):
            raise LLMAuthError(f"groq: {e.message}") from e
        if status == 429:
            retry_after = None
            if e.response and "retry-after" in e.response.headers:
                try:
                    retry_after = float(e.response.headers["retry-after"])
                except ValueError:
                    pass
            raise LLMRateLimitError(
                f"groq: {e.message}", retry_after_s=retry_after,
            ) from e
        if 400 <= status < 500:
            raise LLMBadRequestError(f"groq: {e.message}") from e
        if status >= 500:
            raise LLMServerError(f"groq: {e.message}") from e
        raise LLMError(f"groq: unexpected {status}")
