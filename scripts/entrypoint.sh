#!/bin/sh
# Fix permissions for mounted volume (run as root)
if [ -d "/home/appuser/.nypai-chatbot" ]; then
    chown -R appuser:appgroup /home/appuser/.nypai-chatbot
    chmod -R 755 /home/appuser/.nypai-chatbot
fi

# Switch to appuser and execute the command
if [ "$(id -u)" = "0" ]; then
    # We're running as root, switch to appuser
    exec su appuser -c "$*"
else
    # We're already running as appuser, execute directly
    exec "$@"
fi
