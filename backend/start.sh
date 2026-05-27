#!/bin/bash
set -e

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p temp/uploads temp/original temp/cleaned temp/outputs

# Start the application
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
