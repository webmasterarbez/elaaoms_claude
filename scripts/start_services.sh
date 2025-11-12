#!/bin/bash

# ElevenLabs Webhook Service Startup Script
# This script starts both ngrok and FastAPI services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run from project root:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Activate venv
source "$VENV_DIR/bin/activate"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}ElevenLabs Webhook Service Startup${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to handle cleanup
cleanup() {
    echo -e "${BLUE}Shutting down services...${NC}"
    # Kill any child processes
    kill $(jobs -p) 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Start ngrok in background
echo -e "${GREEN}Starting ngrok tunnel...${NC}"
python ngrok_config.py &
NGROK_PID=$!
sleep 5

# Start FastAPI service
echo -e "${GREEN}Starting FastAPI service...${NC}"
python main.py &
FASTAPI_PID=$!
sleep 3

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "NGrok Tunnel PID: $NGROK_PID"
echo "FastAPI Service PID: $FASTAPI_PID"
echo ""
echo "Services running:"
echo "  - FastAPI: http://localhost:8000"
echo "  - Swagger Docs: http://localhost:8000/docs"
echo "  - Webhook: POST /webhook/post-call"
echo ""
echo "To test webhooks (in another terminal):"
echo "  source venv/bin/activate"
echo "  python test_webhook.py"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait
