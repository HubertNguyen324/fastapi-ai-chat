from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Web Interface"])

# Configure Jinja2 templates
# Assumes templates are in 'app/templates' relative to the project root
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def get_index_page(request: Request):
    """
    Serves the main HTML page for the single-page application.
    """
    logger.info(f"Serving index.html for request: {request.url}")
    # Pass the request object to the template, necessary for Jinja2/Starlette
    return templates.TemplateResponse("index.html", {"request": request})


# You could add other web routes here if needed (e.g., /about page)
