"""API routes for DeepSeek AI assistant — streaming SSE."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.ai import AiRequest
from backend.services.ai_service import stream_ai_response

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/ask")
async def ask_ai(request: AiRequest, db: Session = Depends(get_db)):
    """Agent tool-calling streaming SSE.

    Le LLM reçoit la liste de tools (BDD Pokémon/fusions/moves/items/tutors),
    exécute les appels nécessaires, puis stream sa réponse finale. Si aucun
    tool n'a remonté d'info pertinente, répond *« Je n'ai pas trouvé cette
    information. »* (fail-closed).

    Le frontend consomme cette réponse avec `fetch` + `ReadableStream`.
    """
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise HTTPException(status_code=503, detail="AI service not configured (DEEPSEEK_API_KEY missing)")

    async def token_generator():
        async for token in stream_ai_response(db, request.message, request.context):
            yield token

    return StreamingResponse(
        token_generator(),
        media_type="text/plain; charset=utf-8",
    )
