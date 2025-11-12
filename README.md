# Eleven Labs Agents Universal Agentic Open Memory System (ELAUAOMS)

A FastAPI service that integrates ElevenLabs conversational AI agents with OpenMemory for persistent, personalized caller experiences. The system stores conversation memories and enables agents to recall past interactions across calls.

## Features

- **ElevenLabs Webhook Integration**:
  - `client-data`: Personalized first message based on caller history
  - `post-call`: Automatic memory extraction and storage
  - `search-memory`: Server tool for agents to search caller history
- **OpenMemory Integration**: Connect to your independent OpenMemory instance for memory storage
- **Intelligent Memory Extraction**: LLM-powered extraction of facts, preferences, and important details
- **Multi-Agent Support**: Share memories across agents or keep them isolated
- **HMAC-SHA256 Authentication**: Secure webhook validation
- **Automatic Payload Storage**: All payloads saved to organized directory structure
- **Background Processing**: Non-blocking memory extraction and storage
- **Health Check**: Simple health check endpoint for monitoring
- **Swagger Documentation**: Auto-generated interactive API docs at `/docs`
- **Environment Configuration**: Manage settings via `.env` file
- **Ngrok Integration**: Built-in tunnel setup for local testing with public URLs

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

1. **Clone the repository**:
   ```bash
   git clone https://github.com/webmasterarbez/elaaoms_claude.git
   cd elaaoms_claude
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```bash
   # ElevenLabs
   ELEVENLABS_API_KEY=sk-elevenlabs-...
   ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret

   # OpenMemory (your independent instance)
   OPENMEMORY_API_URL=https://your-openmemory-instance.com
   OPENMEMORY_API_KEY=your_openmemory_api_key

   # LLM (OpenAI, Anthropic, or Groq)
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-...
   LLM_MODEL=gpt-4-turbo

   # Ngrok (optional, for local testing)
   NGROK_AUTHTOKEN=your_ngrok_token
   ```

5. **Setup OpenMemory independently** (see DEPLOYMENT.md for details)

## Quick Start

### Start the Service

**Terminal 1: Run the FastAPI app**
```bash
python main.py
```

The service will start on `http://localhost:8000`

### Create a Public Tunnel with Ngrok

**Terminal 2: Start ngrok tunnel**
```bash
python scripts/ngrok_config.py
```

This will print a public URL like:
```
Ngrok URL: https://abc-123-def.ngrok.io
```

Use this URL to configure your ElevenLabs webhooks:
- Client-Data: `https://abc-123-def.ngrok.io/webhook/client-data`
- Post-Call: `https://abc-123-def.ngrok.io/webhook/post-call`
- Search-Memory: `https://abc-123-def.ngrok.io/webhook/search-memory`

### Verify It's Running

```bash
curl http://localhost:8000/health
# Or via ngrok:
curl https://abc-123-def.ngrok.io/health
```

## Configuration

All configuration is managed through environment variables in the `.env` file.

### Required Configuration

```env
# ElevenLabs Configuration
ELEVENLABS_API_KEY=sk-elevenlabs-...
ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret_from_elevenlabs
ELEVENLABS_API_URL=https://api.elevenlabs.io/v1

# OpenMemory Configuration (your independent instance)
OPENMEMORY_API_URL=https://your-openmemory-instance.com
OPENMEMORY_API_KEY=your_openmemory_api_key

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic, groq
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo

# Memory Settings
AGENT_PROFILE_TTL_HOURS=24
MEMORY_RELEVANCE_THRESHOLD=0.7
HIGH_IMPORTANCE_THRESHOLD=8

# Payload Storage
ELEVENLABS_POST_CALL_PAYLOAD_PATH=./payloads
```

**Important Notes:**
- **OpenMemory must be setup independently** - this project connects to your existing OpenMemory instance
- **HMAC key** must match the secret configured in your ElevenLabs dashboard
- **LLM Provider** can be `openai`, `anthropic`, or `groq`

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

## Additional Settings

Optional environment variables:

```env
APP_NAME=ELAUAOMS
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

- `APP_NAME`: Application name (default: "ELAUAOMS")
- `APP_VERSION`: Application version (default: "1.0.0")
- `DEBUG`: Enable debug mode (default: True)
- `LOG_LEVEL`: Logging level - INFO, DEBUG, WARNING, ERROR (default: "INFO")
- `NGROK_AUTHTOKEN`: Ngrok authentication token (optional, for local testing)

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
