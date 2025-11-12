from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
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
from .openmemory import send_to_openmemory
from .background_jobs import get_job_processor, MemoryExtractionJob
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
            return await _handle_transcription_webhook(webhook, request_id, settings)
        elif webhook.type == "post_call_audio":
            return await _handle_audio_webhook(webhook.data, request_id, settings)
        elif webhook.type == "call_initiation_failure":
            return await _handle_failure_webhook(webhook, request_id, settings)
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


async def _handle_transcription_webhook(webhook: ElevenLabsWebhook, request_id: str, settings) -> PayloadResponse:
    """
    Handle post_call_transcription webhook with async memory extraction.
    """
    try:
        # Validate data structure
        transcription = TranscriptionData(**webhook.data)
        conversation_id = transcription.conversation_id

        logger.info(
            f"[{request_id}] Processing transcription webhook for conversation {conversation_id}, "
            f"transcript items: {len(transcription.transcript)}"
        )

        # Save transcription payload to disk
        file_path = save_transcription_payload(
            settings.elevenlabs_post_call_payload_path,
            conversation_id,
            webhook.model_dump()
        )

        logger.info(f"[{request_id}] Transcription saved to {file_path}")

        # Extract caller_id and agent_id from webhook data
        caller_id = extract_caller_id(webhook.data)
        agent_id = webhook.data.get("agent_id")

        if not caller_id:
            logger.warning(f"[{request_id}] No caller_id found, skipping memory extraction")
        elif not agent_id:
            logger.warning(f"[{request_id}] No agent_id found, skipping memory extraction")
        else:
            # Enqueue background job for memory extraction
            job = MemoryExtractionJob(
                conversation_id=conversation_id,
                agent_id=agent_id,
                caller_id=caller_id,
                transcript=transcription.transcript,
                duration=transcription.duration or 0,
                status=transcription.status
            )

            job_processor = get_job_processor()
            job_processor.enqueue_job(job)

            logger.info(
                f"[{request_id}] Enqueued memory extraction job for conversation {conversation_id}"
            )

        # Legacy: Send to OpenMemory logging (deprecated but keeping for now)
        send_to_openmemory(webhook.model_dump(), request_id)

        return PayloadResponse(
            status="success",
            message="Transcription webhook processed, memory extraction started",
            request_id=request_id,
            data={
                "file_path": file_path,
                "webhook_type": "post_call_transcription",
                "conversation_id": conversation_id,
                "transcript_items": len(transcription.transcript),
                "memory_extraction_queued": bool(caller_id and agent_id)
            }
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error handling transcription webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transcription webhook: {str(e)}"
        )


def extract_caller_id(webhook_data: dict) -> Optional[str]:
    """Extract caller_id from webhook data."""
    # First try nested structure in conversation_initiation_client_data
    conversation_init = webhook_data.get("conversation_initiation_client_data", {})
    dynamic_variables = conversation_init.get("dynamic_variables", {})
    caller_id = dynamic_variables.get("system__caller_id")

    if caller_id:
        return caller_id

    # Fall back to top-level dynamic_variables
    dynamic_variables = webhook_data.get("dynamic_variables", {})
    caller_id = dynamic_variables.get("system__caller_id")

    return caller_id


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


async def _handle_failure_webhook(webhook: ElevenLabsWebhook, request_id: str, settings) -> PayloadResponse:
    """
    Handle call_initiation_failure webhook.
    """
    try:
        # Validate data structure
        failure = FailureData(**webhook.data)
        conversation_id = failure.conversation_id

        logger.info(
            f"[{request_id}] Processing failure webhook for conversation {conversation_id}, "
            f"reason: {failure.failure_reason}"
        )

        # Save failure payload
        file_path = save_failure_payload(
            settings.elevenlabs_post_call_payload_path,
            conversation_id,
            webhook.model_dump()
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
