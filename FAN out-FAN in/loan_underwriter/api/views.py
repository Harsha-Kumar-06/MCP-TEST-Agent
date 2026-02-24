"""
View routes for serving HTML templates.
"""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

# Get template directory
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=template_dir)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/application", response_class=HTMLResponse)
async def application_form(request: Request):
    """Render the application form page."""
    return templates.TemplateResponse("application.html", {"request": request})


@router.get("/apply", response_class=HTMLResponse)
async def apply_form(request: Request):
    """Alias for application form page."""
    return templates.TemplateResponse("application.html", {"request": request})


@router.get("/results/{application_id}", response_class=HTMLResponse)
async def results_page(request: Request, application_id: str):
    """Render the results page for a specific application."""
    return templates.TemplateResponse(
        "results.html", 
        {"request": request, "application_id": application_id}
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})
