# warren-core/app/services/llm_client.py
import logging
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)
_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


async def classify_direction(event_type: str, region: str, payload_summary: str) -> float:
    """
    Returns 0.0 (fully de-escalatory) to 1.0 (fully escalatory).
    Falls back to 0.5 (neutral) on any error.
    """
    settings = get_settings()
    prompt = (
        f"Geopolitical event: '{event_type}' detected in '{region}'. "
        f"Context: {payload_summary[:300]}. "
        "Rate this event on a scale from 0.0 (completely de-escalatory/peaceful) "
        "to 1.0 (highly escalatory/conflictual). "
        "Reply with only a decimal number between 0.0 and 1.0, nothing else."
    )
    try:
        client = get_client()
        resp = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        score = float(raw)
        return max(0.0, min(1.0, score))
    except Exception as e:
        logger.warning("direction_score LLM call failed: %s — defaulting to 0.5", e, exc_info=True)
        return 0.5
