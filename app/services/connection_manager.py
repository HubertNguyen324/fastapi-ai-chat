import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Responsibilities:
    - Storing active connections mapped by client_id.
    - Handling connection acceptance and preventing duplicates.
    - Providing methods to send messages (text, JSON) to specific clients.
    - Handling disconnection cleanup.
    """

    def __init__(self):
        # dictionary to store active WebSocket connections {client_id: WebSocket}
        self.active_connections: dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized.")

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """
        Accepts a WebSocket connection and stores it if the client_id is not already connected.

        Args:
            websocket: The WebSocket connection object.
            client_id: The unique identifier for the client.

        Returns:
            True if the connection was accepted, False if rejected (duplicate).
        """
        await websocket.accept()
        # Prevent multiple active connections for the same client ID
        if client_id in self.active_connections:
            logger.warning(
                f"Client '{client_id}' attempting duplicate connection. Closing new attempt."
            )
            # Send a specific close code and reason
            await websocket.close(code=1008, reason="Session already active")
            return False  # Indicate connection failed

        self.active_connections[client_id] = websocket
        logger.info(
            f"Client '{client_id}' connected. Total connections: {len(self.active_connections)}"
        )
        return True  # Indicate connection successful

    def disconnect(self, client_id: str):
        """
        Removes a client's WebSocket connection from the manager.
        Safe to call even if the client is already disconnected.
        """
        if client_id in self.active_connections:
            # Remove the websocket object from the dictionary
            removed_ws = self.active_connections.pop(client_id, None)
            if removed_ws:
                logger.info(
                    f"Client '{client_id}' disconnected. Total connections: {len(self.active_connections)}"
                )
            # else: # This case implies disconnect was called after pop already happened, likely okay.
            #     logger.debug(f"Disconnect called for '{client_id}', but WebSocket already removed.")
        # else: # No need to log if disconnect is called for a client not currently tracked
        # logger.debug(f"Disconnect called for non-tracked client '{client_id}'.")

    async def send_personal_message(self, message: str, client_id: str):
        """Sends a plain text message to a specific connected client."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception as e:
                # Log errors during send attempts, connection might be closing
                logger.error(
                    f"Error sending text message to '{client_id}': {e}", exc_info=True
                )
                # Consider closing the connection if send fails repeatedly
                # await self._handle_send_error(client_id)
        # else: # Optional: Log if trying to send to a client not currently connected
        #     logger.warning(f"[WS Send Text] WebSocket not found for client_id '{client_id}'")

    async def send_json(self, data: dict, client_id: str):
        """
        Sends JSON serializable data to a specific connected client.
        Logs message type and payload ID for debugging.
        """
        websocket = self.active_connections.get(client_id)
        if websocket:  # Check if connection exists for this client_id
            try:
                # Extract info for logging before sending
                log_type = data.get("type", "N/A")
                log_payload = data.get("payload", {})
                # Safely get 'id' from payload if it's a dictionary
                log_msg_id = (
                    log_payload.get("id", "N/A")
                    if isinstance(log_payload, dict)
                    else "N/A"
                )

                logger.info(
                    f"[WS Send] Attempting to send JSON to '{client_id}'. Type='{log_type}', PayloadID='{log_msg_id}'"
                )
                await websocket.send_json(data)  # Perform the send operation
                logger.debug(
                    f"[WS Send] Successfully sent JSON to '{client_id}'. Type='{log_type}'"
                )

            except Exception as e:
                # Log errors during send, connection might be closing
                logger.error(
                    f"Error sending JSON to '{client_id}' (Type='{data.get('type', 'N/A')}'): {e}",
                    exc_info=True,
                )
                # Consider common error handling, e.g., closing the connection
                # await self._handle_send_error(client_id)
        else:
            # Log clearly if the intended recipient is not connected
            log_type = data.get("type", "N/A")
            logger.warning(
                f"[WS Send] WebSocket NOT FOUND for client_id '{client_id}' when trying to send type '{log_type}'"
            )

    async def broadcast(self, message: str):
        """Sends a plain text message to ALL currently connected clients."""
        # Note: Use this function with caution, especially in scaled environments.
        # Targeted messaging via send_personal_message or send_json is usually preferred.
        disconnected_clients = []
        # Iterate over a copy of the items to avoid runtime modification errors
        active_connections_copy = list(self.active_connections.items())
        logger.info(f"Broadcasting message to {len(active_connections_copy)} clients.")

        for client_id, connection in active_connections_copy:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client '{client_id}': {e}")
                # Mark client for disconnection if broadcast fails
                disconnected_clients.append(client_id)

        # Clean up connections that failed during broadcast
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    # Optional helper for consistent send error handling
    # async def _handle_send_error(self, client_id: str):
    #     logger.warning(f"Handling send error for client '{client_id}'. Closing connection.")
    #     websocket = self.active_connections.get(client_id)
    #     if websocket:
    #         try:
    #             # Attempt graceful close with an appropriate code
    #             await websocket.close(code=1011) # Internal Server Error or similar
    #         except Exception as close_err:
    #              logger.error(f"Error during forceful close for '{client_id}': {close_err}")
    #     # Ensure removal from manager regardless of close success
    #     self.disconnect(client_id)


# Create a singleton instance for global use within the application
connection_manager = ConnectionManager()
