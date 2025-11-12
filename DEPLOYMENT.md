# 🚀 Deployment Guide

## Prerequisites

- Python 3.10+
- OpenMemory instance (setup separately)
- API keys: ElevenLabs, OpenAI/Anthropic/Groq
- Ngrok account (free tier works)

---

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/webmasterarbez/elaaoms_claude.git
cd elaaoms_claude
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=sk-elevenlabs-...
ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_secret
ELEVENLABS_API_URL=https://api.elevenlabs.io/v1

# OpenMemory Configuration (your independent instance)
OPENMEMORY_API_URL=https://your-openmemory-instance.com
OPENMEMORY_API_KEY=your_openmemory_api_key

# LLM Configuration
LLM_PROVIDER=openai  # or anthropic, groq
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo  # or claude-3-opus-20240229, mixtral-8x7b-32768

# Memory Settings
AGENT_PROFILE_TTL_HOURS=24
MEMORY_RELEVANCE_THRESHOLD=0.7
HIGH_IMPORTANCE_THRESHOLD=8

# Payload Storage
ELEVENLABS_POST_CALL_PAYLOAD_PATH=./payloads

# Ngrok Configuration (optional, for local testing)
NGROK_AUTHTOKEN=your_ngrok_token
```

### 5. Setup OpenMemory Independently

**You need to setup your own OpenMemory instance separately.** Options include:

1. **Self-hosted OpenMemory:**
   - Deploy OpenMemory to your own server
   - Configure with PostgreSQL or your preferred database
   - Get the API URL and key

2. **OpenMemory Cloud:**
   - Sign up for OpenMemory service
   - Get your API URL and key

3. **Local OpenMemory (Development Only):**
   ```bash
   # In a separate terminal/server
   # Follow OpenMemory's installation instructions
   ```

Once setup, update your `.env` with:
```bash
OPENMEMORY_API_URL=https://your-openmemory-url
OPENMEMORY_API_KEY=your-api-key
```

### 6. Start the Application

**Terminal 1: Run the FastAPI app**
```bash
python main.py
```

Service will start on `http://localhost:8000`

**Terminal 2: Create public tunnel with ngrok**
```bash
python scripts/ngrok_config.py
```

You'll get a public URL like:
```
Ngrok URL: https://abc-123-def.ngrok.io
```

### 7. Verify It's Running

```bash
# Health check
curl http://localhost:8000/health

# Or via ngrok
curl https://abc-123-def.ngrok.io/health
```

**Expected response:**
```json
{"status": "healthy", "message": "Service is running"}
```

---

## ElevenLabs Webhook Configuration

Use your ngrok URL (or production domain) to configure ElevenLabs webhooks:

### 1. Conversation Initiation Webhook

```
Type: Conversation Initiation
URL: https://your-ngrok-url.ngrok.io/webhook/client-data
HMAC Key: (use ELEVENLABS_POST_CALL_HMAC_KEY from .env)
```

### 2. Post-Call Webhook

```
Type: post_call_transcription
URL: https://your-ngrok-url.ngrok.io/webhook/post-call
HMAC Key: (use ELEVENLABS_POST_CALL_HMAC_KEY from .env)
```

### 3. Server Tool (Search Memory)

Add this tool definition to your ElevenLabs agent:

```json
{
  "name": "search_memory",
  "description": "Search the caller's previous conversation history and stored preferences. Use this when you need context about past interactions, previous orders, customer preferences, or any information the caller mentioned before.",
  "url": "https://your-ngrok-url.ngrok.io/webhook/search-memory",
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

Wait 10-20 seconds for background processing, then test search again.

---

## Production Deployment

### Option 1: Cloud Platform (Recommended)

Deploy to a cloud platform with Python support:

#### Deploy to Render.com

1. **Fork the repository**
2. **Create new Web Service:**
   - Repository: Your forked repo
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
3. **Add environment variables** from your `.env`
4. **Deploy**

Render provides HTTPS URL automatically.

#### Deploy to Railway.app

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Add environment variables:
```bash
railway variables set ELEVENLABS_API_KEY=sk-...
railway variables set OPENMEMORY_API_URL=https://...
railway variables set LLM_API_KEY=sk-...
# ... add all variables from .env
```

#### Deploy to Heroku

```bash
heroku create your-app-name
heroku config:set ELEVENLABS_API_KEY=sk-...
heroku config:set OPENMEMORY_API_URL=https://...
# ... add all variables
git push heroku main
```

### Option 2: VPS (DigitalOcean, AWS EC2, Linode)

1. **SSH into your server:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/webmasterarbez/elaaoms_claude.git
   cd elaaoms_claude
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure .env** with your credentials

4. **Run with process manager (PM2, systemd, supervisor):**

   **Using systemd:**
   ```bash
   sudo nano /etc/systemd/system/elaaoms.service
   ```

   ```ini
   [Unit]
   Description=ELAAOMS FastAPI Service
   After=network.target

   [Service]
   User=your-user
   WorkingDirectory=/path/to/elaaoms_claude
   Environment="PATH=/path/to/elaaoms_claude/venv/bin"
   ExecStart=/path/to/elaaoms_claude/venv/bin/python main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable elaaoms
   sudo systemctl start elaaoms
   ```

5. **Setup reverse proxy (nginx/caddy) for HTTPS**

---

## Monitoring

### View Logs

```bash
# If running directly
tail -f logs/app.log  # if configured

# If using systemd
sudo journalctl -u elaaoms -f

# If using PM2
pm2 logs elaaoms
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
# Check your OpenMemory instance health
curl https://your-openmemory-url/health
```

---

## Troubleshooting

### Issue: Webhook returns 401 Unauthorized

**Cause:** HMAC signature validation failing

**Solution:**
1. Verify `ELEVENLABS_POST_CALL_HMAC_KEY` matches ElevenLabs dashboard
2. Check webhook sends `elevenlabs-signature` header
3. For testing, temporarily disable HMAC (not recommended for production)

### Issue: No memories being extracted

**Cause:** Background job not running or LLM API key invalid

**Solution:**
1. Check application logs
2. Verify `LLM_API_KEY` is correct
3. Check OpenMemory is accessible: `curl $OPENMEMORY_API_URL/health`
4. Look for error messages in background worker logs

### Issue: First message not personalized

**Cause:** No previous memories exist or LLM generation failed

**Solution:**
1. Check if caller has previous conversations
2. Verify memories were stored from post-call webhook
3. Check LLM API quota/credits
4. System falls back to default message gracefully

### Issue: Cannot connect to OpenMemory

**Cause:** OpenMemory not running or wrong URL

**Solution:**
1. Verify `OPENMEMORY_API_URL` in .env is correct
2. Check OpenMemory instance is running
3. Test connection: `curl $OPENMEMORY_API_URL/health`
4. Check API key is valid: `OPENMEMORY_API_KEY`

### Issue: Ngrok tunnel disconnects

**Cause:** Free ngrok tunnels expire after 2 hours

**Solution:**
1. Restart ngrok: `python scripts/ngrok_config.py`
2. Update webhook URLs in ElevenLabs dashboard
3. For production, deploy to cloud platform with permanent URL
4. Consider ngrok paid plan for persistent URLs

---

## Scaling for Production

### For 1,000+ calls/day:

1. **Deploy to multiple regions:**
   - Use load balancer (AWS ALB, Cloudflare Load Balancing)
   - Deploy app instances in different regions
   - All instances connect to same OpenMemory

2. **Use managed OpenMemory:**
   - Ensure your OpenMemory setup can handle the load
   - Consider clustering if OpenMemory supports it

3. **Add Redis for job queue:**
   - Replace simple threading with RQ or Celery
   - See commented code in `app/background_jobs.py`

4. **Use CDN/Proxy:**
   - Cloudflare, AWS CloudFront for webhook endpoints
   - Reduces latency, improves reliability

---

## Security Checklist

- ✅ HMAC signature validation enabled (ELEVENLABS_POST_CALL_HMAC_KEY set)
- ✅ API keys stored in .env (not committed to git)
- ✅ HTTPS enabled (use cloud platform or reverse proxy)
- ✅ OpenMemory API key configured
- ✅ Strong HMAC secret (32+ random characters)
- ✅ Rate limiting configured (optional, for production)

---

## Cost Optimization

### Reduce LLM Costs:

1. **Use cheaper models:**
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo  # Instead of gpt-4-turbo
   ```

2. **Use Groq (faster & cheaper):**
   ```bash
   LLM_PROVIDER=groq
   LLM_MODEL=mixtral-8x7b-32768
   ```

3. **Adjust memory extraction:**
   - Reduce `importance` threshold to store fewer memories
   - Increase deduplication threshold to reinforce more, store less

---

## Next Steps

1. ✅ Setup Python environment and install dependencies
2. ✅ Configure independent OpenMemory instance
3. ✅ Configure .env with all API keys
4. ✅ Run application locally with ngrok
5. ✅ Configure ElevenLabs webhooks
6. ✅ Test with sample calls
7. ✅ Monitor logs for 24 hours
8. ✅ Deploy to production cloud platform
9. ✅ Adjust thresholds based on results

**Your universal agent memory system is ready!** 🚀
