"""API routes for DB audit stats."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.stats import CoverageOut
from backend.services.stats_service import compute_coverage

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/coverage", response_model=CoverageOut)
def get_coverage(db: Session = Depends(get_db)):
    """Audit : Pokémon sans sprite/types/moves, moves/abilities orphelins, totaux."""
    return CoverageOut(**compute_coverage(db))
