# Quick Start Guide: ELAAOMS Memory Management Platform

**Feature**: [1-elaaoms-memory-system](../features/1-elaaoms-memory-system.md)  
**Created**: 2024-12-19

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- ElevenLabs account with API access
- OpenAI or Anthropic API key

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd elaaoms_claude
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in required values:

```env
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret_key

# OpenMemory Configuration
OPENMEMORY_API_URL=http://localhost:8001
OPENMEMORY_API_KEY=your_openmemory_api_key

# LLM Provider Configuration
LLM_PROVIDER=openai  # or "anthropic"
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Agent Profile Caching
AGENT_PROFILE_TTL_HOURS=24

# Memory Search Configuration
MEMORY_RELEVANCE_THRESHOLD=0.7

# Data Storage
ELEVENLABS_POST_CALL_PAYLOAD_PATH=./data/payloads
```

### 5. Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- OpenMemory (port 8001)
- Backend API (port 8000)

### 6. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

### 7. Set Up Ngrok for Webhook Testing

```bash
pip install pyngrok
python scripts/ngrok_config.py
```

This will:
- Start ngrok tunnel
- Display public URL (e.g., `https://abc123.ngrok.io`)
- Configure webhook URLs automatically

### 8. Configure ElevenLabs Agent

1. Log in to ElevenLabs dashboard
2. Select your agent
3. Configure webhooks:
   - **Client Data Webhook**: `https://your-ngrok-url.ngrok.io/webhook/client-data`
   - **Server Tools** → **Memory Search**: `https://your-ngrok-url.ngrok.io/webhook/search-memory`
   - **Post-Call Webhook**: `https://your-ngrok-url.ngrok.io/webhook/post-call`
4. Set HMAC secret to match `ELEVENLABS_POST_CALL_HMAC_KEY` in `.env`
5. Configure dynamic variable: `system__caller_id` for caller identification

## Testing the System

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "System operational",
  "dependencies": {
    "openmemory": "available",
    "postgres": "available"
  }
}
```

### 2. Test Pre-Call Webhook

```bash
curl -X POST http://localhost:8000/webhook/client-data \
  -H "Content-Type: application/json" \
  -H "elevenlabs-signature: t=1234567890,v0=signature" \
  -d '{
    "agent_id": "test_agent",
    "conversation_id": "test_conv_123",
    "dynamic_variables": {
      "system__caller_id": "+15551234567"
    }
  }'
```

### 3. Test Memory Search Webhook

```bash
curl -X POST http://localhost:8000/webhook/search-memory \
  -H "Content-Type: application/json" \
  -H "elevenlabs-signature: t=1234567890,v0=signature" \
  -d '{
    "query": "What was my last order?",
    "caller_id": "+15551234567",
    "agent_id": "test_agent",
    "conversation_id": "test_conv_123"
  }'
```

### 4. Test Post-Call Webhook

```bash
curl -X POST http://localhost:8000/webhook/post-call \
  -H "Content-Type: application/json" \
  -H "elevenlabs-signature: t=1234567890,v0=signature" \
  -d '{
    "type": "post_call_transcription",
    "conversation_id": "test_conv_123",
    "agent_id": "test_agent",
    "caller_id": "+15551234567",
    "transcript": {
      "text": "Customer called about delayed package XYZ-789..."
    }
  }'
```

## Development Workflow

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests
pytest
```

### Code Organization

```
backend/
├── app/
│   ├── routes.py          # API endpoint definitions
│   ├── models.py           # Pydantic request/response models
│   ├── auth.py             # HMAC signature verification
│   ├── storage.py          # File system operations
│   ├── background_jobs.py  # Async memory extraction
│   ├── llm_service.py      # LLM provider abstraction
│   ├── openmemory_client.py # OpenMemory API client
│   └── elevenlabs_client.py # ElevenLabs API client
├── config/
│   └── settings.py        # Environment configuration
└── main.py                 # Application entry point
```

### Hot Reload

The server runs with `--reload` flag, so code changes automatically restart the server.

### Viewing Logs

```bash
# Application logs
tail -f data/logs/app.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f openmemory
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## Common Issues

### Issue: HMAC Signature Validation Fails

**Solution**: Ensure `ELEVENLABS_POST_CALL_HMAC_KEY` in `.env` matches the secret configured in ElevenLabs dashboard.

### Issue: OpenMemory Connection Failed

**Solution**: 
1. Check Docker containers are running: `docker-compose ps`
2. Verify OpenMemory is accessible: `curl http://localhost:8001/health`
3. Check `OPENMEMORY_API_URL` in `.env`

### Issue: LLM API Errors

**Solution**:
1. Verify API keys are set correctly in `.env`
2. Check API rate limits and quotas
3. Review logs for specific error messages

### Issue: Ngrok Tunnel Not Working

**Solution**:
1. Ensure ngrok is authenticated: `ngrok config add-authtoken <token>`
2. Check firewall/network settings
3. Verify ngrok process is running: `ps aux | grep ngrok`

## Next Steps

1. **Read the Specification**: Review [feature specification](../features/1-elaaoms-memory-system.md)
2. **Review Architecture**: See [implementation plan](./plan.md)
3. **Understand Data Model**: Check [data model documentation](./data-model.md)
4. **API Reference**: See [OpenAPI specification](./contracts/openapi.yaml)

## Production Deployment

For production deployment instructions, see:
- [Deployment Guide](../../../docs/DEPLOYMENT.md)
- [Memory System Guide](../../../docs/MEMORY_SYSTEM_GUIDE.md)

## Getting Help

- Check logs in `data/logs/app.log`
- Review API documentation at `/docs`
- Check Docker container status: `docker-compose ps`
- Verify environment variables: `cat .env`

## Development Tips

1. **Use Request IDs**: All requests generate UUIDs for tracing
2. **Check Health Endpoint**: `/health` shows system status
3. **Monitor Performance**: Response times logged with request IDs
4. **Test Webhooks**: Use ngrok for local ElevenLabs integration
5. **Debug Memory Extraction**: Check `data/payloads/` for saved transcripts

