"""Tool-using compliance agent that checks a contract against playbook rules."""

from __future__ import annotations

import json
import logging

from langfuse import Langfuse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from langfuse.decorators import observe
except ImportError:
    from langfuse import observe

from app.core.config import get_settings
from app.llm.base import LLMProvider, LLMRequest, Message
from app.models import Contract
from app.services.agent_tools import (
    TOOL_SCHEMAS,
    flag_for_review,
    get_clause,
    propose_action,
    search_similar_clauses,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an autonomous legal compliance AI agent. Your job is to check "
    "this contract using the provided tools. Think step by step. If you find "
    "a missing clause or a conflict, you MUST immediately use the "
    "`flag_for_review` tool to flag it. Do NOT ask the user for permission. "
    "Act autonomously. If you decide a contract must be rejected or approved, "
    "you MUST use `propose_action`. Do NOT assume the action is complete until "
    "you get a pending_approval response. Once you have taken the necessary "
    "actions, provide a final summary of what you did. CRITICAL: Review your "
    "previous messages. Do NOT call the same tool with the exact same "
    "arguments twice. If a clause is missing, do not try to flag a "
    "non-existent clause ID; instead, proceed to propose an action to reject "
    "or review the entire contract."
)


def _tool_arguments(tool_call: dict) -> dict:
    """Parse tool-call arguments from a JSON string or dict."""
    raw = tool_call.get("arguments")
    function = tool_call.get("function")
    if raw is None and isinstance(function, dict):
        raw = function.get("arguments")
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Invalid tool arguments JSON: %s", raw)
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


async def _execute_tool(db: AsyncSession, name: str, args: dict) -> dict | list[dict]:
    """Dispatch a named tool to the matching `agent_tools` function."""
    if name == "get_clause":
        return await get_clause(db, **args)
    elif name == "search_similar_clauses":
        return await search_similar_clauses(db, **args)
    elif name == "flag_for_review":
        return await flag_for_review(db, **args)
    elif name == "propose_action":
        return await propose_action(db, **args)
    return {"error": f"Unknown tool: {name}"}


def _langfuse_client() -> Langfuse:
    """Return a Langfuse client that no-ops when keys are missing."""
    settings = get_settings()
    enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)
    return Langfuse(
        public_key=settings.langfuse_public_key or None,
        secret_key=settings.langfuse_secret_key or None,
        tracing_enabled=enabled,
    )


def _start_tool_span(langfuse: Langfuse, tool_name: str):
    """Open a current span for one tool call (v4 `start_as_current_span` or v5)."""
    start_span = getattr(langfuse, "start_as_current_span", None)
    if callable(start_span):
        return start_span(name=f"tool_{tool_name}")
    return langfuse.start_as_current_observation(
        name=f"tool_{tool_name}",
        as_type="tool",
    )


@observe(name="agent_compliance_check")
async def run_compliance_check(
    db: AsyncSession,
    contract: Contract,
    llm: LLMProvider,
    max_steps: int = 5,
) -> dict:
    """Run a bounded tool-calling loop over one contract.

    Args:
        db: Active async database session.
        contract: Contract whose id is given to the agent.
        llm: Provider used for each reasoning step.
        max_steps: Maximum LLM round-trips before stopping.

    Returns:
        `status`, `final_answer`, `tools_called`, and `steps_taken` when the
        model stops.
    """
    tools_called: list[str] = []
    langfuse = _langfuse_client()
    messages: list[Message] = [
        Message(role="system", content=_SYSTEM_PROMPT),
        Message(
            role="user",
            content=(
                f"Contract ID to analyze: {contract.id}. Check for any missing "
                "clauses or cross-reference conflicts (e.g., Liability Cap vs "
                "Indemnification)."
            ),
        ),
    ]

    for step in range(max_steps):
        if step == max_steps - 1:
            messages.append(
                Message(
                    role="user",
                    content=(
                        "You have reached the maximum number of steps. You must "
                        "provide your final answer now based on the information "
                        "gathered so far."
                    ),
                )
            )
        response = await llm.complete(
            LLMRequest(
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.0,
            )
        )
        print(f"[Step {step+1}] LLM Tool Calls: {response.tool_calls}")
        print(f"[Step {step+1}] LLM Text: {response.text}")
        if not response.tool_calls:
            return {
                "status": "success",
                "final_answer": response.text,
                "steps_taken": step + 1,
                "tools_called": tools_called,
            }

        assistant_msg = {"role": "assistant", "content": response.text}
        if response.tool_calls:
            assistant_msg["tool_calls"] = response.tool_calls
            for tc in response.tool_calls:
                tools_called.append(tc["function"]["name"])
        messages.append(Message.model_validate(assistant_msg))
        for tc in response.tool_calls:
            name = tc["function"]["name"]
            args = _tool_arguments(tc)
            logger.info("Agent tool call step=%s name=%s", step + 1, name)
            with _start_tool_span(langfuse, name) as span:
                result = await _execute_tool(db, name, args)
                span.update(input=args, output=result)
            messages.append(
                Message.model_validate(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tc["function"]["name"],
                        "content": json.dumps(result),
                    }
                )
            )

    return {
        "status": "max_steps_reached",
        "final_answer": "Agent stopped to prevent infinite loops.",
        "tools_called": tools_called,
    }
