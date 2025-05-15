import uuid

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timezone


# Helper for timestamping with timezone awareness
def now_tz():
    """Returns the current time with UTC timezone."""
    return datetime.now(timezone.utc)


class Message(BaseModel):
    """
    Represents a single message within a chat topic.
    """

    # ID must be provided during instantiation (generated in ChatManager)
    id: str = Field(...)
    topic_id: str = Field(...)
    sender: Literal["user", "agent", "system"]  # Enforce allowed sender types
    content: str
    timestamp: datetime = Field(default_factory=now_tz)


class TaskResult(BaseModel):
    """
    Represents the result of an asynchronous task associated with a topic.
    """

    # ID must be provided during instantiation (generated in ChatManager)
    id: str = Field(...)
    topic_id: str = Field(...)
    content: str = Field(...)
    timestamp: datetime = Field(default_factory=now_tz)


class Topic(BaseModel):
    """
    Represents a single chat conversation topic.
    """

    # Topic ID can use default factory upon creation
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = Field(...)
    agent_id: str = Field(...)
    name: str = Field(...)
    messages: list[Message] = []
    task_results: list[TaskResult] = Field(
        default_factory=list
    )  # List of task results for the topic
    timestamp: datetime = Field(default_factory=now_tz)  # Topic creation timestamp


class Session(BaseModel):
    """
    Represents a user's session state.
    """

    client_id: str  # Unique identifier for the client session
    active_topic_id: str | None = None  # ID of the currently selected topic
    last_activity: datetime = Field(
        default_factory=now_tz
    )  # Timestamp of the last interaction
