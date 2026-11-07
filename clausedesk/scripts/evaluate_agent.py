"""Run a small set of compliance-agent scenarios against the database."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.llm.base import LLMProvider
from app.llm.factory import make_llm_provider
from app.models import Contract
from app.services.agent_service import run_compliance_check

logger = logging.getLogger(__name__)

SCENARIOS: list[dict] = [
    {
        "id": 1,
        "description": "Contract with missing clauses",
        "expected_tool_calls": [
            "get_clause",
            "search_similar_clauses",
            "propose_action",
        ],
        "expected_status": "success",
    },
    {
        "id": 54,
        "description": "Contract with valid clauses",
        "expected_tool_calls": ["get_clause"],
        "expected_status": "success",
    },
    {
        "id": 2,
        "description": "Contract with cross-reference conflict",
        "expected_tool_calls": ["get_clause", "propose_action"],
        "expected_status": "success",
    },
]


async def evaluate_scenario(
    db: AsyncSession,
    llm: LLMProvider,
    scenario: dict,
) -> dict:
    """Run one scenario against `run_compliance_check`.

    Args:
        db: Active async database session.
        llm: Provider used by the agent loop.
        scenario: Case id, description, and expected status.

    Returns:
        `scenario_id`, `status`, `steps_taken`, and `final_answer`.
    """
    result = await db.execute(select(Contract).where(Contract.id == scenario["id"]))
    contract = result.scalar_one_or_none()
    if contract is None:
        return {
            "scenario_id": scenario["id"],
            "status": "contract_not_found",
            "steps_taken": 0,
            "final_answer": f"Contract {scenario['id']} not found",
        }
    result = await run_compliance_check(db, contract, llm, max_steps=5)
    return {
        "scenario_id": scenario["id"],
        "status": result["status"],
        "steps_taken": result.get("steps_taken"),
        "final_answer": result.get("final_answer"),
    }


async def main() -> None:
    """Evaluate each scenario and print a console report."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = get_settings()
    llm = make_llm_provider(settings)
    factory = get_session_factory()
    report: list[dict] = []

    async with factory() as db:
        for scenario in SCENARIOS:
            outcome = await evaluate_scenario(db, llm, scenario)
            expected = scenario["expected_status"]
            matched = outcome["status"] == expected
            report.append(
                {
                    "id": scenario["id"],
                    "description": scenario["description"],
                    "result_status": outcome["status"],
                    "steps_taken": outcome["steps_taken"],
                    "expected_status": expected,
                    "hit_expected_status": matched,
                    "final_answer": outcome["final_answer"],
                }
            )
            print(f"ID: {scenario['id']}")
            print(f"Description: {scenario['description']}")
            print(f"Result Status: {outcome['status']}")
            print(f"Steps Taken: {outcome['steps_taken']}")
            print(f"Hit expected status ({expected}): {matched}")
            print("-" * 40)

    logger.info("Agent evaluation report: %s", json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
