# burmese_tutor

![burmese_tutor hero](docs/images/padauk-tutor-hero.svg)

`burmese_tutor` is a public Burmese-first personalized learning demo by AI4Burmese. It wraps a fine-tuned agentic tutor model in a lightweight local web app so learners can paste study material and receive step-by-step guidance in Burmese or another preferred language.

Developed by Dr. Wai Yan Nyein Naing.

## What It Does

- Personalized lesson flow grounded in the learner's pasted source text
- Burmese-native tutoring with multilingual support when requested
- Fine-tuned agentic tutor behavior for guided, one-step-at-a-time teaching
- On-device small LLM workflow powered by the [`ai4burmese`](https://pypi.org/project/ai4burmese/) runtime
- Streaming local chat UI for practical study sessions

## Why This Repo Exists

This repository is a clean public export of the current tutor app experience from AI4Burmese. It keeps the current screenshots and app assets while publishing only the tracked project files needed to run the demo locally.

## How AI4Burmese Powers It

[`ai4burmese`](https://pypi.org/project/ai4burmese/) provides the Burmese-first model runtime used here to:

- download the small local GGUF model
- start a local OpenAI-compatible server at `http://127.0.0.1:8000/v1`
- serve the tutor model used by the Flask app

The web UI in this repo stays intentionally small. The model runtime and on-device inference path come from AI4Burmese.

## App Screenshot

![burmese_tutor screenshot](docs/images/app-screenshot.png)

## Quick Setup

```bash
cd ai4burmese_app
chmod +x install_and_run.sh
./install_and_run.sh
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Manual Setup

```bash
cd ai4burmese_app
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "ai4burmese[full]" flask openai
ai4burmese download --quant q8_0
ai4burmese serve --quant q8_0 --backend auto --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd ai4burmese_app
source .venv/bin/activate
python app.py
```

If your machine does not automatically find `llama-server`, set:

```bash
export AI4BURMESE_LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
```

## Notes On Public Safety

- This public copy was exported from the current tracked files only.
- `.env`, local databases, key material, logs, and virtual environments are ignored.
- The OpenAI SDK key in the app is a local placeholder for the OpenAI-compatible interface and is not a real secret.

## Repo Layout

- `ai4burmese_app/app.py`: Flask backend and streaming tutor endpoints
- `ai4burmese_app/templates/index.html`: tutor UI
- `ai4burmese_app/static/app.js`: streaming chat client
- `docs/images/`: README screenshots and visuals
