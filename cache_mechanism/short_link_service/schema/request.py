from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class createLinkRequest(BaseModel):
    urlLink: str