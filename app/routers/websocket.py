import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.connection_manager import connection_manager  # Import instance
from app.services.chat_manager import chat_manager  # Import instance
from app.services.agent_manager import agent_manager  # Import instance

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    connected = await connection_manager.connect(websocket, client_id)
    if not connected:
        logger.warning(
            f"WebSocket connection rejected for duplicate client_id: {client_id}"
        )
        return  # Connection already closed by manager

    initial_topic_id = None
    try:
        # Handle initial setup or reconnect for the client
        initial_topic_id = await chat_manager.handle_connect(client_id)

        # Send initial state (agents, topics, active topic + state)
        logger.info(
            f"Sending initial state for {client_id}. Active topic: {initial_topic_id}"
        )  # Add log
        agents = agent_manager.list_agents()
        await connection_manager.send_json(
            {
                "type": "initial_state",
                "payload": {
                    "client_id": client_id,
                    "agents": [agent.model_dump() for agent in agents],
                    "active_topic_id": initial_topic_id,  # Sends null if it's null
                },
            },
            client_id,
        )
        await chat_manager.send_topic_list_update(
            client_id
        )  # Sends empty list if needed

        # Send full state only if a topic exists and is active
        if initial_topic_id:
            logger.info(f"Sending initial full state for topic {initial_topic_id}")
            await chat_manager.send_full_topic_state(client_id, initial_topic_id)
        else:
            # This log is now expected for new sessions
            logger.info(
                f"No initial active topic for client {client_id}, skipping initial topic state send."
            )

        # Main loop to listen for messages
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                payload = message_data.get("payload", {})
                received_topic_id = payload.get("topic_id")  # Topic ID sent from client

                logger.debug(
                    f"Received message type: '{message_type}' from {client_id}"
                )

                # Update activity on any valid message received
                chat_manager._update_last_activity(client_id)

                if message_type == "send_message":
                    content = payload.get("content")
                    current_agent_id = payload.get("current_agent_id")

                    if not content or not current_agent_id:
                        logger.warning(
                            f"Missing content or current_agent_id for send_message from {client_id}"
                        )
                        continue

                    topic = (
                        chat_manager.get_topic(received_topic_id)
                        if received_topic_id
                        else None
                    )

                    # Case 1: New topic flow (no topic_id sent)
                    if received_topic_id is None:
                        logger.info(
                            f"First message in new topic flow for client {client_id}"
                        )
                        new_topic = await chat_manager.create_topic(
                            client_id, current_agent_id
                        )
                        if new_topic:
                            await chat_manager.add_message_and_process(
                                client_id, new_topic.id, content
                            )
                            await chat_manager.send_active_topic_update(
                                client_id, new_topic.id
                            )
                        else:
                            logger.error(
                                f"Failed to create new topic for client {client_id}"
                            )
                            # Inform client? Maybe send an error message
                            await connection_manager.send_json(
                                {
                                    "type": "error",
                                    "payload": {
                                        "detail": "Failed to create new topic."
                                    },
                                },
                                client_id,
                            )
                            await chat_manager.send_topic_list_update(
                                client_id
                            )  # Sends empty list initially

                            # This condition correctly skips sending full state if initial_topic_id is None
                            if initial_topic_id:
                                await chat_manager.send_full_topic_state(
                                    client_id, initial_topic_id
                                )
                            else:
                                logger.info(
                                    f"No initial active topic for client {client_id}, skipping initial state send."
                                )  # Correct log message

                    # Case 2: Agent changed mid-topic (topic_id exists but agent mismatch)
                    elif topic and topic.agent_id != current_agent_id:
                        logger.info(
                            f"Agent changed mid-topic for client {client_id}. Creating new topic."
                        )
                        # change_agent_for_topic creates new topic, sets it active, sends first message
                        new_topic_id = await chat_manager.change_agent_for_topic(
                            client_id, received_topic_id, current_agent_id, content
                        )
                        if new_topic_id:
                            # Send update so frontend knows the *new* active topic ID explicitly
                            await chat_manager.send_active_topic_update(
                                client_id, new_topic_id
                            )
                        else:
                            logger.error(
                                f"Failed to create new topic during agent change for client {client_id}"
                            )

                    # Case 3: Standard message to existing topic
                    elif topic:
                        await chat_manager.add_message_and_process(
                            client_id, received_topic_id, content
                        )

                    # Case 4: Invalid topic ID sent
                    else:  # topic is None but received_topic_id was not None
                        logger.warning(
                            f"Received message for non-existent topic_id '{received_topic_id}' from client {client_id}. Ignoring."
                        )

                elif message_type == "select_topic":
                    if received_topic_id:
                        topic = chat_manager.get_topic(received_topic_id)
                        session = chat_manager.sessions.get(client_id)
                        if topic and session and topic.client_id == client_id:
                            session.active_topic_id = (
                                received_topic_id  # Update active topic in session
                            )
                            await chat_manager.send_full_topic_state(
                                client_id, received_topic_id
                            )  # Send state for the selected topic
                            await chat_manager.send_active_topic_update(
                                client_id, received_topic_id
                            )  # Confirm active topic change
                        else:
                            logger.warning(
                                f"Client {client_id} tried to select invalid/mismatched topic {received_topic_id}"
                            )
                    else:
                        logger.warning(
                            f"Missing topic_id for select_topic from {client_id}"
                        )

                elif message_type == "ping":
                    await connection_manager.send_json({"type": "pong"}, client_id)

                else:
                    logger.warning(
                        f"Unknown message type received from {client_id}: {message_type}"
                    )

            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON from {client_id}: {data}")
            except WebSocketDisconnect:
                # Re-raise to be caught by outer handler
                raise
            except Exception as e:
                logger.error(
                    f"Error processing message from {client_id}: {e}", exc_info=True
                )
                # Optionally send an error message back to the client
                try:
                    await connection_manager.send_json(
                        {
                            "type": "error",
                            "payload": {
                                "detail": "Internal server error processing message."
                            },
                        },
                        client_id,
                    )
                except Exception:
                    pass  # Avoid errors during error reporting

    except WebSocketDisconnect as e:
        logger.info(
            f"WebSocket disconnected for client {client_id}. Code: {e.code}, Reason: {e.reason}"
        )
    except Exception as e:
        logger.error(
            f"Unhandled exception in WebSocket endpoint for client {client_id}: {e}",
            exc_info=True,
        )
        # Ensure connection is closed if error occurs before/during main loop
        if client_id in connection_manager.active_connections:
            try:
                await connection_manager.active_connections[client_id].close(
                    code=1011, reason="Internal server error"
                )
            except Exception:
                pass  # Ignore errors during forced close
    finally:
        # This ensures the connection manager cleans up on ANY exit path
        connection_manager.disconnect(client_id)
        logger.info(f"Cleaned up connection manager entry for client {client_id}")
