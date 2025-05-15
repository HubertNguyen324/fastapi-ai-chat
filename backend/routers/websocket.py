import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.connection_manager import connection_manager
from backend.services.chat_manager import chat_manager
from backend.services.agent_manager import agent_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Handles WebSocket connections for real-time chat communication.

    - Accepts connection and registers with ConnectionManager.
    - Handles initial state synchronization (agents, topics, active topic).
    - Listens for incoming messages from the client.
    - Routes client messages to appropriate ChatManager actions.
    - Handles disconnection and cleanup.
    """
    # Attempt to connect and register the client
    connected = await connection_manager.connect(websocket, client_id)
    if not connected:
        # ConnectionManager already logged the reason (e.g., duplicate) and closed the socket
        return

    initial_topic_id: str | None = None  # Ensure defined scope
    try:
        # --- Initial Connection Setup ---
        # Handle session creation or retrieval for the connecting client
        initial_topic_id = await chat_manager.handle_connect(client_id)
        # Note: handle_connect returns None for new sessions, active_topic_id for reconnects

        # Send essential initial state for the frontend to initialize
        logger.info(
            f"Sending initial state for '{client_id}'. Active topic ID: {initial_topic_id}"
        )
        agents = agent_manager.list_agents()
        await connection_manager.send_json(
            {
                "type": "initial_state",
                "payload": {
                    "client_id": client_id,
                    "agents": [agent.model_dump() for agent in agents],
                    "active_topic_id": initial_topic_id,  # Can be null
                },
            },
            client_id,
        )

        # Always send the topic list (might be empty for new clients)
        await chat_manager.send_topic_list_update(client_id)

        # If reconnecting to an existing active topic, send its full state
        if initial_topic_id:
            logger.info(f"Sending initial full state for topic '{initial_topic_id}'")
            await chat_manager.send_full_topic_state(client_id, initial_topic_id)
        else:
            # Expected for new sessions, frontend shows welcome screen
            logger.info(
                f"No initial active topic for client '{client_id}'; welcome state expected."
            )

        # ==================================
        # Main Message Processing Loop
        # ==================================
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            try:
                # Parse the incoming JSON message
                message_data = json.loads(data)
                message_type = message_data.get("type")
                payload = message_data.get("payload", {})
                # Get topic_id from payload if present, used by several actions
                received_topic_id = payload.get("topic_id")

                logger.debug(
                    f"Received message type: '{message_type}' from '{client_id}'"
                )

                # Update session activity on any valid message reception
                chat_manager._update_last_activity(client_id)

                # --- Route message based on its type ---
                if message_type == "send_message":
                    content = payload.get("content")
                    # Agent selected in the UI when the message was sent
                    current_agent_id = payload.get("current_agent_id")

                    # Validate required payload fields
                    if not content or not current_agent_id:
                        logger.warning(
                            f"Missing content or current_agent_id for send_message from '{client_id}'"
                        )
                        continue  # Ignore invalid message

                    # Determine if this message starts a new topic or belongs to an existing one
                    topic = (
                        chat_manager.get_topic(received_topic_id)
                        if received_topic_id
                        else None
                    )

                    # Scenario 1: Start a new chat topic
                    if received_topic_id is None:
                        logger.info(
                            f"First message in new topic flow for client '{client_id}' with agent '{current_agent_id}'"
                        )
                        new_topic = await chat_manager.create_topic(
                            client_id, current_agent_id
                        )
                        if new_topic:
                            # Process the message within the new topic context
                            await chat_manager.add_message_and_process(
                                client_id, new_topic.id, content
                            )
                            # Explicitly tell frontend the new topic is now active
                            await chat_manager.send_active_topic_update(
                                client_id, new_topic.id
                            )
                        else:
                            # Handle potential failure to create topic
                            logger.error(
                                f"Failed to create new topic for client '{client_id}'"
                            )
                            await connection_manager.send_json(
                                {
                                    "type": "error",
                                    "payload": {"detail": "Failed to start new chat."},
                                },
                                client_id,
                            )

                    # Scenario 2: Agent changed mid-conversation for an existing topic
                    elif topic and topic.agent_id != current_agent_id:
                        logger.info(
                            f"Agent changed mid-topic for client '{client_id}'. Creating new topic with agent '{current_agent_id}'."
                        )
                        # Service function handles creating new topic, setting active, processing message
                        new_topic_id = await chat_manager.change_agent_for_topic(
                            client_id, received_topic_id, current_agent_id, content
                        )
                        if new_topic_id:
                            # Inform frontend about the new active topic ID
                            await chat_manager.send_active_topic_update(
                                client_id, new_topic_id
                            )
                        else:
                            logger.error(
                                f"Failed to create new topic during agent change for client '{client_id}'"
                            )
                            await connection_manager.send_json(
                                {
                                    "type": "error",
                                    "payload": {"detail": "Failed to switch agent."},
                                },
                                client_id,
                            )

                    # Scenario 3: Standard message to an existing topic
                    elif topic:
                        # Process message within the existing topic context
                        await chat_manager.add_message_and_process(
                            client_id, received_topic_id, content
                        )

                    # Scenario 4: Message sent with a topic_id that doesn't exist
                    else:  # topic is None but received_topic_id was not None
                        logger.warning(
                            f"Received message for non-existent topic_id '{received_topic_id}' from client '{client_id}'. Ignoring."
                        )
                        await connection_manager.send_json(
                            {
                                "type": "error",
                                "payload": {
                                    "detail": f"Topic '{received_topic_id}' not found."
                                },
                            },
                            client_id,
                        )

                elif message_type == "select_topic":
                    # Client requests to view a different topic
                    if received_topic_id:
                        topic = chat_manager.get_topic(received_topic_id)
                        session = chat_manager.sessions.get(client_id)
                        # Validate topic existence, ownership, and session
                        if topic and session and topic.client_id == client_id:
                            logger.info(
                                f"Client '{client_id}' selected topic '{received_topic_id}'"
                            )
                            session.active_topic_id = (
                                received_topic_id  # Update server-side session state
                            )
                            # Send the full message/result history for the selected topic
                            await chat_manager.send_full_topic_state(
                                client_id, received_topic_id
                            )
                            # Confirm the active topic change to the frontend
                            await chat_manager.send_active_topic_update(
                                client_id, received_topic_id
                            )
                        else:
                            # Log and optionally inform client of invalid selection
                            logger.warning(
                                f"Client '{client_id}' tried to select invalid/mismatched topic '{received_topic_id}'"
                            )
                            await connection_manager.send_json(
                                {
                                    "type": "error",
                                    "payload": {
                                        "detail": f"Cannot select topic '{received_topic_id}'."
                                    },
                                },
                                client_id,
                            )
                    else:
                        logger.warning(
                            f"Missing topic_id for 'select_topic' message from '{client_id}'"
                        )

                elif message_type == "ping":
                    # Simple keepalive mechanism initiated by client
                    await connection_manager.send_json({"type": "pong"}, client_id)

                # TODO: Add handlers for other client actions (e.g., delete topic, rename topic)

                else:
                    # Handle unknown message types
                    logger.warning(
                        f"Unknown message type '{message_type}' received from '{client_id}'"
                    )

            # --- Inner Exception Handling (Message Processing Loop) ---
            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON from client '{client_id}': {data}")
                # Optionally send error back to client
            except WebSocketDisconnect:
                # This indicates the client disconnected while processing a message
                logger.warning(
                    f"WebSocket disconnected during message processing loop for '{client_id}'."
                )
                raise  # Re-raise to be caught by the outer handler
            except Exception as e:
                # Catch unexpected errors during the processing of a single message
                logger.error(
                    f"Error processing message from client '{client_id}': {e}",
                    exc_info=True,
                )
                # Attempt to send a generic error message back to the client
                try:
                    await connection_manager.send_json(
                        {
                            "type": "error",
                            "payload": {
                                "detail": "Internal server error processing your request."
                            },
                        },
                        client_id,
                    )
                except Exception:
                    pass  # Avoid cascading errors if sending the error fails

    # --- Outer Exception Handling (WebSocket Connection Lifecycle) ---
    except WebSocketDisconnect as e:
        # Handles both clean and unclean disconnects initiated by client or server
        logger.info(
            f"WebSocket disconnected for client '{client_id}'. Code: {e.code}, Reason: '{e.reason}'"
        )
    except Exception as e:
        # Catch unexpected errors during connection setup or the main loop itself
        logger.error(
            f"Unhandled exception in WebSocket endpoint for client '{client_id}': {e}",
            exc_info=True,
        )
        # Attempt to close the connection gracefully if it seems open
        if client_id in connection_manager.active_connections:
            try:
                # Use code 1011 for Internal Server Error
                await websocket.close(code=1011, reason="Internal server error")
            except Exception as close_err:
                # Log error during the forced close attempt
                logger.error(
                    f"Error attempting to close WebSocket for '{client_id}' after exception: {close_err}"
                )
    finally:
        # CRITICAL: Ensure the client is removed from the ConnectionManager
        # regardless of how the connection endpoint exits (normal disconnect, error, etc.)
        connection_manager.disconnect(client_id)
        logger.info(f"Cleaned up connection manager entry for client '{client_id}'")
