from pydantic import BaseModel


class GenerationOut(BaseModel):
    id: int
    name_en: str
    name_fr: str

    model_config = {"from_attributes": True}
