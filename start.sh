#!/bin/bash
# filepath: /home/fullaware/projects/beryl/start.sh

# Run with Uvicorn (perfect for FastAPI)
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Note: To install required packages:
# pip install fastapi uvicorn jinja2 python-multipart fastapi-sessions