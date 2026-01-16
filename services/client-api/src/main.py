"""FastAPI application entry point."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add shared package to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared"))

from .api.routes import dashboard, debtors, calls
from .core.config import get_settings
from .core.database import verify_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup - verify database connection
    await verify_database_connection()
    yield
    # Shutdown


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(debtors.router, prefix="/debtors", tags=["Debtors"])
app.include_router(calls.router, prefix="/calls", tags=["Calls"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.api_version}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
    }
