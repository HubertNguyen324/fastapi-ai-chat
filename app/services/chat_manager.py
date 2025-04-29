# app/services/chat_manager.py
import asyncio
import random
import uuid
import logging
from typing import Dict, List, Optional
import datetime
from datetime import timezone, timedelta

from app.models.chat import Session, Topic, Message, TaskResult
from app.models.agent import Agent
from app.services.connection_manager import connection_manager  # Import instance
from app.services.agent_manager import agent_manager  # Import instance

logger = logging.getLogger(__name__)


# Helper for timestamping
def now_tz():
    return datetime.datetime.now(timezone.utc)


class ChatManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.topics: Dict[str, Topic] = {}
        self.SESSION_TIMEOUT = timedelta(minutes=30)
        self._cleanup_task = None

    def _update_last_activity(self, client_id: str):
        """Updates the last activity timestamp for a session."""
        session = self.sessions.get(client_id)
        if session:
            session.last_activity = now_tz()
            logger.debug(
                f"Updated last activity for client {client_id} to {session.last_activity}"
            )
        else:
            logger.warning(
                f"Attempted to update last activity for non-existent session: {client_id}"
            )

    async def handle_connect(self, client_id: str) -> Optional[str]:
        """Handles initial connection, retrieves or creates session.
        Does NOT create a default topic for new sessions anymore.
        """
        now = now_tz()
        session = self.sessions.get(client_id)  # Try to get session first

        if session:
            # --- Session Exists (Reconnect Flow) ---
            # Simplified log - only log reconnect info here
            logger.info(f"Handling reconnect for existing session client {client_id}")
            self._update_last_activity(client_id)

            active_topic_id = session.active_topic_id
            # Validate active topic ID or find latest
            if active_topic_id and active_topic_id not in self.topics:
                logger.warning(
                    f"Reconnect: Active topic {active_topic_id} not found. Clearing."
                )
                active_topic_id = None
                session.active_topic_id = None

            if not active_topic_id:  # If still no active topic
                client_topics = self.get_topics_for_client(client_id)
                if client_topics:
                    latest_topic = max(client_topics, key=lambda t: t.timestamp)
                    active_topic_id = latest_topic.id
                    session.active_topic_id = active_topic_id
                    logger.info(
                        f"Reconnect: Restored active topic to latest: {active_topic_id}"
                    )

            return active_topic_id
        else:
            # --- Create New Session ---
            # Log creation here
            logger.info(
                f"Creating new session for client {client_id}. No default topic created."
            )
            new_session = Session(client_id=client_id, last_activity=now)
            self.sessions[client_id] = new_session
            return None  # No active topic for new session

    async def create_topic(self, client_id: str, agent_id: str) -> Topic:
        """Creates a new topic, stores it, and updates session."""
        topic_id = str(uuid.uuid4())
        topic = Topic(
            id=topic_id, client_id=client_id, agent_id=agent_id, timestamp=now_tz()
        )
        self.topics[topic_id] = topic

        if client_id in self.sessions:
            self.sessions[
                client_id
            ].active_topic_id = topic_id  # Set as active when created
            self._update_last_activity(client_id)
        else:
            logger.error(
                f"Session not found for client {client_id} when creating topic {topic_id}"
            )

        logger.info(
            f"Created new topic {topic_id} for agent {agent_id} by client {client_id}"
        )
        # Send topic list update AFTER topic is fully created and session updated
        await self.send_topic_list_update(client_id)
        return topic

    def get_topics_for_client(self, client_id: str) -> List[Topic]:
        """Gets all topics associated with a client, sorted by timestamp."""
        client_topics = [t for t in self.topics.values() if t.client_id == client_id]
        return sorted(client_topics, key=lambda t: t.timestamp)

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        return self.topics.get(topic_id)

    async def add_message_and_process(
        self, client_id: str, topic_id: str, user_message_content: str
    ):
        """Adds user message, triggers agent response and task simulation."""
        topic = self.get_topic(topic_id)
        if not topic or topic.client_id != client_id:
            logger.warning(f"Invalid topic {topic_id} for client {client_id}")
            return

        self._update_last_activity(client_id)

        # 1. Add user message
        logger.info(f"[ChatManager] Adding user message to topic {topic_id}")
        user_message_id = str(uuid.uuid4())
        user_message = Message(
            id=user_message_id,
            topic_id=topic_id,
            sender="user",
            content=user_message_content,
            timestamp=now_tz(),
        )
        logger.info(f"[ChatManager] User Message CREATED with ID: {user_message.id}")
        topic.messages.append(user_message)
        await self.send_message_update(client_id, user_message)
        logger.info(
            f"[ChatManager] User message update sent call completed for {client_id}"
        )

        # 2. Trigger Agent Response
        logger.info(f"[ChatManager] Preparing agent response for topic {topic_id}...")
        agent = agent_manager.get_agent_by_id(topic.agent_id)
        agent_name = agent.name if agent else "Unknown Agent"
        agent_response_content = (
            f"Okay, I received: '{user_message_content}' (from {agent_name})"
        )
        agent_message_id = str(uuid.uuid4())
        if agent_message_id == user_message_id:  # Prevent collision
            logger.warning(
                f"[ChatManager] UUID collision! Re-generating agent message ID."
            )
            agent_message_id = str(uuid.uuid4())
        agent_message = Message(
            id=agent_message_id,
            topic_id=topic_id,
            sender="agent",
            content=agent_response_content,
            timestamp=now_tz(),
        )
        logger.info(f"[ChatManager] Agent Message CREATED with ID: {agent_message.id}")
        topic.messages.append(agent_message)
        logger.info(
            f"[ChatManager] Agent message object created in memory. Simulating delay..."
        )

        await asyncio.sleep(random.uniform(0.5, 1.5))

        logger.info(
            f"[ChatManager] Sending agent message update to client {client_id} for topic {topic_id}..."
        )
        logger.info(
            f"[ChatManager] Attempting to send agent_message object with ID: {agent_message.id}"
        )
        await self.send_message_update(client_id, agent_message)
        logger.info(
            f"[ChatManager] Agent message update call completed for client {client_id}"
        )

        # 3. Trigger Background Task
        logger.info(
            f"[ChatManager] Triggering background task simulation for topic {topic_id}"
        )
        asyncio.create_task(
            self.simulate_background_task(client_id, topic_id, user_message_content)
        )

    async def simulate_background_task(
        self, client_id: str, topic_id: str, task_input: str
    ):
        """Simulates a background task and sends result."""
        await asyncio.sleep(random.uniform(2.0, 5.0))
        topic = self.get_topic(topic_id)
        if not topic or topic.client_id != client_id:
            logger.warning(
                f"Task completed for topic {topic_id}, but topic/client mismatch or disconnected."
            )
            return

        result_id = str(uuid.uuid4())
        result_content = f"Task '{task_input[:20]}...' completed"
        task_result = TaskResult(
            id=result_id, topic_id=topic_id, content=result_content, timestamp=now_tz()
        )
        topic.task_results.append(task_result)
        logger.info(f"Task result created for topic {topic_id}. Sending update.")
        await self.send_task_result_update(client_id, task_result)

    async def change_agent_for_topic(
        self,
        client_id: str,
        current_topic_id: str,
        new_agent_id: str,
        first_message: str,
    ):
        """Creates a new topic when the agent is changed mid-conversation."""
        self._update_last_activity(client_id)
        logger.info(
            f"Client {client_id} changing agent to {new_agent_id} from topic {current_topic_id}. Creating new topic."
        )
        new_topic = await self.create_topic(client_id, new_agent_id)
        await self.add_message_and_process(client_id, new_topic.id, first_message)
        return new_topic.id

    # --- WebSocket Update Helpers ---
    async def send_full_topic_state(self, client_id: str, topic_id: str):
        topic = self.get_topic(topic_id)
        if topic and topic.client_id == client_id:
            logger.debug(
                f"Sending full topic state for topic {topic_id} to client {client_id}"
            )
            state_data = {
                "type": "topic_state",
                "payload": {
                    "topic_id": topic.id,
                    "agent_id": topic.agent_id,
                    "messages": [msg.model_dump(mode="json") for msg in topic.messages],
                    "task_results": [
                        res.model_dump(mode="json") for res in topic.task_results
                    ],
                },
            }
            await connection_manager.send_json(state_data, client_id)
        else:
            logger.warning(
                f"Attempted state send for invalid/mismatched topic {topic_id} client {client_id}"
            )

    async def send_topic_list_update(self, client_id: str):
        topics_list = self.get_topics_for_client(client_id)
        logger.debug(
            f"Sending topic list update ({len(topics_list)} topics) to client {client_id}"
        )
        topic_list_data = [
            {"id": t.id, "agent_id": t.agent_id, "name": t.name or f"Chat {i + 1}"}
            for i, t in enumerate(topics_list)
        ]
        update_data = {"type": "topic_list_update", "payload": topic_list_data}
        await connection_manager.send_json(update_data, client_id)

    async def send_message_update(self, client_id: str, message: Message):
        logger.debug(f"Sending message update (ID: {message.id}) to client {client_id}")
        update_data = {
            "type": "new_message",
            "payload": message.model_dump(mode="json"),
        }
        await connection_manager.send_json(update_data, client_id)

    async def send_task_result_update(self, client_id: str, task_result: TaskResult):
        logger.debug(
            f"Sending task result update (ID: {task_result.id}) to client {client_id}"
        )
        update_data = {
            "type": "new_task_result",
            "payload": task_result.model_dump(mode="json"),
        }
        await connection_manager.send_json(update_data, client_id)

    async def send_active_topic_update(
        self, client_id: str, topic_id: Optional[str]
    ):  # Allow None
        logger.debug(
            f"Sending active topic update (Topic: {topic_id}) to client {client_id}"
        )
        update_data = {"type": "active_topic_update", "payload": {"topic_id": topic_id}}
        await connection_manager.send_json(update_data, client_id)

    # --- Session Cleanup Task ---
    async def start_cleanup_task(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            logger.info(
                f"Starting session cleanup task (timeout: {self.SESSION_TIMEOUT})..."
            )
            self._cleanup_task = asyncio.create_task(self._run_cleanup_loop())
        else:
            logger.warning("Cleanup task already running.")

    async def stop_cleanup_task(self):
        if self._cleanup_task and not self._cleanup_task.done():
            logger.info("Stopping session cleanup task...")
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled normally.")
            except Exception as e:
                logger.error(f"Exception during cleanup task stop: {e}", exc_info=True)
            finally:
                self._cleanup_task = None
                logger.info("Cleanup task stopped.")
        else:
            logger.info("Session cleanup task not running or already completed.")

    async def _run_cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            try:
                now = now_tz()
                inactive_client_ids = [
                    client_id
                    for client_id, session in self.sessions.items()
                    if now - session.last_activity > self.SESSION_TIMEOUT
                ]

                if not inactive_client_ids:
                    continue

                logger.info(
                    f"Found {len(inactive_client_ids)} inactive sessions to clean up."
                )
                for client_id in inactive_client_ids:
                    topics_to_remove = [
                        tid
                        for tid, t in self.topics.items()
                        if t.client_id == client_id
                    ]
                    logger.debug(
                        f"Removing {len(topics_to_remove)} topics for inactive client {client_id}."
                    )
                    for topic_id in topics_to_remove:
                        if topic_id in self.topics:
                            del self.topics[topic_id]

                    if client_id in self.sessions:
                        del self.sessions[client_id]
                        logger.debug(f"Removed inactive session for client {client_id}")

                    websocket = connection_manager.active_connections.get(client_id)
                    if websocket:
                        logger.info(
                            f"Closing potentially lingering WebSocket for inactive client {client_id}"
                        )
                        await websocket.close(code=1000, reason="Session timed out")
                        connection_manager.disconnect(
                            client_id
                        )  # Ensure manager cleanup

            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(300)  # Wait longer after error


# Singleton instance
chat_manager = ChatManager()
