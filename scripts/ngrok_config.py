"""
Ngrok configuration for tunneling FastAPI service
Usage: python ngrok_config.py
"""

import subprocess
import logging
import os
import sys
import shutil
import time
from pathlib import Path

# Add backend directory to path so we can import config module
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def cleanup_old_ngrok_configs():
    """
    Remove old ngrok config files to prevent conflicts.
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

        logger.info("Old ngrok configs cleaned up")
    except Exception as e:
        logger.warning(f"Could not cleanup old ngrok configs: {str(e)}")


def start_ngrok():
    """Start ngrok tunnel and print the public URL"""
    try:
        # Check if ngrok is installed
        result = subprocess.run(["which", "ngrok"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("ngrok is not installed. Please install ngrok first.")
            print("Error: ngrok is not installed. Please install ngrok first.")
            return

        ngrok_path = result.stdout.strip()
        logger.info(f"Using ngrok from: {ngrok_path}")

        # Set auth token if provided
        if settings.ngrok_authtoken:
            logger.info("Setting ngrok auth token")
            subprocess.run(
                [ngrok_path, "config", "add-authtoken", settings.ngrok_authtoken],
                capture_output=True
            )

        # Start ngrok tunnel on port 8000
        logger.info("Starting ngrok tunnel on port 8000")
        cmd = [ngrok_path, "http", "8000", "--log", "stdout"]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        print(f"\n{'='*60}")
        print("Ngrok tunnel started")
        print(f"{'='*60}\n")

        # Keep the tunnel open and stream output
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line, end='')

            # Look for the public URL in the output
            if "forwarding" in line.lower() and "http" in line.lower():
                logger.info(f"Ngrok output: {line}")

    except KeyboardInterrupt:
        logger.info("Ngrok tunnel stopped by user")
        print("\nNgrok tunnel stopped")
    except Exception as e:
        logger.error(f"Error starting ngrok: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Clean up old configs first
    cleanup_old_ngrok_configs()
    # Then start ngrok
    start_ngrok()
