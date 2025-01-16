#!/bin/bash

# Path to the chat.log file
LOG_FILE="/home/student/singhr62/distributed-chat-app/chat.log"

# Check if the file exists and delete it
if [ -f "$LOG_FILE" ]; then
    rm "$LOG_FILE"
    echo "Deleted $LOG_FILE"
else
    echo "$LOG_FILE does not exist"
fi