import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager  # Use async context manager for lifespan

# Import routers, services, and config
from app.routers import web, websocket
from app.services.chat_manager import chat_manager  # Import the singleton instance
from app.config import settings  # Import the settings instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detail during development
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Get a logger instance for this module
logger = logging.getLogger(__name__)


# --- Lifespan Management (Recommended for FastAPI >= 0.104.0) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for application startup and shutdown events.
    """
    # --- Startup ---
    logger.info("Application startup sequence initiated...")
    logger.info(
        f"Session timeout configured to: {settings.session_timeout_minutes} minutes"
    )
    # Start background tasks like the session cleanup
    await chat_manager.start_cleanup_task()
    logger.info("Application startup complete. Ready to accept connections.")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Application shutdown sequence initiated...")
    # Gracefully stop background tasks
    await chat_manager.stop_cleanup_task()
    # Add any other cleanup tasks (e.g., close database connections)
    logger.info("Application shutdown complete.")


# Create FastAPI app instance with lifespan manager
app = FastAPI(
    title="AI Agent Chat App",
    description="A WebSocket-based chat interface skeleton for AI agents.",
    version="0.1.0",
    lifespan=lifespan,  # Register the lifespan context manager
)

# --- Static Files ---
# Serve CSS, JS files from the 'app/static' directory at the '/static' URL path
# Check if the directory exists to avoid errors during startup if structure is wrong
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Mounted static files directory at /static")
except RuntimeError as e:
    logger.error(
        f"Failed to mount static files directory 'app/static': {e}. Ensure the directory exists."
    )
    logger.error("Static files (CSS, JS) will not be served.")


# --- Routers ---
# Include API and WebSocket routes defined in separate modules
app.include_router(web.router)
app.include_router(websocket.router)
logger.info("Included web and websocket routers.")


# --- Optional Root/Health Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Simple endpoint to check if the application is running."""
    return {"status": "ok", "message": "AI Agent Chat App is running"}
