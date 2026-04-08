#!/usr/bin/env bash
set -euo pipefail

# Start FastAPI backend in background for Streamlit to consume.
uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cleanup() {
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Start Streamlit (main public app for Hugging Face Space).
exec streamlit run ui.py --server.address 0.0.0.0 --server.port 8501
