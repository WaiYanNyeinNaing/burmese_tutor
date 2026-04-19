#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "ai4burmese[full]"
pip install -r requirements.txt

export AI4BURMESE_LLAMA_SERVER="${AI4BURMESE_LLAMA_SERVER:-$HOME/llama.cpp/build/bin/llama-server}"

echo "Downloading Padauk model (q8_0)..."
ai4burmese download --quant q8_0

echo "Starting ai4burmese server on http://127.0.0.1:8000 ..."
ai4burmese serve --quant q8_0 --backend auto --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

sleep 8

echo "Starting Tutor UI on http://127.0.0.1:5000 ..."
python app.py

kill $SERVER_PID
