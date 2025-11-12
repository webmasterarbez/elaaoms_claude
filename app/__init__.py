from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from config.settings import get_settings
from .routes import router

settings = get_settings()

# Configure logging
log_level = settings.log_level
# Set to DEBUG for development
if settings.debug:
    log_level = "DEBUG"

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add CORS middleware
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


@app.on_event("shutdown")
async def shutdown_event():
    logger = logging.getLogger(__name__)
    logger.info(f"Shutting down {settings.app_name}")
