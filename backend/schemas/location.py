from pydantic import BaseModel


class LocationOut(BaseModel):
    location_id: int
    location_name: str
    method: str
    notes: str | None

    model_config = {"from_attributes": True}
