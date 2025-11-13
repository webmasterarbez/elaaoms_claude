"""
File storage handler for ElevenLabs webhook payloads
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def save_transcription_payload(
    base_path: str,
    conversation_id: str,
    payload_dict: dict
) -> str:
    """
    Save transcription JSON payload to disk.

    Args:
        base_path: Base directory path for payloads
        conversation_id: Unique conversation identifier
        payload_dict: Transcription payload as dictionary

    Returns:
        Path to saved file

    Raises:
        Exception: If file save fails
    """
    try:
        # Create directory structure
        directory = Path(base_path) / conversation_id
        directory.mkdir(parents=True, exist_ok=True)

        # Save JSON file
        file_path = directory / f"{conversation_id}_transcription.json"
        with open(file_path, 'w') as f:
            json.dump(payload_dict, f, indent=2, default=str)

        logger.info(f"Saved transcription payload to {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving transcription payload: {str(e)}")
        raise


def save_audio_payload(
    base_path: str,
    conversation_id: str,
    audio_data: bytes
) -> str:
    """
    Save audio file from webhook.

    Args:
        base_path: Base directory path for payloads
        conversation_id: Unique conversation identifier
        audio_data: Audio file bytes

    Returns:
        Path to saved file

    Raises:
        Exception: If file save fails
    """
    try:
        # Create directory structure
        directory = Path(base_path) / conversation_id
        directory.mkdir(parents=True, exist_ok=True)

        # Save audio file
        file_path = directory / f"{conversation_id}_audio.mp3"
        with open(file_path, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Saved audio payload to {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving audio payload: {str(e)}")
        raise


def save_failure_payload(
    base_path: str,
    conversation_id: str,
    payload_dict: dict
) -> str:
    """
    Save failure JSON payload to disk.

    Args:
        base_path: Base directory path for payloads
        conversation_id: Unique conversation identifier
        payload_dict: Failure payload as dictionary

    Returns:
        Path to saved file

    Raises:
        Exception: If file save fails
    """
    try:
        # Create directory structure
        directory = Path(base_path) / conversation_id
        directory.mkdir(parents=True, exist_ok=True)

        # Save JSON file
        file_path = directory / f"{conversation_id}_failure.json"
        with open(file_path, 'w') as f:
            json.dump(payload_dict, f, indent=2, default=str)

        logger.info(f"Saved failure payload to {file_path}")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving failure payload: {str(e)}")
        raise
