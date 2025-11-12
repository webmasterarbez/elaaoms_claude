# Utility Scripts

This directory contains utility scripts for the ElevenLabs + OpenMemory integration system.

## get_conversation.py

Fetches conversation details from ElevenLabs API and sends them to the OpenMemory system via the `/webhook/post-call` endpoint.

### Setup

1. Set your ElevenLabs API key in your `.env` file:
   ```bash
   ELEVENLABS_API_KEY=your_api_key_here
   ```

2. Optionally configure the webhook URL (defaults to `http://localhost:8000/webhook/post-call`):
   ```bash
   WEBHOOK_URL=http://your-webhook-url.com/webhook/post-call
   ```

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

- The script adds an `X-Internal-Request: true` header to bypass HMAC signature validation
- Make sure your webhook endpoint is running before executing the script
- You need a valid ElevenLabs API key with access to the Conversational AI API
