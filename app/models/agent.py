from pydantic import BaseModel
import uuid


class Agent(BaseModel):
    id: str = str(uuid.uuid4())
    name: str
