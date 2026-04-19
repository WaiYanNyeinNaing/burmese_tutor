#!/bin/bash
set -e

# 1. Create virtual env
python3 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip and install deps
pip install --upgrade pip
pip install "ai4burmese[full]" flask openai

# 3. Set llama-server path (adjust if needed)
export AI4BURMESE_LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"

# 4. Download model (q8_0 is a good balance)
ai4burmese download --quant q8_0

# 5. Start ai4burmese server in background
ai4burmese serve --quant q8_0 --backend auto --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
echo "ai4burmese server started (PID $SERVER_PID) on http://127.0.0.1:8000"

# Wait a few seconds for server to be ready
sleep 5

# 6. Start Flask UI
python app.py

# Cleanup on exit
trap "kill $SERVER_PID" EXIT
