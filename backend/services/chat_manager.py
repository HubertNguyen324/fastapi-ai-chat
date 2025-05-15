import asyncio
import random
import uuid
import logging
import datetime
from datetime import timezone, timedelta

# Import models and managers/config
from backend.models.chat import Session, Topic, Message, TaskResult
from backend.services.connection_manager import connection_manager
from backend.services.agent_manager import agent_manager
from backend.config import settings  # Import configured settings

logger = logging.getLogger(__name__)


# Helper for timestamping
def now_tz():
    """Returns the current datetime with UTC timezone."""
    return datetime.datetime.now(timezone.utc)


class ChatManager:
    """
    Manages chat sessions, topics, messages, and related business logic.
    Uses in-memory storage in this skeleton version.
    """

    def __init__(self):
        """Initializes the ChatManager."""
        self.sessions: dict[str, Session] = {}  # client_id -> Session object
        self.topics: dict[str, Topic] = {}  # topic_id -> Topic object
        # Load session timeout from config
        self.SESSION_TIMEOUT = timedelta(minutes=settings.session_timeout_minutes)
        self._cleanup_task: asyncio.Task | None = None  # Background task handle
        logger.info(
            f"ChatManager initialized. Session timeout set to: {self.SESSION_TIMEOUT}"
        )

    def _update_last_activity(self, client_id: str):
        """Updates the last_activity timestamp for the client's session."""
        session = self.sessions.get(client_id)
        if session:
            session.last_activity = now_tz()
            logger.debug(
                f"Updated last activity for client '{client_id}' to {session.last_activity}"
            )
        else:
            # This could happen if an action occurs right as a session times out.
            logger.warning(
                f"Attempted to update last activity for non-existent session: '{client_id}'"
            )

    async def handle_connect(self, client_id: str) -> str | None:
        """
        Handles a client connecting via WebSocket.
        - If session exists, updates last activity and returns active topic ID (or latest).
        - If session is new, creates it and returns None (no default topic).
        """
        session = self.sessions.get(client_id)

        if session:
            # --- Existing Session (Reconnect) ---
            logger.info(f"Handling reconnect for existing session client '{client_id}'")
            self._update_last_activity(client_id)  # Mark activity on reconnect

            active_topic_id = session.active_topic_id
            # Validate that the active topic still exists in our topics store
            if active_topic_id and active_topic_id not in self.topics:
                logger.warning(
                    f"Reconnect: Active topic '{active_topic_id}' not found for client '{client_id}'. Clearing."
                )
                active_topic_id = None
                session.active_topic_id = None  # Clear invalid ID from session

            # If no valid active topic, try setting to the most recently created one
            if not active_topic_id:
                client_topics = self.get_topics_for_client(
                    client_id
                )  # Sorted oldest first
                if client_topics:
                    latest_topic = client_topics[-1]  # Get the last topic (most recent)
                    active_topic_id = latest_topic.id
                    session.active_topic_id = active_topic_id  # Update session state
                    logger.info(
                        f"Reconnect: Restored active topic to latest ('{active_topic_id}') for client '{client_id}'"
                    )

            return (
                active_topic_id  # Return current or latest valid topic ID (can be None)
            )

        else:
            # --- New Session ---
            logger.info(
                f"Creating new session for client '{client_id}'. No default topic will be created."
            )
            new_session = Session(client_id=client_id, last_activity=now_tz())
            self.sessions[client_id] = new_session
            # Return None, indicating no active topic initially for a new session
            return None

    async def create_topic(self, client_id: str, agent_id: str) -> Topic | None:
        """
        Creates a new chat topic associated with a client and agent.
        Sets the new topic as the client's active topic.
        Returns the created Topic object or None on failure.
        """
        session = self.sessions.get(client_id)
        if not session:
            logger.error(
                f"Cannot create topic: Session not found for client '{client_id}'"
            )
            return None

        agent = agent_manager.get_agent_by_id(agent_id)
        if not agent:
            logger.error(f"Cannot create topic: Agent not found with ID '{agent_id}'")
            return None

        # Generate topic ID and create the Topic object
        topic_id = str(uuid.uuid4())
        topic = Topic(
            id=topic_id, client_id=client_id, agent_id=agent_id, timestamp=now_tz()
        )
        self.topics[topic_id] = topic  # Store the new topic

        # Update the session: set new topic as active and update activity time
        session.active_topic_id = topic_id
        self._update_last_activity(client_id)

        logger.info(
            f"Created new topic '{topic_id}' for agent '{agent.name}' by client '{client_id}'"
        )
        # Notify the client about the updated list of topics AFTER creation
        await self.send_topic_list_update(client_id)
        return topic

    def get_topics_for_client(self, client_id: str) -> list[Topic]:
        """Retrieves all topics for a specific client, sorted by creation time (oldest first)."""
        client_topics = [t for t in self.topics.values() if t.client_id == client_id]
        return sorted(client_topics, key=lambda t: t.timestamp)

    def get_topic(self, topic_id: str) -> Topic | None:
        """Retrieves a single topic by its ID."""
        return self.topics.get(topic_id)

    async def add_message_and_process(
        self, client_id: str, topic_id: str, user_message_content: str
    ):
        """
        Core logic for handling a new user message:
        1. Validates the topic and client.
        2. Updates session activity.
        3. Creates and stores the user Message object.
        4. Sends the user message update to the client.
        5. Simulates triggering the agent response.
        6. Simulates triggering a background task.
        """
        topic = self.get_topic(topic_id)
        # Validate topic existence and ownership
        if not topic:
            logger.warning(f"Cannot add message: Topic '{topic_id}' not found.")
            # Optionally inform client via WebSocket error message
            await connection_manager.send_json(
                {
                    "type": "error",
                    "payload": {"detail": f"Chat topic {topic_id} not found."},
                },
                client_id,
            )
            return
        if topic.client_id != client_id:
            logger.warning(
                f"Permission denied: Topic '{topic_id}' does not belong to client '{client_id}'."
            )
            await connection_manager.send_json(
                {
                    "type": "error",
                    "payload": {"detail": "Access denied to this chat topic."},
                },
                client_id,
            )
            return

        # Update activity timestamp for the session
        self._update_last_activity(client_id)

        # 1. Create and store the user message
        logger.info(f"[ChatManager] Adding user message to topic '{topic_id}'")
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
        # Send update to the originating client
        await self.send_message_update(client_id, user_message)
        logger.info(
            f"[ChatManager] User message update sent call completed for '{client_id}'"
        )

        # 2. Simulate Agent Response (replace with actual logic)
        await self._simulate_agent_response(client_id, topic, user_message)

        # 3. Simulate Background Task (replace with actual logic)
        logger.info(
            f"[ChatManager] Triggering background task simulation for topic '{topic_id}'"
        )
        # Create task without awaiting its completion here
        asyncio.create_task(
            self._simulate_background_task(client_id, topic_id, user_message_content)
        )

    async def _simulate_agent_response(
        self, client_id: str, topic: Topic, user_message: Message
    ):
        """Placeholder for actual agent interaction logic."""
        logger.info(f"[Agent Sim] Preparing response for topic '{topic.id}'...")
        agent = agent_manager.get_agent_by_id(topic.agent_id)
        agent_name = agent.name if agent else "Unknown Agent"

        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Generate response content (simple echo for now)
        full_response_content = (
            f"Okay, I received: '{user_message.content}' (from {agent_name})"
        )
        words = full_response_content.split()

        # Create and store the agent message
        agent_message_id = str(uuid.uuid4())
        # Basic collision check (very unlikely but harmless)
        if agent_message_id == user_message.id:
            logger.warning("[Agent Sim] UUID collision! Regenerating agent message ID.")
            agent_message_id = str(uuid.uuid4())

        # Simulate streaming
        current_chunk = ""
        chunk_size = random.randint(
            2, 5
        )  # Simulate variable chunk sizes (words per chunk)
        word_count = 0

        for word in words:
            current_chunk += word + " "
            word_count += 1
            if word_count >= chunk_size:
                # Send the chunk
                await self.send_agent_message_chunk(
                    client_id=client_id,
                    topic_id=topic.id,
                    message_id=agent_message_id,
                    content_chunk=current_chunk,
                    is_first_chunk=(
                        word_count == chunk_size
                    ),  # Mark the very first chunk
                )
                # Reset for next chunk
                current_chunk = ""
                word_count = 0
                chunk_size = random.randint(2, 5)
                # Simulate network delay between chunks
                await asyncio.sleep(random.uniform(0.1, 0.4))

        # Send any remaining part as the last chunk
        if current_chunk:
            await self.send_agent_message_chunk(
                client_id=client_id,
                topic_id=topic.id,
                message_id=agent_message_id,
                content_chunk=current_chunk,
                is_first_chunk=(len(words) <= chunk_size and current_chunk != ""),
            )

        await self.send_agent_stream_end(client_id, topic.id, agent_message_id)
        logger.info(
            f"[Agent Sim] Sent stream end signal for message ID: {agent_message_id}"
        )

        final_agent_message = Message(
            id=agent_message_id,  # Use the same ID as the stream
            topic_id=topic.id,
            sender="agent",
            content=full_response_content,  # Store the full assembled content
            timestamp=now_tz(),  # Timestamp can be start or end of generation
        )
        topic.messages.append(final_agent_message)
        logger.info(
            f"[Agent Sim] Stored complete agent message (ID: {agent_message_id}) in history."
        )

    async def _simulate_background_task(
        self, client_id: str, topic_id: str, task_input: str
    ):
        """Placeholder for triggering and handling background tasks."""
        delay = random.uniform(2.0, 5.0)
        logger.info(
            f"[Task Sim] Simulating background task for topic '{topic_id}' (input: '{task_input[:30]}...', delay: {delay:.1f}s)"
        )
        await asyncio.sleep(delay)

        # Important: Re-check if session/topic are still valid after the delay
        topic = self.get_topic(topic_id)
        session = self.sessions.get(client_id)
        if not session or not topic or topic.client_id != client_id:
            logger.warning(
                f"[Task Sim] Task completed for topic '{topic_id}', but session/topic invalid or client disconnected. Result not sent."
            )
            return

        # Create and store the task result
        result_id = str(uuid.uuid4())
        result_content = f"Task '{task_input[:20]}...' completed successfully."
        task_result = TaskResult(
            id=result_id, topic_id=topic_id, content=result_content, timestamp=now_tz()
        )
        topic.task_results.append(task_result)  # Add to topic's result list

        logger.info(
            f"[Task Sim] Task result created for topic '{topic_id}'. Sending update to client '{client_id}'."
        )
        # Send the result to the client
        await self.send_task_result_update(client_id, task_result)

    async def change_agent_for_topic(
        self,
        client_id: str,
        current_topic_id: str,
        new_agent_id: str,
        first_message: str,
    ) -> str | None:
        """
        Handles the scenario where a user changes the agent mid-conversation.
        This creates a *new* topic linked to the new agent and sends the
        current message as the first message to that new topic.
        Returns the new topic ID or None on failure.
        """
        self._update_last_activity(client_id)  # Count as activity
        logger.info(
            f"Client '{client_id}' changing agent to '{new_agent_id}' from topic '{current_topic_id}'. Creating new topic."
        )

        # Create the new topic (this also updates the session's active topic ID)
        new_topic = await self.create_topic(client_id, new_agent_id)
        if not new_topic:
            logger.error(
                f"Failed to create new topic during agent change for client '{client_id}'"
            )
            return None  # Indicate failure

        # Process the user's message within the context of the *new* topic
        await self.add_message_and_process(client_id, new_topic.id, first_message)
        # Return the ID of the newly created and now active topic
        return new_topic.id

    # --- WebSocket Update Helper Methods ---
    # These methods format data and use ConnectionManager to send updates

    async def send_full_topic_state(self, client_id: str, topic_id: str):
        """Sends the complete message and task history for a topic."""
        topic = self.get_topic(topic_id)
        # Ensure topic exists and belongs to the requesting client
        if topic and topic.client_id == client_id:
            logger.debug(
                f"Sending full topic state for topic '{topic_id}' to client '{client_id}'"
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
                f"Attempted state send for invalid/mismatched topic '{topic_id}' client '{client_id}'"
            )

    async def send_topic_list_update(self, client_id: str):
        """Sends the client's current list of topics (summary info)."""
        topics_list = self.get_topics_for_client(client_id)  # Sorted oldest first
        logger.debug(
            f"Sending topic list update ({len(topics_list)} topics) to client '{client_id}'"
        )
        # Generate default names like "Chat 1", "Chat 2" if topic.name is None
        topic_list_data = [
            {"id": t.id, "agent_id": t.agent_id, "name": t.name or f"Chat {i + 1}"}
            for i, t in enumerate(topics_list)
        ]
        update_data = {"type": "topic_list_update", "payload": topic_list_data}
        await connection_manager.send_json(update_data, client_id)

    async def send_message_update(self, client_id: str, message: Message):
        """Sends a single new message object."""
        logger.debug(
            f"Sending message update (ID: {message.id}) to client '{client_id}'"
        )
        update_data = {
            "type": "new_message",
            "payload": message.model_dump(mode="json"),
        }
        await connection_manager.send_json(update_data, client_id)

    async def send_task_result_update(self, client_id: str, task_result: TaskResult):
        """Sends a single new task result object."""
        logger.debug(
            f"Sending task result update (ID: {task_result.id}) to client '{client_id}'"
        )
        update_data = {
            "type": "new_task_result",
            "payload": task_result.model_dump(mode="json"),
        }
        await connection_manager.send_json(update_data, client_id)

    async def send_active_topic_update(self, client_id: str, topic_id: str | None):
        """Informs the client which topic ID should be considered active (can be None)."""
        logger.debug(
            f"Sending active topic update (Topic: {topic_id}) to client '{client_id}'"
        )
        update_data = {"type": "active_topic_update", "payload": {"topic_id": topic_id}}
        await connection_manager.send_json(update_data, client_id)

    # --- Session Cleanup Task Logic ---

    async def start_cleanup_task(self):
        """Starts the background task that periodically cleans up inactive sessions."""
        if self._cleanup_task is None or self._cleanup_task.done():
            logger.info(
                f"Starting session cleanup task (timeout: {self.SESSION_TIMEOUT})..."
            )
            self._cleanup_task = asyncio.create_task(self._run_cleanup_loop())
        else:
            logger.warning("Cleanup task start requested, but already running.")

    async def stop_cleanup_task(self):
        """Stops the background session cleanup task gracefully."""
        if self._cleanup_task and not self._cleanup_task.done():
            logger.info("Stopping session cleanup task...")
            self._cleanup_task.cancel()  # Request cancellation
            try:
                # Wait for the task to finish handling the cancellation
                await self._cleanup_task
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled normally.")
            except Exception as e:
                logger.error(
                    f"Exception while waiting for cleanup task cancellation: {e}",
                    exc_info=True,
                )
            finally:
                self._cleanup_task = None  # Clear task handle
                logger.info("Cleanup task stopped.")
        else:
            logger.info(
                "Session cleanup task stop requested, but task not running or already completed."
            )

    async def _run_cleanup_loop(self):
        """The actual loop performing periodic session cleanup."""
        logger.info("Session cleanup loop started.")
        while True:
            # Wait for the check interval (e.g., 60 seconds)
            await asyncio.sleep(60)
            try:
                now = now_tz()
                # Identify clients whose last activity is older than the timeout
                inactive_client_ids = [
                    client_id
                    for client_id, session in self.sessions.items()
                    if now - session.last_activity > self.SESSION_TIMEOUT
                ]

                # If no inactive sessions, continue to next check
                if not inactive_client_ids:
                    # logger.debug("Session cleanup: No inactive sessions found.") # Optional: reduce log noise
                    continue

                logger.info(
                    f"Session cleanup: Found {len(inactive_client_ids)} inactive sessions: {inactive_client_ids}"
                )
                for client_id in inactive_client_ids:
                    # 1. Remove associated topics from memory
                    # Iterate over a copy of keys/items if modifying the dict during iteration
                    topics_to_remove = [
                        tid
                        for tid, t in list(self.topics.items())
                        if t.client_id == client_id
                    ]
                    if topics_to_remove:
                        logger.debug(
                            f"Removing {len(topics_to_remove)} topics for inactive client '{client_id}'."
                        )
                        for topic_id in topics_to_remove:
                            if topic_id in self.topics:
                                del self.topics[topic_id]  # Remove topic data

                    # 2. Remove the session object itself
                    if client_id in self.sessions:
                        del self.sessions[client_id]  # Remove session data
                        logger.debug(
                            f"Removed inactive session data for client '{client_id}'"
                        )

                    # 3. Attempt to close any potentially lingering WebSocket connection
                    websocket = connection_manager.active_connections.get(client_id)
                    if websocket:
                        logger.info(
                            f"Closing potentially lingering WebSocket for inactive client '{client_id}'"
                        )
                        # Send standard close frame
                        await websocket.close(code=1000, reason="Session timed out")
                        # Ensure removal from connection manager (should also happen in router finally block)
                        connection_manager.disconnect(client_id)

            except asyncio.CancelledError:
                # Expected when stop_cleanup_task is called
                logger.info(
                    "Session cleanup loop received cancellation request. Exiting."
                )
                break  # Exit the loop gracefully
            except Exception as e:
                # Log unexpected errors but allow the loop to continue
                logger.error(
                    f"Error occurred in session cleanup loop: {e}", exc_info=True
                )
                # Consider waiting longer after an error to prevent rapid logging
                await asyncio.sleep(300)

        logger.info("Session cleanup loop finished.")

    async def send_agent_message_chunk(
        self,
        client_id: str,
        topic_id: str,
        message_id: str,
        content_chunk: str,
        is_first_chunk: bool,
    ):
        """Sends a single chunk of an agent's streaming message."""
        logger.debug(
            f"Sending agent msg chunk (ID: {message_id}, First: {is_first_chunk}) to client '{client_id}'"
        )
        update_data = {
            "type": "agent_message_chunk",
            "payload": {
                "topic_id": topic_id,
                "message_id": message_id,
                "content_chunk": content_chunk,
                "is_first_chunk": is_first_chunk,
                # Add timestamp if needed, though less critical for chunks
                # "timestamp": now_tz().isoformat()
            },
        }
        # Use mode='json' if timestamp is included and needs serialization
        await connection_manager.send_json(update_data, client_id)

    async def send_agent_stream_end(
        self, client_id: str, topic_id: str, message_id: str
    ):
        """Signals the end of a streamed agent message."""
        logger.debug(
            f"Sending agent msg stream end (ID: {message_id}) to client '{client_id}'"
        )
        update_data = {
            "type": "agent_stream_end",
            "payload": {"topic_id": topic_id, "message_id": message_id},
        }
        await connection_manager.send_json(update_data, client_id)


# Create a singleton instance of the ChatManager for use across the application
chat_manager = ChatManager()
