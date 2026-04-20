"""Pydantic schemas for the AI assistant endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Question posée à l'assistant.")
    context: str | None = Field(
        None,
        description="Contexte optionnel injecté dans le prompt (ex. 'Pokémon Dracaufeu id=6, fusion avec Mewtwo id=150').",
    )
