# ElevenLabs Agents Universal Agentic Open Memory System (ELAAOMS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](Dockerfile)

A universal memory system for ElevenLabs AI agents that automatically extracts, stores, and retrieves conversation memories across all your agents. Provides personalized greetings for returning callers and real-time memory search during calls.

## 🎯 Quick Links

- 📖 [Complete Memory System Guide](docs/MEMORY_SYSTEM_GUIDE.md) - Full implementation details
- 🚀 [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- 🛠️ [Utility Scripts](utility/README.md) - Helper tools and scripts
- 📝 [API Documentation](#api-endpoints) - Endpoint reference
- 🔍 [Code-Documentation Alignment](docs/CODE_DOCUMENTATION_ALIGNMENT.md) - Technical deep-dive

## ✨ Key Features

### Memory System (Primary Features)
- **Automatic Memory Extraction**: LLM extracts memories from every conversation automatically
- **Personalized Greetings**: Returning callers get customized first messages based on history
- **Real-Time Memory Search**: Agents can search caller history during active calls
- **Multi-Agent Support**: Share high-importance memories across different agents
- **Zero Database Setup**: Everything stored in OpenMemory (PostgreSQL-backed)

### Webhook Processing
- **ElevenLabs Post-Call Webhooks**: Receive and process three webhook types:
  - `post_call_transcription`: Transcription JSON payloads with memory extraction
  - `post_call_audio`: Audio files as base64-encoded data
  - `call_initiation_failure`: Call failure notifications
- **HMAC-SHA256 Authentication**: All webhooks validated using ElevenLabs HMAC signatures
- **Automatic Payload Storage**: Payloads saved to disk in organized directory structure
- **Background Job Processing**: Memory extraction runs asynchronously

### Technical Features
- **Health Check**: Simple health check endpoint for monitoring
- **Swagger Documentation**: Auto-generated interactive API docs at `/docs`
- **CORS Enabled**: Accept requests from any origin
- **Request Tracking**: Every request gets a unique UUID for tracing
- **Structured Logging**: Comprehensive logging for debugging
- **Environment Configuration**: Manage settings via `.env` file
- **Ngrok Integration**: Built-in tunnel setup for testing with public URLs

## 📁 Project Structure

```
.
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py          # FastAPI app initialization
│   │   ├── auth.py              # HMAC signature verification
│   │   ├── models.py            # Pydantic request/response models
│   │   ├── routes.py            # API endpoint definitions
│   │   ├── storage.py           # File storage handlers
│   │   ├── background_jobs.py   # Memory extraction job processor
│   │   ├── llm_service.py       # LLM integration (OpenAI/Anthropic)
│   │   ├── openmemory_client.py # OpenMemory API client
│   │   └── elevenlabs_client.py # ElevenLabs API client
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Environment settings
│   ├── main.py                  # Application entry point
│   └── requirements.txt         # Python dependencies
├── frontend/                    # Frontend applications
│   ├── react-portfolio/        # React-based portfolio site
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   └── landing-page/           # Static HTML landing page
│       ├── css/
│       ├── js/
│       └── index.html
├── docs/                       # All project documentation
│   ├── MEMORY_SYSTEM_GUIDE.md  # Memory system implementation
│   ├── DEPLOYMENT.md           # Deployment instructions
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── SECURITY.md             # Security documentation
│   ├── MARKETING_STRATEGY.md   # Marketing documentation
│   └── [other docs...]
├── docker/                     # Docker configuration
│   └── Dockerfile             # Backend container definition
├── scripts/                    # Utility scripts
│   ├── ngrok_config.py        # Ngrok tunnel configuration
│   └── services.sh            # Service management script
├── utility/                    # Helper utilities
│   ├── get_conversation.py    # Fetch conversations from ElevenLabs
│   └── generate_hmac.py       # HMAC signature generation
├── tests/                      # Test files
│   └── test_webhook.py
├── data/                       # Runtime data (gitignored)
│   ├── payloads/              # Webhook payloads
│   └── logs/                  # Application logs
├── docker-compose.yml         # Backend service orchestration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- OpenMemory instance (must be configured and running independently)
- Docker (optional, only for backend containerization - not required for local development)

### Steps

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
   cd backend
   pip install -r requirements.txt
   ```

4. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

5. **Configure your `.env` file**:
   ```env
   # ElevenLabs Configuration
   ELEVENLABS_API_KEY=sk-elevenlabs-your-key-here
   ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret_from_elevenlabs
   ELEVENLABS_POST_CALL_PAYLOAD_PATH=./payloads

   # OpenMemory Configuration
   # Note: OpenMemory must be configured and running independently
   OPENMEMORY_API_URL=http://localhost:8080
   OPENMEMORY_API_KEY=your_openmemory_key

   # LLM Configuration (choose one)
   LLM_PROVIDER=openai  # or anthropic
   LLM_API_KEY=sk-your-openai-key-here
   LLM_MODEL=gpt-4-turbo
   ```

## 🚀 Quick Start

### Option 1: Local Development (Recommended)

1. **Install dependencies** (if not already done):
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Ensure OpenMemory is running** (must be configured independently):
   - Verify your OpenMemory instance is accessible at the URL specified in your `.env` file
   - Test connection: `curl http://your-openmemory-url:8080/health`

3. **Start the FastAPI service**:
   ```bash
   cd backend
   python main.py
   ```

   The service will start on `http://localhost:8000`

4. **Optional: Create a public tunnel** (for testing with ElevenLabs):
   ```bash
   python scripts/ngrok_config.py
   ```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Option 2: Docker Compose (Optional)

**Note:** Docker Compose only runs the backend service. OpenMemory must be configured and running independently.

Start the FastAPI backend service:

```bash
docker-compose up -d
```

This starts:
- FastAPI app on port 8000

**Important:** Ensure your `.env` file has the correct `OPENMEMORY_API_URL` pointing to your OpenMemory instance (which must be running separately).

## 🔧 Configuration

### Environment Variables

All configuration is managed through environment variables in `.env`:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key | - |
| `ELEVENLABS_POST_CALL_HMAC_KEY` | Yes | Webhook HMAC secret | - |
| `ELEVENLABS_API_URL` | No | ElevenLabs API base URL | `https://api.elevenlabs.io/v1` |
| `OPENMEMORY_API_URL` | Yes | OpenMemory API URL (must point to external instance) | `http://localhost:8080` |
| `OPENMEMORY_API_KEY` | No | OpenMemory API key (if auth enabled) | - |
| `LLM_PROVIDER` | Yes | LLM provider (`openai` or `anthropic`) | `openai` |
| `LLM_API_KEY` | Yes | OpenAI or Anthropic API key | - |
| `LLM_MODEL` | No | Model name | `gpt-4-turbo` |
| `AGENT_PROFILE_TTL_HOURS` | No | Agent profile cache duration | `24` |
| `MEMORY_RELEVANCE_THRESHOLD` | No | Min relevance score for search | `0.7` |
| `HIGH_IMPORTANCE_THRESHOLD` | No | Min importance for cross-agent memories | `8` |

See `.env.example` for a complete list with descriptions.

## 📡 API Endpoints

### Memory System Endpoints (Primary)

#### POST /webhook/client-data
**Purpose:** Provide personalized first message when a call starts

**Called By:** ElevenLabs at conversation initiation

**Request:**
```json
{
  "agent_id": "agent_abc123",
  "conversation_id": "conv_xyz789",
  "dynamic_variables": {
    "system__caller_id": "+15551234567"
  }
}
```

**Response:**
```json
{
  "first_message": "Hi again! I hope your order XYZ-789 arrived safely. How can I help you today?"
}
```

**Performance:** < 2 seconds

---

#### POST /webhook/search-memory
**Purpose:** Search caller's memory during active conversation

**Called By:** ElevenLabs agent during call (Server Tool)

**Request:**
```json
{
  "query": "What was my last order number?",
  "caller_id": "+15551234567",
  "agent_id": "agent_abc123",
  "conversation_id": "conv_current123",
  "search_all_agents": false
}
```

**Response:**
```json
{
  "results": [
    {
      "memory": "Customer ordered product XYZ-789 on March 15th",
      "relevance": 0.92,
      "timestamp": "2025-11-10T14:30:00Z",
      "conversation_id": "conv_prev456",
      "agent_id": "agent_abc123"
    }
  ],
  "summary": "Most recent order: XYZ-789 on March 15th",
  "searched_agents": "agent_abc123"
}
```

**Performance:** < 3 seconds

---

#### POST /webhook/post-call
**Purpose:** Extract and store memories after call ends

**Called By:** ElevenLabs after call completion

Receive and process ElevenLabs post-call webhooks with HMAC signature validation.

**Three Webhook Types:**

##### 1. post_call_transcription

Receives the transcription of the call as a JSON payload.

**Request Headers:**
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: application/json
```

**Request Body:**
```json
{
  "type": "post_call_transcription",
  "data": {
    "conversation_id": "conv_abc123",
    "transcript": [
      {
        "role": "agent",
        "message": "Hello, how can I help you today?",
        "agent_id": "agent_abc123"
      },
      {
        "role": "user",
        "message": "I need help with my order XYZ-789"
      }
    ],
    "status": "completed",
    "duration": 120,
    "agent_id": "agent_abc123",
    "dynamic_variables": {
      "system__caller_id": "+15551234567"
    }
  }
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Transcription webhook processed, memory extraction started",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_transcription.json",
    "webhook_type": "post_call_transcription",
    "conversation_id": "conv_abc123",
    "transcript_items": 2,
    "memory_extraction_queued": true
  }
}
```

**Background Processing:**
1. Fetch/update agent profile from ElevenLabs API (24h cache)
2. Extract memories using LLM (factual, preference, issue, emotional, relational)
3. Deduplicate against existing memories
4. Store new memories or reinforce existing ones in OpenMemory

**Performance:** < 1 second response, 10-20 seconds background processing

---

##### 2. post_call_audio

Receives the audio recording of the call as JSON with base64-encoded audio data.

**Request Headers:**
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: application/json
```

**Request Body:**
```json
{
  "type": "post_call_audio",
  "data": {
    "conversation_id": "conv_abc123",
    "full_audio": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA..."
  }
}
```

**Note:** `full_audio` contains the MP3 audio file encoded as a base64 string.

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Audio webhook processed and saved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_audio.mp3",
    "webhook_type": "post_call_audio",
    "conversation_id": "conv_abc123",
    "audio_size": 524288,
    "base64_size": 699052
  }
}
```

---

##### 3. call_initiation_failure

Receives failure notification when a call fails to initiate.

**Request Headers:**
```
elevenlabs-signature: t=1234567890,v0=abcd1234...
content-type: application/json
```

**Request Body:**
```json
{
  "type": "call_initiation_failure",
  "data": {
    "agent_id": "agent_abc123",
    "conversation_id": "conv_abc123",
    "failure_reason": "Connection timeout",
    "metadata": {
      "type": "sip",
      "body": {"sip_status_code": 408}
    }
  }
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Failure webhook processed and saved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "file_path": "./payloads/conv_abc123/conv_abc123_failure.json",
    "webhook_type": "call_initiation_failure",
    "conversation_id": "conv_abc123",
    "failure_reason": "Connection timeout",
    "agent_id": "agent_abc123"
  }
}
```

---

### HMAC Signature Validation

All webhooks require valid HMAC-SHA256 signatures. The service automatically validates:
1. The `elevenlabs-signature` header format (`t=timestamp,v0=hash`)
2. The request timestamp (must be within 30 minutes of current time)
3. The HMAC-SHA256 signature using the shared secret

**If validation fails, the endpoint returns 401 Unauthorized.**

**Error Response (401):**
```json
{
  "detail": "Invalid webhook signature"
}
```

**Other Error Responses:**

**400 Bad Request** (invalid payload):
```json
{
  "detail": "Invalid transcription webhook: missing required field 'conversation_id'"
}
```

**500 Internal Server Error** (server issue):
```json
{
  "detail": "Internal server error"
}
```

---

### Storage Structure

Payloads are automatically saved to disk in the `data/` directory:

```
data/
├── payloads/
│   ├── conversation_id_1/
│   │   ├── conversation_id_1_transcription.json
│   │   ├── conversation_id_1_audio.mp3
│   │   └── conversation_id_1_failure.json
│   ├── conversation_id_2/
│   │   ├── conversation_id_2_transcription.json
│   │   └── conversation_id_2_audio.mp3
│   └── ...
└── logs/
    └── app.log
```

---

### Utility Endpoints

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

#### POST /echo

Echo endpoint for testing - returns the payload back.

**Request Body:**
```json
{
  "event_type": "test_event",
  "data": {"key": "value"},
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Echo received",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "event_type": "test_event",
    "data": {"key": "value"},
    "timestamp": "2025-11-12T...",
    "user_id": "user_123"
  }
}
```

#### GET /docs

Interactive Swagger UI documentation. Visit `http://localhost:8000/docs` in your browser.

## 🧪 Testing

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Echo endpoint
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {"key": "value"}
  }'
```

### Testing with ElevenLabs Webhooks

**Important:** For testing with ElevenLabs webhooks, you need valid HMAC signatures. See the [HMAC Testing Guide](utility/README.md#security) for details on generating valid signatures.

For development testing, you can use the `utility/get_conversation.py` script which automatically generates valid HMAC signatures:

```bash
# Process a conversation from ElevenLabs
python utility/get_conversation.py conv_abc123xyz
```

### Using Ngrok URL

Once ngrok is running, use the public URL:

```bash
python scripts/ngrok_config.py

# Use the provided URL in your tests
curl -X POST https://your-ngrok-url.ngrok.io/health
```

## 🏗️ Architecture

The system consists of three main webhook flows:

1. **Pre-Call (Client-Data):** ElevenLabs calls `/webhook/client-data` → Retrieves memories → Generates personalized greeting
2. **During Call (Search-Memory):** Agent uses Server Tool → Calls `/webhook/search-memory` → Returns relevant memories
3. **Post-Call (Memory Extraction):** ElevenLabs calls `/webhook/post-call` → Saves payload → Background job extracts & stores memories

For detailed architecture diagrams and data flows, see [MEMORY_SYSTEM_GUIDE.md](MEMORY_SYSTEM_GUIDE.md).

## 📚 Data Models

### PayloadRequest
Input model for generic webhook endpoints:
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

For complete data model documentation, see the [Swagger docs](http://localhost:8000/docs) or [models.py](backend/app/models.py).

## 🛠️ Development

### Adding New Endpoints

Edit `backend/app/routes.py` and add new routes to the `router`:

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

Add new Pydantic models to `backend/app/models.py` for specialized payloads:

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

## 📋 Requirements

- **Python:** 3.10 or higher
- **FastAPI:** 0.104.1
- **Uvicorn:** 0.24.0
- **Pydantic:** 2.5.0
- **pydantic-settings:** 2.1.0
- **python-dotenv:** 1.0.0
- **pyngrok:** 7.4.1
- **requests:** 2.31.0
- **httpx:** 0.25.2 (async HTTP client)
- **openai:** 1.6.1 (OpenAI Python SDK)
- **anthropic:** 0.25.1 (Anthropic Python SDK)

See `backend/requirements.txt` for the complete list with exact versions.

## 🚨 Troubleshooting

### HMAC Validation Errors (401 Unauthorized)

**Cause:** Invalid or missing HMAC signature

**Solutions:**
1. Verify `ELEVENLABS_POST_CALL_HMAC_KEY` matches your ElevenLabs dashboard
2. Ensure `elevenlabs-signature` header is present
3. Check that timestamp is current (within 30 minutes)
4. Use `utility/get_conversation.py` which generates valid signatures

### Memory Not Being Stored

**Cause:** Missing `caller_id` or `agent_id` in webhook data

**Solutions:**
1. Ensure ElevenLabs agent is configured with `dynamic_variables`
2. Check logs for "No caller_id found" warnings
3. Verify OpenMemory is accessible: `curl http://your-openmemory-url:8080/health`
4. Check LLM API key is valid and has credits

### OpenMemory Connection Errors

**Cause:** OpenMemory service not accessible or misconfigured

**Solutions:**
1. Verify OpenMemory is running independently: `curl http://your-openmemory-url:8080/health`
2. Check that `OPENMEMORY_API_URL` in `.env` matches your OpenMemory instance URL
3. Ensure OpenMemory instance is accessible from your backend (network/firewall settings)
4. Verify `OPENMEMORY_API_KEY` is correct if authentication is enabled

### OpenAI API Errors

**Cause:** Invalid API key or deprecated SDK usage

**Solutions:**
1. Verify `LLM_API_KEY` is correct
2. Ensure you have API credits available
3. Check that you're using OpenAI SDK 1.x (already updated in this version)

For more troubleshooting, see [DEPLOYMENT.md](docs/DEPLOYMENT.md#troubleshooting).

## 📖 Additional Documentation

- **[MEMORY_SYSTEM_GUIDE.md](docs/MEMORY_SYSTEM_GUIDE.md)** - Complete memory system implementation guide with architecture, configuration, and examples
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide with Docker, cloud providers, monitoring, and scaling
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Guidelines for contributing to the project
- **[SECURITY.md](docs/SECURITY.md)** - Security policies and best practices
- **[utility/README.md](utility/README.md)** - Documentation for utility scripts and tools
- **[CODE_DOCUMENTATION_ALIGNMENT.md](docs/CODE_DOCUMENTATION_ALIGNMENT.md)** - Technical analysis of code-documentation alignment

## 📄 License

MIT

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on contributing to this project.

## 💬 Support

For issues, questions, or feature requests:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `tail -f data/logs/app.log` or `docker-compose logs -f backend` (if using Docker)
3. Consult the documentation guides linked above
4. Open an issue on GitHub

## 🎯 Next Steps

1. ✅ Complete installation and configuration
2. ✅ Configure ElevenLabs webhooks (see [MEMORY_SYSTEM_GUIDE.md](docs/MEMORY_SYSTEM_GUIDE.md#elevenlabs-setup))
3. ✅ Test with a sample call
4. ✅ Monitor logs and adjust settings
5. ✅ Deploy to production (see [DEPLOYMENT.md](docs/DEPLOYMENT.md))

**Your universal agent memory system is ready!** 🚀

---

For detailed memory system implementation, webhook configuration, and production deployment, see the complete guides:
- 📖 [Memory System Guide](docs/MEMORY_SYSTEM_GUIDE.md)
- 🚀 [Deployment Guide](docs/DEPLOYMENT.md)
- 🎨 [React Portfolio](frontend/react-portfolio/README.md)
- 🌐 [Landing Page](frontend/landing-page/README.md)
