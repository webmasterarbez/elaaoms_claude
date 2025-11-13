#!/bin/bash

# ElevenLabs Webhook Service Management Script
# This script manages both ngrok and FastAPI services
# Usage: ./scripts/services.sh [start|stop|status]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
PID_FILE="$PROJECT_ROOT/.services.pids"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print usage
usage() {
    echo -e "${BLUE}ElevenLabs Webhook Service Manager${NC}"
    echo ""
    echo "Usage: $0 [start|stop|status]"
    echo ""
    echo "Commands:"
    echo "  start   - Start ngrok and FastAPI services"
    echo "  stop    - Stop ngrok and FastAPI services"
    echo "  status  - Show service status"
    echo ""
}

# Function to check if venv exists
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
        echo "Please run from project root:"
        echo "  python -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
}

# Function to start services
start_services() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}ElevenLabs Webhook Service Startup${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""

    check_venv

    # Check if services are already running
    if [ -f "$PID_FILE" ]; then
        EXISTING_PIDS=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [ ! -z "$EXISTING_PIDS" ]; then
            echo -e "${YELLOW}Warning: Services may already be running${NC}"
            show_status
            echo ""
            read -p "Continue with startup? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Startup cancelled"
                exit 0
            fi
        fi
    fi

    # Change to project root
    cd "$PROJECT_ROOT"

    # Activate venv
    source "$VENV_DIR/bin/activate"

    # Start ngrok in background
    echo -e "${GREEN}Starting ngrok tunnel...${NC}"
    python scripts/ngrok_config.py > /tmp/ngrok.log 2>&1 &
    NGROK_PID=$!
    sleep 5

    # Start FastAPI service
    echo -e "${GREEN}Starting FastAPI service...${NC}"
    cd "$PROJECT_ROOT/backend"
    python main.py > /tmp/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    cd "$PROJECT_ROOT"
    sleep 3

    # Save PIDs to file
    echo "$NGROK_PID $FASTAPI_PID" > "$PID_FILE"

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
    echo "  python tests/test_webhook.py"
    echo ""
    echo "View logs:"
    echo "  - Ngrok: tail -f /tmp/ngrok.log"
    echo "  - FastAPI: tail -f /tmp/fastapi.log"
    echo ""
    echo "To stop services:"
    echo "  $0 stop"
    echo ""
}

# Function to stop services
stop_services() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}ElevenLabs Webhook Service Shutdown${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""

    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}No service PIDs file found. Services may not be running.${NC}"
        return
    fi

    PIDS=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -z "$PIDS" ]; then
        echo -e "${YELLOW}No service PIDs found in $PID_FILE${NC}"
        return
    fi

    echo "Stopping services..."
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "${GREEN}Killing process $PID...${NC}"
            kill "$PID" 2>/dev/null || true
            # Wait a bit for graceful shutdown
            sleep 1
            # Force kill if still running
            if kill -0 "$PID" 2>/dev/null; then
                kill -9 "$PID" 2>/dev/null || true
            fi
        else
            echo -e "${YELLOW}Process $PID not running${NC}"
        fi
    done

    # Remove PID file
    rm -f "$PID_FILE"

    echo -e "${GREEN}Services stopped${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

# Function to show service status
show_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}No services running (no PID file)${NC}"
        return
    fi

    PIDS=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -z "$PIDS" ]; then
        echo -e "${YELLOW}No service PIDs found${NC}"
        return
    fi

    echo -e "${BLUE}Service Status:${NC}"
    RUNNING_COUNT=0
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            echo -e "  PID $PID: ${GREEN}RUNNING${NC}"
            RUNNING_COUNT=$((RUNNING_COUNT + 1))
        else
            echo -e "  PID $PID: ${RED}NOT RUNNING${NC}"
        fi
    done

    if [ $RUNNING_COUNT -eq 0 ]; then
        echo -e "${YELLOW}No services are currently running${NC}"
    fi
}

# Main script logic
if [ $# -eq 0 ]; then
    usage
    exit 0
fi

COMMAND=$1

case "$COMMAND" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
