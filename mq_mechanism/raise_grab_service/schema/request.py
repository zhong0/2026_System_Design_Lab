from pydantic import BaseModel


class GrabRequest(BaseModel):
    username: str
