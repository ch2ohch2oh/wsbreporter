#!/bin/bash
# Simple wrapper script to run wsbreporter with the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the Python script using the venv's Python interpreter
# Pass all arguments through using "$@"
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/run.py" "$@"
