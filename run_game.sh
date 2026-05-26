#!/usr/bin/env bash
# run_game.sh — wrapper called by the autograder
# Usage: bash run_game.sh <algorithm> <heuristic> <depth>
# Board is read from stdin; output goes to stdout/stderr unchanged.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/solution.py" "$1" "$2" "$3"
