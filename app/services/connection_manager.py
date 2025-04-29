# In app/services/connection_manager.py
import logging
from fastapi import WebSocket  # Ensure WebSocket is imported if not already
from typing import Dict, List
import json  # Import json if needed for specific error handling later

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id in self.active_connections:
            logger.warning(
                f"Client {client_id} attempting duplicate connection. Closing new attempt."
            )
            await websocket.close(code=1008, reason="Session already active")
            return False
        self.active_connections[client_id] = websocket
        logger.info(
            f"Client {client_id} connected. Total connections: {len(self.active_connections)}"
        )
        return True

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Ensure the websocket object is removed
            removed_ws = self.active_connections.pop(client_id, None)
            if removed_ws:
                logger.info(
                    f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}"
                )
            else:
                # This case should ideally not happen if disconnect is called correctly
                logger.warning(
                    f"Disconnect called for client {client_id}, but no active WebSocket was found in manager."
                )
        # else: # No need to log if disconnect is called for an already disconnected client
        # logger.debug(f"Disconnect called for non-existent client {client_id}.")

    async def send_personal_message(self, message: str, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(
                    f"Error sending text message to {client_id}: {e}", exc_info=True
                )
        # else: # Optionally log if websocket not found for text message
        #    logger.warning(f"[WS Send Text] WebSocket not found for active client_id {client_id}")

    async def send_json(self, data: dict, client_id: str):
        """Sends JSON data, adding logging for message type and ID."""
        websocket = self.active_connections.get(client_id)
        if websocket:  # Check if connection exists for this client_id
            try:
                log_type = data.get("type", "N/A")
                log_payload = data.get("payload", {})
                log_msg_id = (
                    log_payload.get("id", "N/A")
                    if isinstance(log_payload, dict)
                    else "N/A"
                )
                # Log BEFORE attempting send
                logger.info(
                    f"[WS Send] Attempting to send JSON to {client_id}. Type='{log_type}', PayloadID='{log_msg_id}'"
                )
                await websocket.send_json(data)  # The actual send operation
                logger.debug(
                    f"[WS Send] Successfully sent JSON to {client_id}. Type='{log_type}'"
                )  # Log success

            except Exception as e:
                logger.error(
                    f"Error sending JSON to {client_id} (Type='{data.get('type')}'): {e}",
                    exc_info=True,
                )
                # Consider disconnecting if send fails persistently
                # self.disconnect(client_id) # Be careful with auto-disconnect on send failure
        else:
            # --- ADD THIS LOG ---
            log_type = data.get("type", "N/A")
            logger.warning(
                f"[WS Send] WebSocket NOT FOUND for active client_id '{client_id}' when trying to send type '{log_type}'"
            )
            # --- END ADDED LOG ---

    async def broadcast(self, message: str):
        # Use sparingly
        disconnected_clients = []
        active_connections_copy = list(
            self.active_connections.items()
        )  # Iterate over a copy
        for client_id, connection in active_connections_copy:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)

        for client_id in disconnected_clients:
            self.disconnect(client_id)


# Singleton instance
connection_manager = ConnectionManager()
