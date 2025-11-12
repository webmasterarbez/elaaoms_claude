from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class PayloadRequest(BaseModel):
    """Generic payload request model"""
    event_type: str = Field(..., description="Type of event being sent")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Request timestamp")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "user_signup",
                "data": {"email": "user@example.com", "name": "John Doe"},
                "user_id": "user_123"
            }
        }


class PayloadResponse(BaseModel):
    """Generic response model"""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Payload processed successfully",
                "request_id": "req_123",
                "data": {}
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = "error"
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for debugging")
    request_id: Optional[str] = Field(None, description="Request identifier")


# ElevenLabs Post-Call Webhook Models

class MessageItem(BaseModel):
    """Message item in transcript"""
    role: str = Field(..., description="Role: agent, user, etc")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    message: str = Field(..., description="Message content")
    source_medium: Optional[str] = Field(None, description="Source medium")


class TranscriptionData(BaseModel):
    """Data payload for post_call_transcription webhook"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    transcript: list = Field(..., description="List of message objects with role, message, etc")
    status: str = Field(..., description="Call status")
    duration: Optional[int] = Field(None, description="Call duration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_12345",
                "transcript": [
                    {
                        "role": "agent",
                        "message": "Hello, how can I help?",
                        "agent_id": "agent_123",
                        "source_medium": "phone"
                    }
                ],
                "status": "completed",
                "duration": 120
            }
        }


class AudioData(BaseModel):
    """Data payload for post_call_audio webhook"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    full_audio: str = Field(..., description="Base64-encoded MP3 audio data")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_12345",
                "full_audio": "/9j/4AAQSkZJRgABA..."  # truncated base64
            }
        }


class FailureMetadata(BaseModel):
    """Metadata for call_initiation_failure webhook"""
    type: Optional[str] = Field(None, description="Provider type (sip, twilio, etc)")
    body: Optional[Dict[str, Any]] = Field(None, description="Provider-specific data")


class FailureData(BaseModel):
    """Data payload for call_initiation_failure webhook"""
    agent_id: str = Field(..., description="Agent identifier")
    conversation_id: str = Field(..., description="Unique conversation identifier")
    failure_reason: Optional[str] = Field(None, description="Why the call failed")
    metadata: Optional[FailureMetadata] = Field(None, description="Provider-specific metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_123",
                "conversation_id": "conv_12345",
                "failure_reason": "Connection timeout",
                "metadata": {
                    "type": "sip",
                    "body": {"sip_status_code": 408}
                }
            }
        }


class ElevenLabsWebhook(BaseModel):
    """Wrapper for all ElevenLabs post-call webhooks"""
    type: str = Field(..., description="Webhook type: post_call_transcription, post_call_audio, or call_initiation_failure")
    data: Dict[str, Any] = Field(..., description="Webhook-specific data")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "post_call_transcription",
                "data": {
                    "conversation_id": "conv_12345",
                    "transcript": "Hello...",
                    "status": "completed"
                }
            }
        }
