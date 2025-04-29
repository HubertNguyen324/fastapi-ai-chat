from pydantic import BaseModel, Field
import uuid


class Agent(BaseModel):
    """
    Represents an AI Agent available in the system.
    """

    # Use Field for default_factory for clarity and potential future validation
    id: str = Field(default_factory=lambda: f"agent_{str(uuid.uuid4())[:8]}")
    name: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"id": "agent_abc12345", "name": "Helpful Assistant"}]
        }
    }
