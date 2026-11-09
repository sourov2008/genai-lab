"""OpenAI embeddings and cosine similarity helpers."""

from __future__ import annotations

import logging
import math

from openai import AsyncOpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for `text`.

    Args:
        text: Input to embed.

    Returns:
        The first embedding from the OpenAI embeddings API.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        input=text,
        model=settings.embedding_model,
    )
    logger.debug("Embedded text with model=%s", settings.embedding_model)
    return response.data[0].embedding


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Return cosine similarity of two equal-orientation vectors.

    Args:
        vec1: First embedding.
        vec2: Second embedding.

    Returns:
        Similarity in `[-1, 1]`, or `0.0` if either vector has zero magnitude.
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    return dot_product / (mag1 * mag2)
