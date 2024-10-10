from pydantic import BaseModel


class InfoResponse(BaseModel):
    network: str
