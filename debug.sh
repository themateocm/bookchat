#!/bin/bash

# Toggle debug mode
if [ -z "$BOOKCHAT_DEBUG" ]; then
    echo "Enabling debug mode..."
    export BOOKCHAT_DEBUG=true
else
    echo "Disabling debug mode..."
    unset BOOKCHAT_DEBUG
fi

# Restart the server using restart_server.sh
./restart_server.sh

echo "Debug mode is now $([ ! -z "$BOOKCHAT_DEBUG" ] && echo "enabled" || echo "disabled")"
