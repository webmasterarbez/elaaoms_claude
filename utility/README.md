# Utility Scripts

This directory contains utility scripts for the ElevenLabs + OpenMemory integration system.

## Quick Reference

| Script | Purpose |
|--------|---------|
| `get_conversation.py` | Fetch and process conversations from ElevenLabs API |
| `generate_hmac.py` | Generate valid HMAC signatures for testing webhooks |
| `sample_payload.json` | Sample webhook payload for testing |

## get_conversation.py

Fetches conversation details from ElevenLabs API and sends them to the OpenMemory system via the `/webhook/post-call` endpoint.

### Setup

1. Set your ElevenLabs credentials in your `.env` file:
   ```bash
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_POST_CALL_HMAC_KEY=your_hmac_key_from_elevenlabs
   ```

2. Optionally configure the webhook URL (defaults to `http://localhost:8000/webhook/post-call`):
   ```bash
   WEBHOOK_URL=http://your-webhook-url.com/webhook/post-call
   ```

### Security

All requests to the webhook endpoint are signed with HMAC-SHA256 using the same algorithm as ElevenLabs webhooks. This ensures that:
- Only authorized requests can send data to the webhook
- The webhook can verify the authenticity of the request
- No one can bypass signature validation with fake headers

### Usage

**Process a single conversation:**
```bash
python utility/get_conversation.py conv_abc123xyz
```

**Process multiple conversations:**
```bash
python utility/get_conversation.py conv_abc123 conv_def456 conv_ghi789
```

**Use custom webhook URL:**
```bash
WEBHOOK_URL=http://example.com/webhook/post-call python utility/get_conversation.py conv_abc123
```

**Enable debug logging:**
```bash
python utility/get_conversation.py --debug conv_abc123
```

**Use API key from command line:**
```bash
python utility/get_conversation.py --api-key YOUR_KEY conv_abc123
```

### What it does

1. Fetches conversation details from ElevenLabs API using the conversation ID
2. Formats the response to match the ElevenLabs webhook structure (`post_call_transcription` type)
3. Sends the formatted data to the `/webhook/post-call` endpoint
4. The webhook endpoint then:
   - Saves the transcription to local storage
   - Sends it to OpenMemory for persistence and search

### Output

The script provides detailed logging of:
- API requests to ElevenLabs
- Webhook POST requests
- Success/failure status for each conversation
- Final summary with counts

### Exit Codes

- `0`: All conversations processed successfully
- `1`: Some or all conversations failed to process

### Notes

- The script signs all requests with HMAC-SHA256 for security
- Make sure your webhook endpoint is running before executing the script
- You need a valid ElevenLabs API key with access to the Conversational AI API
- Both `ELEVENLABS_API_KEY` and `ELEVENLABS_POST_CALL_HMAC_KEY` are required

---

## generate_hmac.py

Generates valid HMAC-SHA256 signatures for testing webhook endpoints that require ElevenLabs-style HMAC authentication.

### Usage

**Generate signature from JSON file:**
```bash
python utility/generate_hmac.py utility/sample_payload.json
```

**Generate signature from inline JSON:**
```bash
python utility/generate_hmac.py --payload '{"type":"post_call_transcription","data":{}}'
```

**Use custom secret:**
```bash
python utility/generate_hmac.py sample_payload.json --secret my_secret_key
```

**Generate for specific endpoint:**
```bash
python utility/generate_hmac.py sample_payload.json \
  --url http://localhost:8000 \
  --endpoint /webhook/client-data
```

**Generate with specific timestamp (for testing replay attacks):**
```bash
python utility/generate_hmac.py sample_payload.json --timestamp 1234567890
```

**Show only signature (no curl command):**
```bash
python utility/generate_hmac.py sample_payload.json --no-curl
```

### What it does

1. Reads the JSON payload (from file or command line)
2. Generates a valid HMAC-SHA256 signature using the provided secret
3. Outputs the `elevenlabs-signature` header value
4. Provides a ready-to-use cURL command for testing

### Output Example

```
======================================================================
HMAC-SHA256 Signature Generated
======================================================================

Payload: {"type":"post_call_transcription","data":{...}}
Secret:  your_hmac_secret_key
Header:  elevenlabs-signature: t=1699876543,v0=abc123def456...

======================================================================
Complete cURL Command
======================================================================

curl -X POST http://localhost:8000/webhook/post-call \
  -H "Content-Type: application/json" \
  -H "elevenlabs-signature: t=1699876543,v0=abc123def456..." \
  -d '{"type":"post_call_transcription","data":{...}}'

======================================================================
✅ Ready to test!
======================================================================
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `file` | JSON payload file path | - |
| `-p, --payload` | JSON payload as string | - |
| `-s, --secret` | HMAC secret key | `your_hmac_secret_key` |
| `-t, --timestamp` | Unix timestamp | Current time |
| `-u, --url` | Base URL | `http://localhost:8000` |
| `-e, --endpoint` | Endpoint path | `/webhook/post-call` |
| `--no-curl` | Don't generate curl command | False |

### Testing with sample_payload.json

A sample payload file is provided for testing:

```bash
# Test post-call webhook
python utility/generate_hmac.py utility/sample_payload.json

# Copy and run the generated curl command
```

### Integration with Tests

You can integrate this into your test workflow:

```bash
# Generate signature and execute in one command
SIGNATURE=$(python utility/generate_hmac.py sample_payload.json --no-curl | grep "Header:" | cut -d' ' -f4-)
curl -X POST http://localhost:8000/webhook/post-call \
  -H "Content-Type: application/json" \
  -H "elevenlabs-signature: $SIGNATURE" \
  -d @utility/sample_payload.json
```

### Notes

- The timestamp is automatically set to the current time unless specified
- Timestamps must be within 30 minutes of the server's current time
- The signature format is: `t=<timestamp>,v0=<hmac_hash>`
- The HMAC is calculated on: `<timestamp>.<json_payload>`
- Use the same secret key that's configured in your `.env` file's `ELEVENLABS_POST_CALL_HMAC_KEY`

---

## sample_payload.json

A complete sample webhook payload for testing. Contains a realistic conversation transcript with:
- Multiple message exchanges
- Agent and user roles
- Order tracking conversation
- Dynamic variables (caller_id)

Use this with `generate_hmac.py` for quick testing without creating payloads manually.
