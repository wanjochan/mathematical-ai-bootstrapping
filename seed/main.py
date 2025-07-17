"""
CyberCorp Seed Server Main Application

FastAPI application with WebSocket support and hot-reload capability.
Serves as the foundation for CyberCorp system development.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from .config import settings
from .routers import api, websocket, projects
from .core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CyberCorp Seed Server",
    description="FastAPI seed server for CyberCorp system development",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router, prefix="/api/v1", tags=["api"])
app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("CyberCorp Seed Server starting up...")
    logger.info(f"Server running in {settings.environment} mode")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("CyberCorp Seed Server shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CyberCorp Seed Server",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.environment
    }


if __name__ == "__main__":
    # Hot-reload configuration for development
    uvicorn.run(
        "seed.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    ) 