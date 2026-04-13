#!/bin/bash

# Manual Scene Flow Evaluation Wrapper Script
# This script sets up the environment and runs the manual evaluation

cd /code/springwebsite

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source /code/springwebsite/springwebsite/load_spring_env.sh

# Check if entry ID is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <entry_id>"
    echo "Example: $0 252"
    echo ""
    echo "Available commands:"
    echo "  $0 status    - Check evaluation status"
    echo "  $0 kill      - Kill running evaluation processes"
    echo "  $0 <entry_id> - Run manual evaluation for entry"
    exit 1
fi

# Run the evaluation manager
python eval_manager.py "$@"
