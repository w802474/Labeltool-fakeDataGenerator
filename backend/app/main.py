"""FastAPI application entry point for LabelTool."""
import os
import sys
from pathlib import Path
from typing import Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from loguru import logger

# Add the app directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.config.settings import settings
from app.infrastructure.api.routes import router
from app.infrastructure.api.websocket_routes import router as websocket_router
from app.infrastructure.database.config import init_database, close_database


def configure_logging():
    """Configure logging with loguru."""
    # Remove default logger
    logger.remove()
    
    # Add console logger with custom format
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=settings.log_format,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file logger for production
    log_file = "logs/labeltool.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(
        log_file,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days",
        compression="zip"
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Configure logging first
    configure_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title="LabelTool API",
        description="Intelligent Text Detection & Removal Tool",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    app.include_router(router)
    app.include_router(websocket_router)
    
    # Add static file serving for frontend (in production)
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Add startup and shutdown events
    setup_events(app)
    
    logger.info("LabelTool API application created successfully")
    return app


def setup_middleware(app: FastAPI):
    """Setup application middleware."""
    # CORS middleware
    cors_config = settings.get_cors_config()
    app.add_middleware(CORSMiddleware, **cors_config)
    
    # Error handling middleware
    @app.middleware("http")
    async def error_handling_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error in {request.method} {request.url}: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": "An internal server error occurred",
                    "detail": str(e) if settings.log_level == "DEBUG" else None
                }
            )
    
    # Request logging middleware
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        start_time = logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {request.method} {request.url} - {response.status_code}")
        return response


def cleanup_cache_directories():
    """Clean up cache directories on startup (after logging is configured)."""
    import shutil
    from datetime import datetime
    
    # Define cache directories and their cleanup rules (use Docker paths)
    cache_configs = {
        "/app/exports": {"clean_all": True},
        "/app/processed": {"clean_all": True}, 
        "/app/uploads": {"clean_all": True},
        "/app/logs": {"clean_all": False, "keep_current": True}  # Special handling for logs
    }
    
    cleaned_files = 0
    current_log_file = "/app/logs/labeltool.log"
    
    for cache_dir, config in cache_configs.items():
        try:
            if os.path.exists(cache_dir):
                if config["clean_all"]:
                    # Clean everything in this directory
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleaned_files += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            cleaned_files += 1
                    logger.info(f"🧹 Cleaned cache directory: {cache_dir}")
                elif cache_dir == "/app/logs" and config.get("keep_current"):
                    # Special handling for logs - clean old files but keep current one
                    for filename in os.listdir(cache_dir):
                        file_path = os.path.join(cache_dir, filename)
                        # Skip the current log file
                        if file_path == current_log_file:
                            continue
                        # Clean other log files (rotated, compressed, etc.)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleaned_files += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                            cleaned_files += 1
                    logger.info(f"🧹 Cleaned old log files (keeping current: labeltool.log)")
            else:
                # Create the directory if it doesn't exist
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"📁 Created cache directory: {cache_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean cache directory {cache_dir}: {e}")
    
    if cleaned_files > 0:
        logger.info(f"🗑️ Cleaned {cleaned_files} cache files/directories on startup")
    else:
        logger.info("✨ Cache directories were already clean")
    
    # Database cleanup is now handled by MySQL service restart


def setup_events(app: FastAPI):
    """Setup application startup and shutdown events."""
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger.info("Starting LabelTool API...")
        
        # Note: cleanup_cache_directories() is available but not called on startup
        # This allows preserving data between restarts for development/testing
        
        # Log configuration
        logger.info(f"API Host: {settings.api_host}:{settings.api_port}")
        logger.info(f"OCR Device: {settings.paddleocr_device}")
        logger.info(f"Upload Directory: {settings.upload_dir}")
        logger.info(f"Removal Directory: {settings.removal_dir}")
        logger.info(f"Generated Directory: {settings.generated_dir}")
        logger.info(f"Max File Size: {settings.max_file_size / 1024 / 1024:.1f}MB")
        
        # Preload PaddleOCR model at startup for faster first request
        try:
            logger.info("🚀 Preloading PaddleOCR model...")
            from app.infrastructure.ocr.global_ocr import get_global_ocr
            ocr = get_global_ocr()
            logger.info("✅ PaddleOCR model preloaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to preload PaddleOCR model: {e}")
            logger.info("PaddleOCR will be loaded on first request")
        
        # Validate directories
        try:
            settings.create_directories()
            logger.info("Required directories created/verified")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
        
        # Connect to IOPaint WebSocket service
        try:
            from app.websocket.iopaint_client import iopaint_ws_client
            logger.info("🔗 Connecting to IOPaint WebSocket service...")
            connected = await iopaint_ws_client.connect()
            if connected:
                logger.info("✅ Connected to IOPaint WebSocket service")
            else:
                logger.warning("⚠️ Failed to connect to IOPaint WebSocket service - will retry on demand")
        except Exception as e:
            logger.warning(f"⚠️ Error connecting to IOPaint WebSocket service: {e}")
        
        # Initialize database
        try:
            await init_database()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            # Continue startup even if database fails
        
        logger.info("LabelTool API startup completed")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logger.info("Shutting down LabelTool API...")
        
        # Disconnect from IOPaint WebSocket service
        try:
            from app.websocket.iopaint_client import iopaint_ws_client
            logger.info("🔌 Disconnecting from IOPaint WebSocket service...")
            await iopaint_ws_client.disconnect()
            logger.info("✅ Disconnected from IOPaint WebSocket service")
        except Exception as e:
            logger.warning(f"⚠️ Error disconnecting from IOPaint WebSocket service: {e}")
        
        # Cleanup temporary files
        try:
            from app.infrastructure.storage.file_storage import FileStorageService
            file_service = FileStorageService(
                upload_dir=settings.upload_dir,
                removal_dir=settings.removal_dir,
                generated_dir=settings.generated_dir
            )
            cleaned_count = file_service.cleanup_temp_files(older_than_hours=1)
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary files: {e}")
        
        # Close database connections
        try:
            await close_database()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing database connections: {e}")
        
        logger.info("LabelTool API shutdown completed")


# Exception handlers
def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"http_{exc.status_code}",
                "message": exc.detail,
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc} - {request.method} {request.url}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "message": str(exc),
                "path": str(request.url)
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        """Handle file not found errors."""
        logger.warning(f"File not found: {exc} - {request.method} {request.url}")
        return JSONResponse(
            status_code=404,
            content={
                "error": "file_not_found",
                "message": str(exc),
                "path": str(request.url)
            }
        )


# Create the application
app = create_app()
setup_exception_handlers(app)


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint with basic API information."""
    return {
        "name": "LabelTool API",
        "version": "1.0.0",
        "description": "Intelligent Text Detection & Removal Tool",
        "status": "healthy",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )