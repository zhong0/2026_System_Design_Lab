from pydantic import BaseModel

class FortuneRequest(BaseModel):
    username: str