#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Function to log errors
error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    error "Python3 is not installed"
    exit 1
fi

# Check if required ports are available
check_port 8000
if [ $? -eq 1 ]; then
    error "Port 8000 is already in use"
    exit 1
fi

check_port 8080
if [ $? -eq 1 ]; then
    error "Port 8080 is already in use"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p logs

# Start API server
log "Starting API server on port 8000..."
nohup python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
API_PID=$!

# Wait a moment to ensure API server starts
sleep 2

# Check if API server started successfully
if ! ps -p $API_PID > /dev/null; then
    error "Failed to start API server"
    exit 1
fi

# Start web server
log "Starting web server on port 8080..."
nohup python3 -m http.server 8080 > logs/web.log 2>&1 &
WEB_PID=$!

# Wait a moment to ensure web server starts
sleep 2

# Check if web server started successfully
if ! ps -p $WEB_PID > /dev/null; then
    error "Failed to start web server"
    kill $API_PID
    exit 1
fi

log "Both servers started successfully!"
log "API server running on http://localhost:8000"
log "Web server running on http://localhost:8080"
log "API logs: logs/api.log"
log "Web server logs: logs/web.log"

# Save PIDs for cleanup
echo $API_PID > logs/api.pid
echo $WEB_PID > logs/web.pid

# Function to handle script termination
cleanup() {
    log "Shutting down servers..."
    kill $API_PID
    kill $WEB_PID
    rm -f logs/*.pid
    log "Servers stopped"
    exit 0
}

# Register cleanup function
trap cleanup SIGINT SIGTERM

# Keep script running
while true; do
    sleep 1
done
