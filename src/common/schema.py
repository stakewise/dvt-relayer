from pydantic import BaseModel


class InfoResponse(BaseModel):
    network: str
    validators_manager_address: str
