#!/bin/bash

# Kill any existing Python processes running server.py
pkill -f "python3 server.py"

# Wait a moment for the port to be freed
sleep 1

# Start the server in the background
python3 server.py &

# Exit successfully
exit 0
