import uvicorn
import logging
from config.settings import get_settings
from app import app

settings = get_settings()
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
