"""LLM clause extraction orchestration."""

from __future__ import annotations

import logging

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.llm.base import LLMProvider, LLMRequest, Message
from app.llm.prompt_loader import load_prompt
from app.llm.retry import with_retry
from app.models import Clause, Contract, PromptRun
from app.models.contract import ContractStatus
from app.schemas.extraction import ExtractionResult
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
        HTTPException: 500 if the model output fails `ExtractionResult` validation.
    """
    settings = get_settings()
    system_prompt = load_prompt(settings.prompt_version)
    schema = ExtractionResult.model_json_schema()
    schema["additionalProperties"] = False
    if settings.llm_provider == "groq":
        response_format: dict = {"type": "json_object"}
    else:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "extraction",
                "strict": True,
                "schema": schema,
            },
        }
    request = LLMRequest(
        messages=[
            Message(role="system", content=system_prompt),
            Message(role="user", content=contract.raw_text),
        ],
        response_format=response_format,
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
        parsed_data = ExtractionResult.model_validate_json(text)
    except ValidationError as exc:
        prompt_run.error = f"Invalid JSON: {exc}"
        contract.status = ContractStatus.FAILED.value
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail="LLM output validation failed",
        ) from exc

    prompt_run.parsed_json = parsed_data.model_dump()
    created: list[Clause] = []
    raw_clauses = parsed_data.clauses
    if not raw_clauses:
        logger.info("No clauses found for contract %s", contract.id)
    for item in raw_clauses:
        verified_data = verify_clause(contract, item.model_dump())
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
