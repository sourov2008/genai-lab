import time
import uuid
from google import genai
from google.genai import types as gtypes
from google.genai import errors as gexc
from .base import LLMProvider, LLMRequest, LLMResponse, LLMUsage, T
from .errors import (
    LLMAuthError, LLMBadRequestError, LLMRateLimitError,
    LLMServerError, LLMTimeoutError, LLMError,
)
from ..config import ModelPricing


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        pricing: ModelPricing | None = None,
        timeout_s: float = 30.0,
    ):
        self._client = genai.Client(
            api_key=api_key,
            http_options={'timeout': int(timeout_s * 1000)}
        )
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

        system_parts = [m.content for m in request.messages if m.role == "system"]
        user_parts = [m.content for m in request.messages if m.role != "system"]
        system = "\n".join(system_parts) if system_parts else None
        contents = "\n".join(user_parts)

        config = gtypes.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            response_mime_type="application/json" if schema else "text/plain",
        )
        if schema is not None:
            config.response_schema = schema
        if system:
            config.system_instruction = system

        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=contents, config=config,
            )
        except gexc.APIError as e:
            code = e.code
            if code in (401, 403):
                raise LLMAuthError(f"gemini: {e.message}") from e
            elif code == 429:
                raise LLMRateLimitError(f"gemini: {e.message}") from e
            elif code == 400:
                raise LLMBadRequestError(f"gemini: {e.message}") from e
            elif code >= 500:
                raise LLMServerError(f"gemini: {e.message}") from e
            else:
                raise LLMError(f"gemini: unexpected APIError {code}: {e.message}") from e
        except Exception as e:
            raise LLMError(f"gemini: unexpected {type(e).__name__}: {e}") from e

        latency_ms = int((time.monotonic() - start) * 1000)
        text = resp.text or ""

        parsed = None
        if schema is not None:
            try:
                parsed = schema.model_validate_json(text)
            except Exception:
                parsed = None

        meta = resp.usage_metadata
        in_tok = getattr(meta, "prompt_token_count", 0) or 0
        out_tok = getattr(meta, "candidates_token_count", 0) or 0
        cost = (
            in_tok / 1_000_000 * self._pricing.input_per_1m
            + out_tok / 1_000_000 * self._pricing.output_per_1m
        )

        return LLMResponse(
            text=text, parsed=parsed, model=self._model, provider="gemini",
            usage=LLMUsage(input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost),
            latency_ms=latency_ms, request_id=request_id,
        )
