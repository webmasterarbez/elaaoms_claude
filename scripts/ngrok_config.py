"""
Ngrok configuration for tunneling FastAPI service
Usage: python ngrok_config.py
"""

from pyngrok import ngrok
import logging
import os
import shutil
from pathlib import Path
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def cleanup_old_ngrok_binaries():
    """
    Remove old ngrok binaries to prevent version conflicts.
    This ensures pyngrok downloads a fresh, compatible version.
    """
    try:
        # Clear ngrok config directories
        ngrok_config_paths = [
            Path.home() / ".ngrok2",
            Path.home() / ".config" / "ngrok",
        ]

        for path in ngrok_config_paths:
            if path.exists():
                logger.info(f"Clearing ngrok config directory: {path}")
                shutil.rmtree(path, ignore_errors=True)

        logger.info("Old ngrok binaries and configs cleaned up")
    except Exception as e:
        logger.warning(f"Could not cleanup old ngrok binaries: {str(e)}")


def start_ngrok():
    """Start ngrok tunnel and print the public URL"""
    try:
        if settings.ngrok_authtoken:
            ngrok.set_auth_token(settings.ngrok_authtoken)

        # Start ngrok tunnel on port 8000
        public_url = ngrok.connect(8000, "http")
        logger.info(f"Ngrok tunnel started: {public_url}")
        print(f"\n{'='*60}")
        print(f"Ngrok Public URL: {public_url}")
        print(f"{'='*60}\n")

        # Keep the tunnel open
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()

    except Exception as e:
        logger.error(f"Error starting ngrok: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Clean up old binaries first
    cleanup_old_ngrok_binaries()
    # Then start ngrok
    start_ngrok()
