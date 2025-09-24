#!/bin/bash

# Script to navigate to the backend directory and activate the virtual environment

# Change to the backend directory
cd "$(dirname "$0")/backend"

# Activate the virtual environment
. ./newvenv/bin/activate

# Print success message
echo "Virtual environment activated in $(pwd)"
echo "Python version: $(python -V)"
echo "Type 'exit' or press Ctrl+D to exit this shell"

# Start a new interactive shell
exec $SHELL