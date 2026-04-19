"""API routes for DeepSeek AI assistant — streaming SSE."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.schemas.ai import AiRequest
from backend.services.ai_service import stream_ai_response

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/ask")
async def ask_ai(request: AiRequest):
    """
    Streaming SSE endpoint — retourne les tokens DeepSeek au fur et à mesure.

    Le frontend consomme cette réponse avec `fetch` + `ReadableStream`
    ou via `EventSource`.
    """
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=503, detail="AI service not configured (DEEPSEEK_API_KEY missing)")

    async def token_generator():
        async for token in stream_ai_response(request.message, request.context):
            yield token

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
    )
