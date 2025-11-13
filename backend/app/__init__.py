from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from config.settings import get_settings
from config.logging import setup_logging
from .routes import router
from .middleware import RequestIDMiddleware, ErrorHandlingMiddleware
from .background_jobs import start_background_worker, stop_background_worker

settings = get_settings()

# Configure structured logging with request ID tracking and API key masking
setup_logging(
    log_level=settings.log_level,
    debug=settings.debug
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlingMiddleware)  # Outermost - catches all errors
app.add_middleware(RequestIDMiddleware)  # Generates request IDs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Start background worker for memory extraction
    start_background_worker()
    logger.info("Background worker started for memory extraction")


@app.on_event("shutdown")
async def shutdown_event():
    logger = logging.getLogger(__name__)
    logger.info(f"Shutting down {settings.app_name}")

    # Stop background worker
    stop_background_worker()
    logger.info("Background worker stopped")
