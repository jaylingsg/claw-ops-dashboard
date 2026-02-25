#!/bin/bash
# Start Claw Ops Dashboard on port 3004

cd "$(dirname "$0")"

echo "Starting Claw Ops Dashboard on port 3004..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 3004
