from pydantic import BaseModel


class TypeOut(BaseModel):
    id: int
    name_en: str
    name_fr: str | None
    is_triple_fusion_type: bool

    model_config = {"from_attributes": True}
