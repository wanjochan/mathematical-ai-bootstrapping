"""Main FastAPI application for CyberCorp Server."""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_config, config_manager
from .models import *
from .auth import auth_manager
from .monitoring import monitoring_service
from .websocket import websocket_manager
from .database import database_manager
from .logging_config import setup_logging
from .routers import (
    auth_router,
    system_router,
    windows_router,
    processes_router,
    config_router,
    websocket_router,
    employees_router,
    tasks_router,
)


class CyberCorpServer:
    """Main CyberCorp Server application."""
    
    def __init__(self):
        """Initialize the server."""
        self.config = get_config()
        self.app: Optional[FastAPI] = None
        self.logger = logging.getLogger(__name__)
        self._shutdown_event = asyncio.Event()
        
    async def create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan manager."""
            # Startup
            await self.startup()
            yield
            # Shutdown
            await self.shutdown()
        
        # Create FastAPI app
        app = FastAPI(
            title="CyberCorp Server",
            description="Production-ready background service for system monitoring and control",
            version="1.0.0",
            docs_url="/docs" if self.config.debug else None,
            redoc_url="/redoc" if self.config.debug else None,
            lifespan=lifespan,
        )
        
        # Configure middleware
        self._configure_middleware(app)
        
        # Configure exception handlers
        self._configure_exception_handlers(app)
        
        # Include routers
        self._include_routers(app)
        
        # Add health check endpoint
        self._add_health_check(app)
        
        self.app = app
        return app
    
    def _configure_middleware(self, app: FastAPI):
        """Configure middleware."""
        
        # CORS middleware
        if self.config.cors.enabled:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors.allow_origins,
                allow_credentials=self.config.cors.allow_credentials,
                allow_methods=self.config.cors.allow_methods,
                allow_headers=self.config.cors.allow_headers,
            )
        
        # Trusted host middleware
        if not self.config.debug:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=["localhost", "127.0.0.1", self.config.server.host]
            )
        
        # Request logging middleware
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = asyncio.get_event_loop().time()
            
            # Process request
            response = await call_next(request)
            
            # Log request
            process_time = asyncio.get_event_loop().time() - start_time
            self.logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            return response
    
    def _configure_exception_handlers(self, app: FastAPI):
        """Configure exception handlers."""
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions."""
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": f"HTTP_{exc.status_code}",
                        "message": exc.detail,
                    }
                }
            )
        
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            """Handle validation errors."""
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "details": exc.errors(),
                    }
                }
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions."""
            self.logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                    }
                }
            )
    
    def _include_routers(self, app: FastAPI):
        """Include API routers."""
        
        # API v1 prefix
        api_prefix = "/api/v1"
        
        # Include routers
        app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
        app.include_router(system_router, prefix=f"{api_prefix}/system", tags=["System"])
        app.include_router(windows_router, prefix=f"{api_prefix}/windows", tags=["Windows"])
        app.include_router(processes_router, prefix=f"{api_prefix}/processes", tags=["Processes"])
        app.include_router(config_router, prefix=f"{api_prefix}/config", tags=["Configuration"])
        app.include_router(websocket_router, prefix=f"{api_prefix}/ws", tags=["WebSocket"])
        app.include_router(employees_router, prefix=f"{api_prefix}/employees", tags=["Employees"])
        app.include_router(tasks_router, prefix=f"{api_prefix}/tasks", tags=["Tasks"])
    
    def _add_health_check(self, app: FastAPI):
        """Add health check endpoint."""
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "services": {
                    "database": await database_manager.health_check(),
                    "monitoring": monitoring_service.is_running(),
                    "websocket": websocket_manager.is_running(),
                }
            }
        
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "CyberCorp Server",
                "version": "1.0.0",
                "docs": "/docs" if self.config.debug else None,
            }
    
    async def startup(self):
        """Application startup tasks."""
        self.logger.info("Starting CyberCorp Server...")
        
        try:
            # Initialize database
            await database_manager.initialize()
            self.logger.info("Database initialized")
            
            # Initialize authentication
            await auth_manager.initialize()
            self.logger.info("Authentication system initialized")
            
            # Start monitoring service
            if self.config.monitoring.enabled:
                await monitoring_service.start()
                self.logger.info("Monitoring service started")
            
            # Start WebSocket manager
            if self.config.websocket.enabled:
                await websocket_manager.start()
                self.logger.info("WebSocket manager started")
            
            # Setup configuration hot reload
            config_manager.add_watcher(self._on_config_change)
            
            self.logger.info("CyberCorp Server started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """Application shutdown tasks."""
        self.logger.info("Shutting down CyberCorp Server...")
        
        try:
            # Stop WebSocket manager
            await websocket_manager.stop()
            self.logger.info("WebSocket manager stopped")
            
            # Stop monitoring service
            await monitoring_service.stop()
            self.logger.info("Monitoring service stopped")
            
            # Close database connections
            await database_manager.close()
            self.logger.info("Database connections closed")
            
            self.logger.info("CyberCorp Server shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    async def _on_config_change(self, old_config, new_config):
        """Handle configuration changes."""
        self.logger.info("Configuration changed, applying updates...")
        
        try:
            # Update monitoring service
            if old_config.monitoring.enabled != new_config.monitoring.enabled:
                if new_config.monitoring.enabled:
                    await monitoring_service.start()
                else:
                    await monitoring_service.stop()
            
            # Update WebSocket manager
            if old_config.websocket.enabled != new_config.websocket.enabled:
                if new_config.websocket.enabled:
                    await websocket_manager.start()
                else:
                    await websocket_manager.stop()
            
            # Update logging configuration
            if old_config.logging != new_config.logging:
                setup_logging(new_config.logging)
            
            self.logger.info("Configuration updates applied successfully")
            
        except Exception as e:
            self.logger.error(f"Error applying configuration changes: {e}", exc_info=True)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the server."""
        # Setup logging
        setup_logging(self.config.logging)
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Create app
        app = await self.create_app()
        
        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            app,
            host=self.config.server.host,
            port=self.config.server.port,
            reload=self.config.server.reload and self.config.debug,
            workers=1,  # Always use 1 worker for WebSocket support
            log_level=self.config.logging.level.lower(),
            access_log=True,
            ssl_keyfile=self.config.ssl.key_file if self.config.ssl.enabled else None,
            ssl_certfile=self.config.ssl.cert_file if self.config.ssl.enabled else None,
        )
        
        # Create server
        server = uvicorn.Server(uvicorn_config)
        
        # Run server
        try:
            self.logger.info(
                f"Starting server on {self.config.server.host}:{self.config.server.port}"
            )
            
            # Start server in background
            server_task = asyncio.create_task(server.serve())
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            # Graceful shutdown
            self.logger.info("Initiating graceful shutdown...")
            server.should_exit = True
            await server_task
            
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
            raise


# Global server instance
server = CyberCorpServer()


async def main():
    """Main entry point."""
    try:
        await server.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())