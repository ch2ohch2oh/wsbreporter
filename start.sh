#!/bin/bash
# Simple wrapper script to run wsbreporter with uv

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the combined pipeline in uv's managed environment.
# Pass all arguments through using "$@"
cd "$SCRIPT_DIR" || exit 1
uv run python -m wsbreporter.pipeline "$@"
