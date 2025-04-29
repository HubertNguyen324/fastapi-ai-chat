from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import datetime
import uuid


# Helper for timestamping
def now_tz():
    return datetime.datetime.now(datetime.timezone.utc)


class Message(BaseModel):
    # ID must be provided during instantiation
    id: str
    topic_id: str
    sender: str  # 'user' or 'agent' or 'system'
    content: str
    timestamp: datetime.datetime = Field(default_factory=now_tz)


class TaskResult(BaseModel):
    # ID must be provided during instantiation
    id: str
    topic_id: str
    content: str
    timestamp: datetime.datetime = Field(default_factory=now_tz)


class Topic(BaseModel):
    # Topic ID can use default factory
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    agent_id: str
    name: Optional[str] = None
    messages: List[Message] = []
    task_results: List[TaskResult] = []
    timestamp: datetime.datetime = Field(default_factory=now_tz)


class Session(BaseModel):
    client_id: str
    active_topic_id: Optional[str] = None
    last_activity: datetime.datetime = Field(default_factory=now_tz)
