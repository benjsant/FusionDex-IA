from pydantic import BaseModel


class CreatorOut(BaseModel):
    id: int
    name: str
    sprite_count: int

    model_config = {"from_attributes": True}
