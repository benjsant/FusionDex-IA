from pydantic import BaseModel


class AbilityListItem(BaseModel):
    id: int
    name_en: str
    name_fr: str | None

    model_config = {"from_attributes": True}


class AbilityDetail(AbilityListItem):
    description_en: str | None
    description_fr: str | None
