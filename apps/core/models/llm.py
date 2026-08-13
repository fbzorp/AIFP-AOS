import json
import logging
import asyncio
from typing import Any, Dict, Optional
from litellm import acompletion
from apps.api.config import settings
from apps.core.models.factory import deepseek_fast
from apps.core.audit.service import record_event_async

logger = logging.getLogger(__name__)

# Simple in-memory budget tracker for the session
_session_spend = 0.0

async def complete_json(
    model: str,
    system_prompt: str,
    user_content: str,
    schema_hint: Optional[str] = None,
    session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Calls LLM to get a JSON response.
    Enforces a daily budget guard and handles fallbacks if no API key is present.
    In production, raises explicit errors instead of falling back to mock content.
    """
    global _session_spend

    is_production = settings.APP_ENV == "production"

    # Budget guard
    budget = getattr(settings, "DAILY_LLM_BUDGET_USD", 25.0)
    if _session_spend >= budget:
        error_msg = f"Daily LLM budget of ${budget} exceeded. Session spend: ${_session_spend}"
        logger.warning(error_msg)
        if is_production:
            if session:
                await record_event_async(
                    session,
                    agent_name="llm",
                    event_type="budget_exceeded",
                    message=error_msg,
                    metadata={"session_spend": _session_spend, "budget": budget}
                )
            raise ValueError(error_msg)
        return _fallback_heuristic(system_prompt, user_content)

    # Check for API key (via pydantic settings)
    if not settings.DEEPSEEK_API_KEY:
        error_msg = "DEEPSEEK_API_KEY not found"
        logger.warning(error_msg)
        if is_production:
            if session:
                await record_event_async(
                    session,
                    agent_name="llm",
                    event_type="missing_credentials",
                    message=error_msg,
                    metadata={"env": "production"}
                )
            raise ValueError(error_msg)
        logger.info("DEEPSEEK_API_KEY not found, using local fallback heuristic")
        return _fallback_heuristic(system_prompt, user_content)

    prompt = f"{system_prompt}\n\nSchema Hint: {schema_hint if schema_hint else 'Return valid JSON'}"

    try:
        response = await acompletion(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            timeout=30
        )

        # Track spend
        _session_spend += getattr(response, "_response_ms", 0) / 1000 * 0.0001  # Mock cost calc

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        error_msg = f"LLM completion failed: {e}"
        logger.error(error_msg)
        if is_production:
            if session:
                await record_event_async(
                    session,
                    agent_name="llm",
                    event_type="provider_failure",
                    message=error_msg,
                    metadata={"model": model, "error": str(e)}
                )
            raise RuntimeError(error_msg) from e
        return _fallback_heuristic(system_prompt, user_content)

def _fallback_heuristic(system_prompt: str, user_content: str) -> Dict[str, Any]:
    """Deterministic fallback for tests/no-key environments."""
    logger.debug("Executing fallback heuristic")
    # Simple logic to return something that looks like the expected schema
    if "Market Intelligence" in system_prompt:
        return {
            "sources": [
                {
                    "title": "Heuristic Source",
                    "url": "https://example.com/mock",
                    "relevance": 0.8,
                    "summary": "Mock summary for testing."
                }
            ]
        }
    return {"status": "mock_success", "data": "fallback_triggered"}
