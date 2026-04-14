from __future__ import annotations

from pydantic import BaseModel


class SpriteOut(BaseModel):
    id: int
    head_id: int
    body_id: int
    sprite_path: str
    is_custom: bool
    is_default: bool
    source: str  # local | community | auto_generated
    creators: list[str]

    model_config = {"from_attributes": True}
