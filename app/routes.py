from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import uuid
import logging
import json
import base64
from .models import (
    PayloadRequest,
    PayloadResponse,
    ErrorResponse,
    ElevenLabsWebhook,
    TranscriptionData,
    AudioData,
    FailureData,
)
from .auth import verify_elevenlabs_webhook
from .storage import save_transcription_payload, save_audio_payload, save_failure_payload
from config.settings import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook/post-call", response_model=PayloadResponse)
async def receive_elevenlabs_webhook(request: Request):
    """
    Receive and process ElevenLabs post-call webhooks.

    Supports three webhook types:
    - post_call_transcription: Transcription JSON payload
    - post_call_audio: Audio file as base64-encoded data in JSON
    - call_initiation_failure: Failure notification JSON payload

    All webhooks require valid HMAC-SHA256 signature validation.
    """
    request_id = str(uuid.uuid4())
    settings = get_settings()

    try:
        # Get signature header
        signature_header = request.headers.get("elevenlabs-signature")

        # Get raw request body for HMAC validation
        body = await request.body()

        logger.debug(f"[{request_id}] Raw body length: {len(body)} bytes")

        # Verify HMAC signature
        verify_elevenlabs_webhook(
            request_body=body,
            signature_header=signature_header,
            secret=settings.elevenlabs_post_call_hmac_key
        )

        logger.info(f"[{request_id}] HMAC signature validated successfully")

        # Parse the webhook payload
        webhook_payload = json.loads(body.decode('utf-8'))
        logger.debug(f"[{request_id}] Webhook type: {webhook_payload.get('type')}")

        # Validate webhook structure
        webhook = ElevenLabsWebhook(**webhook_payload)

        # Route to appropriate handler based on webhook type
        if webhook.type == "post_call_transcription":
            return await _handle_transcription_webhook(webhook.data, request_id, settings)
        elif webhook.type == "post_call_audio":
            return await _handle_audio_webhook(webhook.data, request_id, settings)
        elif webhook.type == "call_initiation_failure":
            return await _handle_failure_webhook(webhook.data, request_id, settings)
        else:
            logger.warning(f"[{request_id}] Unknown webhook type: {webhook.type}")
            raise HTTPException(
                status_code=400,
                detail=f"Unknown webhook type: {webhook.type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid webhook: {str(e)}"
        )


async def _handle_transcription_webhook(data: dict, request_id: str, settings) -> PayloadResponse:
    """
    Handle post_call_transcription webhook.
    """
    try:
        # Validate data structure
        transcription = TranscriptionData(**data)
        conversation_id = transcription.conversation_id

        logger.info(
            f"[{request_id}] Processing transcription webhook for conversation {conversation_id}, "
            f"transcript length: {len(transcription.transcript)} chars"
        )

        # Save transcription payload
        file_path = save_transcription_payload(
            settings.elevenlabs_post_call_payload_path,
            conversation_id,
            transcription.model_dump()
        )

        logger.info(f"[{request_id}] Transcription saved to {file_path}")

        return PayloadResponse(
            status="success",
            message="Transcription webhook processed and saved",
            request_id=request_id,
            data={
                "file_path": file_path,
                "webhook_type": "post_call_transcription",
                "conversation_id": conversation_id,
                "transcript_length": len(transcription.transcript)
            }
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error handling transcription webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transcription webhook: {str(e)}"
        )


async def _handle_audio_webhook(data: dict, request_id: str, settings) -> PayloadResponse:
    """
    Handle post_call_audio webhook with base64-encoded audio data.
    """
    try:
        # Validate data structure
        audio = AudioData(**data)
        conversation_id = audio.conversation_id

        logger.info(
            f"[{request_id}] Processing audio webhook for conversation {conversation_id}, "
            f"base64 data length: {len(audio.full_audio)} chars"
        )

        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio.full_audio)
        except Exception as e:
            logger.error(f"[{request_id}] Failed to decode base64 audio: {str(e)}")
            raise ValueError(f"Invalid base64 audio data: {str(e)}")

        logger.debug(f"[{request_id}] Decoded audio size: {len(audio_bytes)} bytes")

        # Save audio file
        file_path = save_audio_payload(
            settings.elevenlabs_post_call_payload_path,
            conversation_id,
            audio_bytes
        )

        logger.info(f"[{request_id}] Audio saved to {file_path}")

        return PayloadResponse(
            status="success",
            message="Audio webhook processed and saved",
            request_id=request_id,
            data={
                "file_path": file_path,
                "webhook_type": "post_call_audio",
                "conversation_id": conversation_id,
                "audio_size": len(audio_bytes),
                "base64_size": len(audio.full_audio)
            }
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error handling audio webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio webhook: {str(e)}"
        )


async def _handle_failure_webhook(data: dict, request_id: str, settings) -> PayloadResponse:
    """
    Handle call_initiation_failure webhook.
    """
    try:
        # Validate data structure
        failure = FailureData(**data)
        conversation_id = failure.conversation_id

        logger.info(
            f"[{request_id}] Processing failure webhook for conversation {conversation_id}, "
            f"reason: {failure.failure_reason}"
        )

        # Save failure payload
        file_path = save_failure_payload(
            settings.elevenlabs_post_call_payload_path,
            conversation_id,
            failure.model_dump()
        )

        logger.info(f"[{request_id}] Failure recorded to {file_path}")

        return PayloadResponse(
            status="success",
            message="Failure webhook processed and saved",
            request_id=request_id,
            data={
                "file_path": file_path,
                "webhook_type": "call_initiation_failure",
                "conversation_id": conversation_id,
                "failure_reason": failure.failure_reason,
                "agent_id": failure.agent_id
            }
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error handling failure webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid failure webhook: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Service is running"}


@router.post("/echo")
async def echo_payload(payload: PayloadRequest):
    """
    Echo endpoint for testing - returns the payload back
    """
    request_id = str(uuid.uuid4())
    return PayloadResponse(
        status="success",
        message="Echo received",
        request_id=request_id,
        data=payload.model_dump()
    )
