from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.agent_manager import agent_manager  # Import instance

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    # You could pass initial data here if needed, but agents are sent via WS
    return templates.TemplateResponse("index.html", {"request": request})
