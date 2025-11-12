# FastAPI Webhook Service

A structured FastAPI service that receives and processes webhook payloads with built-in ngrok support for public URL testing.

## Features

- **ElevenLabs Post-Call Webhooks**: Receive and process three webhook types:
  - `post_call_transcription`: Transcription JSON payloads
  - `post_call_audio`: Audio files via multipart form data
  - `call_initiation_failure`: Call failure notifications
- **HMAC-SHA256 Authentication**: All webhooks are validated using ElevenLabs-provided HMAC signatures
- **Automatic Payload Storage**: Payloads are automatically saved to disk in organized directory structure
- **Health Check**: Simple health check endpoint for monitoring
- **Echo Endpoint**: Test endpoint that echoes back received payloads
- **Swagger Documentation**: Auto-generated interactive API docs at `/docs`
- **CORS Enabled**: Accept requests from any origin
- **Request Tracking**: Every request gets a unique UUID for tracing
- **Structured Logging**: Comprehensive logging for debugging
- **Environment Configuration**: Manage settings via `.env` file
- **Ngrok Integration**: Built-in tunnel setup for testing with public URLs

## Project Structure

```
.
├── app/
│   ├── __init__.py          # FastAPI app initialization with middleware
│   ├── auth.py              # HMAC signature verification
│   ├── models.py            # Pydantic request/response models
│   ├── routes.py            # API endpoint definitions
│   └── storage.py           # File storage handlers for payloads
├── config/
│   ├── __init__.py
│   └── settings.py          # Environment and application settings
├── main.py                  # Application entry point
├── ngrok_config.py          # Ngrok tunnel configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /home/ubuntu/claude/elaaoms_claude
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   ```

   To use ngrok with authentication, add your auth token to `.env`:
   ```
   NGROK_AUTHTOKEN=your_token_here
   ```

## Quick Start

### Start the Service

In Terminal 1:
```bash
python main.py
```

The service will start on `http://localhost:8000`

### Create a Public Tunnel (Optional)

In Terminal 2:
```bash
python ngrok_config.py
```

This will print a public URL like `https://abc-123-def.ngrok.io` that you can use for testing.

## Configuration

### ElevenLabs Post-Call Webhooks Setup

Before using the webhook endpoints, configure the required environment variables in your `.env` file:

```env
ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret_key_from_elevenlabs
ELEVENLABS_POST_CALL_PAYLOAD_PATH=./payloads
```

- **ELEVENLABS_POST_CALL_HMAC_KEY**: The shared secret provided by ElevenLabs for webhook authentication
- **ELEVENLABS_POST_CALL_PAYLOAD_PATH**: Base directory where webhook payloads will be stored

## API Endpoints

### POST /webhook/post-call

Receive and process ElevenLabs post-call webhooks with HMAC signature validation.

**Three Webhook Types**:

#### 1. post_call_transcription

Receives the transcription of the call as a JSON payload.

**Request Headers**:
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: application/json
```

**Request Body**:
```json
{
  "conversation_id": "conv_abc123",
  "transcript": "Hello, how can I help you today?",
  "status": "completed",
  "duration": 120,
  "timestamp": "2025-11-12T08:00:00Z"
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "message": "Transcription webhook processed and saved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_transcription.json",
    "webhook_type": "transcription"
  }
}
```

#### 2. post_call_audio

Receives the audio recording of the call as multipart form data.

**Request Headers**:
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: multipart/form-data
```

**Form Fields**:
- `conversation_id` (string): Unique conversation identifier
- `audio` (file): MP3 audio file

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Audio webhook processed and saved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_audio.mp3",
    "webhook_type": "audio",
    "file_size": 524288
  }
}
```

#### 3. call_initiation_failure

Receives failure notification when a call fails to initiate.

**Request Headers**:
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: application/json
```

**Request Body**:
```json
{
  "conversation_id": "conv_abc123",
  "error_code": "INIT_FAILED",
  "error_message": "Failed to initialize call",
  "timestamp": "2025-11-12T08:00:00Z"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Failure webhook processed and saved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_failure.json",
    "webhook_type": "failure"
  }
}
```

**HMAC Signature Validation**:

All webhooks require valid HMAC-SHA256 signatures. The service automatically validates:
1. The `elevenlabs-signature` header format
2. The request timestamp (must be within 30 minutes of current time)
3. The HMAC-SHA256 signature using the shared secret

If validation fails, the endpoint returns **401 Unauthorized**.

**Storage Structure**:

Payloads are automatically saved to disk in the following structure:
```
payloads/
├── conversation_id_1/
│   ├── conversation_id_1_transcription.json
│   ├── conversation_id_1_audio.mp3
│   └── conversation_id_1_failure.json
├── conversation_id_2/
│   ├── conversation_id_2_transcription.json
│   └── conversation_id_2_audio.mp3
└── ...
```

### POST /webhook

Receive and process a generic webhook payload.

**Request Body**:
```json
{
  "event_type": "user_signup",
  "data": {
    "email": "user@example.com",
    "name": "John Doe"
  },
  "user_id": "user_123"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Payload of type 'user_signup' processed successfully",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "processed": true,
    "event_type": "user_signup"
  }
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

### POST /echo

Echo the received payload back (useful for testing).

**Request Body**: Same as `/webhook`

**Response**:
```json
{
  "status": "success",
  "message": "Echo received",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "event_type": "user_signup",
    "data": {...},
    "timestamp": "2025-11-12T...",
    "user_id": "user_123"
  }
}
```

### GET /docs

Interactive Swagger UI documentation. Visit `http://localhost:8000/docs` in your browser.

## Testing

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Send a webhook payload
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {"key": "value"},
    "user_id": "user_123"
  }'

# Echo endpoint
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {"key": "value"}
  }'
```

### Using Ngrok URL

Once ngrok is running, use the public URL:

```bash
curl -X POST https://your-ngrok-url.ngrok.io/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {"key": "value"}
  }'
```

## Configuration

Settings are managed through environment variables in the `.env` file:

```
APP_NAME=FastAPI Service
APP_VERSION=0.1.0
DEBUG=True
LOG_LEVEL=INFO
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

### Available Settings

- `APP_NAME`: Application name (default: "FastAPI Service")
- `APP_VERSION`: Application version (default: "0.1.0")
- `DEBUG`: Enable debug mode (default: True)
- `LOG_LEVEL`: Logging level - INFO, DEBUG, WARNING, ERROR (default: "INFO")
- `NGROK_AUTHTOKEN`: Ngrok authentication token (optional)

## Data Models

### PayloadRequest

Input model for webhook endpoints:
- `event_type` (string, required): Type of event
- `data` (object, optional): Event data
- `timestamp` (datetime, optional): Request timestamp (auto-set if not provided)
- `user_id` (string, optional): User identifier

### PayloadResponse

Output model for successful responses:
- `status` (string): "success" or "error"
- `message` (string): Response message
- `request_id` (string): Unique request identifier for tracking
- `data` (object, optional): Response data

### ErrorResponse

Error response model:
- `status` (string): Always "error"
- `message` (string): Error message
- `error_code` (string, optional): Error code for debugging
- `request_id` (string, optional): Request identifier

## Development

### Adding New Endpoints

Edit `app/routes.py` and add new routes to the `router`:

```python
@router.post("/custom-endpoint")
async def custom_handler(payload: PayloadRequest):
    # Your logic here
    return PayloadResponse(
        status="success",
        message="Custom endpoint worked",
        request_id=str(uuid.uuid4()),
        data={}
    )
```

### Custom Payload Models

Add new Pydantic models to `app/models.py` for specialized payloads:

```python
class CustomPayload(BaseModel):
    field1: str
    field2: int
    field3: Optional[str] = None
```

### Logging

Import and use the logger:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Info message")
logger.debug("Debug message")
logger.error("Error message")
```

## Requirements

- Python 3.8+
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pydantic 2.5.0
- Ngrok 6.0.0

See `requirements.txt` for the complete list.

## License

MIT

## Support

For issues or questions, check the logs or modify the code in the `app/` directory.
