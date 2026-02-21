#!/bin/bash
# Start AlleyBot Dashboard Server
echo "🦞 Starting AlleyBot Dashboard Server..."

# Activate virtual environment
source venv/bin/activate

# Install aiohttp-cors if not available
pip install aiohttp-cors > /dev/null 2>&1

# Start the dashboard server
python3 web_server.py
