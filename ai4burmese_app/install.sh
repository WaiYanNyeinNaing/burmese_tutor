#!/usr/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

export AI4BURMESE_LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"

if [ ! -d "$HOME/.ai4burmese/models" ]; then
  ai4burmese download --quant q8_0
fi

echo "Starting ai4burmese server on http://127.0.0.1:8000 ..."
nohup ai4burmese serve --quant q8_0 --backend auto --host 127.0.0.1 --port 8000 > ai4burmese.log 2>&1 &
SERVER_PID=$!

echo "Waiting for ai4burmese server..."
until curl -s http://127.0.0.1:8000/v1/models > /dev/null; do
  sleep 2
done
echo "ai4burmese server ready."

echo "Starting UI on http://localhost:5000 ..."
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
