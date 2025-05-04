from pydantic import BaseModel, Field
import uuid


class LLMAgent(BaseModel):
    """
    Represents an AI Agent available in the system.
    """

    id: str = Field(default_factory=lambda: f"agent_{str(uuid.uuid4())[:8]}")
    name: str = Field(..., max_length=70)
    description: str = Field(default="")
    model: str = Field(...)
    system_prompt: str | None = Field(default=None)
    temperature: float = Field(default=0.2, ge=0, le=2)
    top_p: float = Field(default=0.95, ge=0, le=1)
