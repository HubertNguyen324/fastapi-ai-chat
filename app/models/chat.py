from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import datetime
import uuid


# Helper for timestamping with timezone awareness
def now_tz():
    """Returns the current time with UTC timezone."""
    return datetime.datetime.now(datetime.timezone.utc)


class Message(BaseModel):
    """
    Represents a single message within a chat topic.
    """

    # ID must be provided during instantiation (generated in ChatManager)
    id: str
    topic_id: str
    sender: Literal["user", "agent", "system"]  # Enforce allowed sender types
    content: str
    timestamp: datetime.datetime = Field(default_factory=now_tz)


class TaskResult(BaseModel):
    """
    Represents the result of an asynchronous task associated with a topic.
    """

    # ID must be provided during instantiation (generated in ChatManager)
    id: str
    topic_id: str
    content: str  # Content/summary of the task result
    timestamp: datetime.datetime = Field(default_factory=now_tz)


class Topic(BaseModel):
    """
    Represents a single chat conversation topic.
    """

    # Topic ID can use default factory upon creation
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str  # Associated client session ID
    agent_id: str  # ID of the agent handling this topic
    name: Optional[str] = None  # Optional user-defined name (or auto-generated)
    messages: List[Message] = Field(
        default_factory=list
    )  # List of messages in the topic
    task_results: List[TaskResult] = Field(
        default_factory=list
    )  # List of task results for the topic
    timestamp: datetime.datetime = Field(
        default_factory=now_tz
    )  # Topic creation timestamp


class Session(BaseModel):
    """
    Represents a user's session state.
    """

    client_id: str  # Unique identifier for the client session
    active_topic_id: Optional[str] = None  # ID of the currently selected topic
    last_activity: datetime.datetime = Field(
        default_factory=now_tz
    )  # Timestamp of the last interaction
