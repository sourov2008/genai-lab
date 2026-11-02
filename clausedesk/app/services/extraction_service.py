"""LLM clause extraction orchestration."""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm.base import LLMProvider, LLMRequest, Message
from app.llm.errors import LLMBadRequestError
from app.llm.prompt_loader import load_prompt
from app.llm.retry import with_retry
from app.models import Clause, Contract, PromptRun
from app.models.contract import ContractStatus
from app.services.verification_service import verify_clause

logger = logging.getLogger(__name__)


async def extract_clauses_from_contract(
    db: AsyncSession,
    contract: Contract,
    llm: LLMProvider,
) -> list[Clause]:
    """Extract, verify, and persist clauses for one contract.

    Args:
        db: Active async database session.
        contract: Contract whose `raw_text` is sent to the LLM.
        llm: Provider used for completion.

    Returns:
        Newly created `Clause` rows.

    Raises:
        LLMBadRequestError: If the model output is not valid JSON.
    """
    settings = get_settings()
    system_prompt = load_prompt(settings.prompt_version)
    request = LLMRequest(
        messages=[
            Message(role="system", content=system_prompt),
            Message(role="user", content=contract.raw_text),
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    response = await with_retry(lambda: llm.complete(request))
    prompt_run = PromptRun(
        contract_id=contract.id,
        provider=response.provider,
        model=response.model,
        raw_response=response.text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=response.usage.cost_usd,
        latency_ms=response.latency_ms,
        request_id=response.request_id,
    )
    db.add(prompt_run)
    await db.flush()

    text = response.text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
        if text.endswith("```"):
            text = text.removesuffix("```").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMBadRequestError("LLM returned invalid JSON") from exc

    created: list[Clause] = []
    for item in payload.get("clauses", []):
        verified_data = verify_clause(contract, item)
        if verified_data is None:
            continue
        clause = Clause(
            contract_id=contract.id,
            clause_type=verified_data["clause_type"],
            quote=verified_data["quote"],
            confidence=verified_data["confidence"],
            verified=verified_data["verified"],
            status=verified_data["status"],
            prompt_run_id=prompt_run.id,
        )
        db.add(clause)
        created.append(clause)

    contract.status = ContractStatus.READY.value
    await db.commit()
    logger.debug(
        "Extracted %s clauses for contract_id=%s prompt_run_id=%s",
        len(created),
        contract.id,
        prompt_run.id,
    )
    return created
