# 🚀 Deployment Guide

## Quick Start (5 Minutes)

### Option 1: Docker Compose (Recommended)

**Prerequisites:**
- Docker and Docker Compose installed
- API keys ready

**Steps:**

1. **Clone the repository:**
```bash
git clone https://github.com/webmasterarbez/elaaoms_claude.git
cd elaaoms_claude
```

2. **Create .env file:**
```bash
cp .env.example .env
```

3. **Edit .env with your API keys:**
```bash
nano .env  # or vim, code, etc.
```

Required variables:
```bash
ELEVENLABS_API_KEY=sk-elevenlabs-...
ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret
LLM_API_KEY=sk-...  # OpenAI or Anthropic
OPENMEMORY_API_KEY=your_openmemory_key  # Optional
```

4. **Start the entire stack:**
```bash
docker-compose up -d
```

This starts:
- ✅ FastAPI app (port 8000)
- ✅ OpenMemory (port 8080)
- ✅ PostgreSQL database

5. **Verify it's running:**
```bash
curl http://localhost:8000/health
curl http://localhost:8080/health  # OpenMemory
```

**Expected response:**
```json
{"status": "healthy", "message": "Service is running"}
```

6. **View logs:**
```bash
docker-compose logs -f app
```

---

### Option 2: Local Development

**Prerequisites:**
- Python 3.10+
- Docker (for OpenMemory)

**Steps:**

1. **Clone and setup:**
```bash
git clone https://github.com/webmasterarbez/elaaoms_claude.git
cd elaaoms_claude
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create .env file:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Start OpenMemory (separate terminal):**
```bash
docker run -d -p 8080:8080 \
  -e DATABASE_URL=sqlite:///data/openmemory.db \
  caviraoss/openmemory:latest
```

6. **Run the application:**
```bash
python main.py
```

Service available at: `http://localhost:8000`

---

## Production Deployment

### Using ngrok (for testing)

1. **Install ngrok:**
```bash
# Already in scripts/ngrok_config.py
python scripts/ngrok_config.py
```

2. **Get public URL:**
```
Ngrok URL: https://abc123.ngrok.io
```

3. **Use this URL in ElevenLabs webhooks:**
```
Client-Data: https://abc123.ngrok.io/webhook/client-data
Search-Memory: https://abc123.ngrok.io/webhook/search-memory
Post-Call: https://abc123.ngrok.io/webhook/post-call
```

### Using a Cloud Provider

#### Deploy to Render.com (Free Tier Available)

1. **Fork the repository**

2. **Create new Web Service on Render:**
   - Repository: Your forked repo
   - Environment: Docker
   - Add environment variables from `.env`

3. **Deploy!**

Render will automatically:
- Build the Docker image
- Deploy the service
- Provide HTTPS URL

#### Deploy to Railway.app

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login and deploy:**
```bash
railway login
railway init
railway up
```

3. **Add environment variables:**
```bash
railway variables set ELEVENLABS_API_KEY=sk-...
railway variables set LLM_API_KEY=sk-...
# ... add all variables
```

#### Deploy to AWS/GCP/Azure

Use the provided `Dockerfile` and `docker-compose.yml` with:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

---

## Configuration

### ElevenLabs Webhook Setup

Once deployed, configure your ElevenLabs agent with these webhooks:

#### 1. Conversation Initiation Webhook

```
Type: Conversation Initiation
URL: https://your-domain.com/webhook/client-data
HMAC Key: (use the same ELEVENLABS_POST_CALL_HMAC_KEY)
```

#### 2. Post-Call Webhook

```
Type: post_call_transcription
URL: https://your-domain.com/webhook/post-call
HMAC Key: (use ELEVENLABS_POST_CALL_HMAC_KEY)
```

#### 3. Server Tool

Add this tool definition to your agent:

```json
{
  "name": "search_memory",
  "description": "Search the caller's previous conversation history and stored preferences. Use this when you need context about past interactions, previous orders, customer preferences, or any information the caller mentioned before.",
  "url": "https://your-domain.com/webhook/search-memory",
  "method": "POST",
  "parameters": {
    "query": {
      "type": "string",
      "required": true,
      "description": "What to search for in the caller's history (e.g., 'last order number', 'customer preferences', 'previous issues')"
    },
    "search_all_agents": {
      "type": "boolean",
      "required": false,
      "description": "Set to true to search across all agents, false to search only this agent's memories (default: false)"
    }
  }
}
```

**Agent System Prompt Addition:**

Add this to your agent's system prompt:

```
You have access to a search_memory tool that can retrieve information from previous conversations with this caller. Use it when:
- The caller asks about previous interactions
- You need context about their history
- They reference past orders, issues, or preferences
- You want to personalize the conversation

Always use search_memory before saying "I don't have that information" about the caller's history.
```

---

## Testing

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Test client-data (will return default message - no memories yet)
curl -X POST http://localhost:8000/webhook/client-data \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test_agent",
    "conversation_id": "test_conv",
    "dynamic_variables": {
      "system__caller_id": "+15551234567"
    }
  }'

# Test search-memory (will return empty - no memories yet)
curl -X POST http://localhost:8000/webhook/search-memory \
  -H "Content-Type: application/json" \
  -d '{
    "query": "order number",
    "caller_id": "+15551234567",
    "agent_id": "test_agent"
  }'
```

### Create Test Data

```bash
# Send a test post-call webhook to create some memories
curl -X POST http://localhost:8000/webhook/post-call \
  -H "Content-Type: application/json" \
  -d '{
    "type": "post_call_transcription",
    "data": {
      "conversation_id": "test_conv_1",
      "agent_id": "test_agent",
      "transcript": [
        {"role": "agent", "message": "Hello, how can I help?"},
        {"role": "user", "message": "I want to order product XYZ-789"},
        {"role": "agent", "message": "Great! Let me help you with that."},
        {"role": "user", "message": "I prefer express shipping"}
      ],
      "status": "completed",
      "duration": 120,
      "dynamic_variables": {
        "system__caller_id": "+15551234567"
      }
    }
  }'
```

Wait 10-20 seconds for background processing, then test search again:

```bash
curl -X POST http://localhost:8000/webhook/search-memory \
  -H "Content-Type: application/json" \
  -d '{
    "query": "order",
    "caller_id": "+15551234567",
    "agent_id": "test_agent"
  }'
```

---

## Monitoring

### View Logs

**Docker Compose:**
```bash
docker-compose logs -f app
docker-compose logs -f openmemory
```

**Local:**
```bash
tail -f logs/app.log  # if configured
```

### Check Background Jobs

Look for these log entries:
```
[job_abc123] Processing job for conversation conv_xyz789
[job_abc123] Extracted 8 memories from conversation
[job_abc123] Stored 6 new memories, reinforced 2 existing
```

### Monitor OpenMemory

```bash
# Check OpenMemory health
curl http://localhost:8080/health

# View stored memories (if API supports it)
curl http://localhost:8080/memories
```

---

## Troubleshooting

### Issue: Webhook returns 401 Unauthorized

**Cause:** HMAC signature validation failing

**Solution:**
1. Verify `ELEVENLABS_POST_CALL_HMAC_KEY` matches ElevenLabs dashboard
2. Check webhook is sending `elevenlabs-signature` header
3. For testing, temporarily disable HMAC (not recommended for production)

### Issue: No memories being extracted

**Cause:** Background job not running or LLM API key invalid

**Solution:**
1. Check logs: `docker-compose logs -f app`
2. Verify `LLM_API_KEY` is correct
3. Check OpenMemory is running: `curl http://localhost:8080/health`
4. Look for error messages in background worker logs

### Issue: First message not personalized

**Cause:** No previous memories exist or LLM generation failed

**Solution:**
1. Check if caller has previous conversations
2. Verify memories were stored from post-call webhook
3. Check LLM API quota/credits
4. System falls back to default message gracefully

### Issue: OpenMemory connection refused

**Cause:** OpenMemory not running or wrong URL

**Solution:**
1. Check OpenMemory: `docker ps | grep openmemory`
2. Verify `OPENMEMORY_API_URL` in .env
3. Restart: `docker-compose restart openmemory`

---

## Scaling

### For 1,000+ calls/day:

1. **Use managed PostgreSQL:**
   - AWS RDS, GCP Cloud SQL, or Azure Database
   - Update `DATABASE_URL` in OpenMemory config

2. **Add Redis for job queue:**
   - Replace simple threading with RQ or Celery
   - See commented code in `app/background_jobs.py`

3. **Scale app horizontally:**
   - Deploy multiple app instances behind load balancer
   - Share Redis/PostgreSQL across instances

4. **Use CDN/Proxy:**
   - Cloudflare, AWS CloudFront for webhook endpoints
   - Reduces latency, improves reliability

---

## Backup & Recovery

### Backup OpenMemory Data

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U openmemory openmemory > backup.sql

# Restore
docker-compose exec -T postgres psql -U openmemory openmemory < backup.sql
```

### Backup Conversation Payloads

```bash
# Payloads are stored in ./payloads directory
tar -czf payloads-backup.tar.gz payloads/
```

---

## Security Checklist

- ✅ HMAC signature validation enabled (ELEVENLABS_POST_CALL_HMAC_KEY set)
- ✅ API keys stored in .env (not committed to git)
- ✅ HTTPS enabled (use ngrok or reverse proxy)
- ✅ OpenMemory API key configured (OPENMEMORY_API_KEY)
- ✅ Database password changed from default (in docker-compose.yml)
- ✅ Rate limiting configured (optional, for production)

---

## Cost Optimization

### Reduce LLM Costs:

1. **Use cheaper models:**
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo  # Instead of gpt-4-turbo
   ```

2. **Use Anthropic Claude (alternative):**
   ```bash
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-sonnet-20240229  # or claude-3-opus-20240229
   ```

3. **Adjust memory extraction:**
   - Reduce `importance` threshold to store fewer memories
   - Increase deduplication threshold to reinforce more, store less

---

## Next Steps

1. ✅ Deploy using Docker Compose or cloud provider
2. ✅ Configure ElevenLabs webhooks
3. ✅ Test with a sample call
4. ✅ Monitor logs for 24 hours
5. ✅ Adjust thresholds based on results
6. ✅ Scale as needed

**Your universal agent memory system is ready!** 🚀
