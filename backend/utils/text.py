"""Text utilities — accent-insensitive search normalization."""

from __future__ import annotations

import unicodedata


def normalize(text: str) -> str:
    """Lowercase + strip accents (NFD decomposition).

    Used for accent-insensitive search on EN/FR names.
    Example: "Éclair" → "eclair", "Pokémon" → "pokemon"
    """
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )
