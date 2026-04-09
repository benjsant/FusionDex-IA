"""DeepSeek AI service — OpenAI-compatible streaming chat.

Reads DEEPSEEK_API_KEY from environment.
Base URL: https://api.deepseek.com
Model: deepseek-chat
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from openai import AsyncOpenAI

SYSTEM_PROMPT = """Tu es FusionDex AI, un expert du jeu Pokémon Infinite Fusion.
Tu connais les mécaniques de fusion (formules de stats, types résultants, talents),
les différences avec les jeux officiels (évolutions modifiées, capacités exclusives IF),
et tu peux donner des conseils stratégiques sur les équipes de fusion.
Réponds en français par défaut, en anglais si l'utilisateur écrit en anglais.
Sois concis et précis."""


def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable not set")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


async def stream_ai_response(
    message: str,
    context: str | None = None,
) -> AsyncIterator[str]:
    """
    Yields text chunks from DeepSeek streaming response.

    Args:
        message: User's question.
        context: Optional Pokémon/fusion context (pre-filled from UI).
    """
    client = _get_client()

    user_content = message
    if context:
        user_content = f"[Contexte: {context}]\n\n{message}"

    stream = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ],
        stream=True,
        max_tokens=1024,
        temperature=0.7,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
