import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.routers import web, websocket
from app.services.chat_manager import chat_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the session cleanup task
    await chat_manager.start_cleanup_task()
    yield
    await chat_manager.stop_cleanup_task()


app = FastAPI(title="AI Agent App", lifespan=lifespan)

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(web.router)
app.include_router(websocket.router)
