#!/bin/bash

# Kill any existing server processes
pkill -f "python server.py" || true

# Wait a moment to ensure the port is released
sleep 1

# Start the server
python server.py
