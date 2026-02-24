"""
FastAPI Application for MortgageClear Web UI
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import config
from .api.routes import router as api_router
from .api.views import router as views_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting MortgageClear Application...")
    logger.info(f"Debug mode: {config.debug}")
    yield
    logger.info("Shutting down MortgageClear Application...")


# Create FastAPI application
app = FastAPI(
    title="MortgageClear",
    description="""
    MortgageClear — Multi-Agent Mortgage Underwriting System.

    Fan-Out/Fan-In architecture for rapid, intelligent mortgage processing:
    - Credit Analysis Agent: Analyzes credit history and DTI ratio
    - Property Valuation Agent: Evaluates property value from multiple sources
    - Fraud Detection Agent: Screens for identity and behavioral fraud
    - Person Verification Agent: Verifies applicant identity consistency
    - Aggregator Agent: Combines all results into a final underwriting decision

    Processing time: ~20-60 seconds vs 30-60 days for traditional manual underwriting
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1", tags=["API"])
app.include_router(views_router, tags=["Views"])

# Mount static files
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mortgageclear",
        "version": "2.0.0"
    }
