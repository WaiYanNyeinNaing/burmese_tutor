import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
import json

app = Flask(__name__)

# Placeholder SDK key for the local OpenAI-compatible endpoint. This is not a real secret.
client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="sk-no-key-required"
)

TUTOR_SYSTEM = (
    "You are Burmese Tutor by AI4Burmese, a Burmese-first AI tutor guiding a learner through pasted study material. "
    "Default to clear Burmese (Myanmar Unicode), but switch to the learner's requested language when helpful. "
    "Teach through a guided conversation, not a long dump. "
    "Personalize the explanation to the learner's apparent level and current question. "
    "Use this structure as သင်ယူမှု ခွဲခြမ်းစိတ်ဖြာချက်: brief overview, one key idea, why it matters, "
    "a simple example, then a short check question. "
    "Only cover one main point at a time. "
    "After each point, ask whether the learner understands and wait for their response before moving on. "
    "If the source text is English, explain key concepts in Burmese and keep important technical terms in parentheses. "
    "Be warm, concise, and proactive."
)

TRANSLATION_MAX_TOKENS = 220
BREAKDOWN_MAX_TOKENS = 520
CHAT_MAX_TOKENS = 420
REQUEST_EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}

LESSON_START_PROMPT = (
    "Start the tutoring session now. "
    "Greet the learner in Burmese, say you will guide them step by step through the text, "
    "offer Burmese-first support with multilingual follow-up if needed, "
    "and ask whether they are ready to begin. "
    "Do not provide the full lesson yet."
)

TRANSLATOR_SYSTEM = (
    "You are a professional English to Burmese translator. "
    "Translate accurately, preserve meaning, use natural Myanmar Unicode. "
    "Do not add explanations unless asked."
)


def build_chat_messages(history, source_text=""):
    messages = [{"role": "system", "content": TUTOR_SYSTEM}]

    if source_text:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Use the following study material as optional context for the chat. "
                    "Only rely on it when relevant.\n\n"
                    f"{source_text}"
                ),
            }
        )

    for item in history:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    return messages


def build_lesson_start_messages(source_text):
    return [
        {"role": "system", "content": TUTOR_SYSTEM},
        {
            "role": "system",
            "content": (
                "Use the following study material as the lesson source. "
                "Keep the whole conversation grounded in it.\n\n"
                f"{source_text}"
            ),
        },
        {"role": "user", "content": LESSON_START_PROMPT},
    ]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    # 1) Translate (English -> Burmese) - optional but useful for UI
    translation_completion = client.chat.completions.create(
        model="padauk-agent",
        messages=[
            {"role": "system", "content": TRANSLATOR_SYSTEM},
            {"role": "user", "content": user_text}
        ],
        temperature=0.2,
        max_tokens=TRANSLATION_MAX_TOKENS,
        extra_body=REQUEST_EXTRA_BODY,
        stream=False
    )
    translation = translation_completion.choices[0].message.content

    # 2) Tutor breakdown in Burmese
    tutor_completion = client.chat.completions.create(
        model="padauk-agent",
        messages=[
            {"role": "system", "content": TUTOR_SYSTEM},
            {"role": "user", "content": user_text}
        ],
        temperature=0.6,
        max_tokens=BREAKDOWN_MAX_TOKENS,
        extra_body=REQUEST_EXTRA_BODY,
        stream=False
    )
    breakdown = tutor_completion.choices[0].message.content

    return jsonify({"translation": translation, "breakdown": breakdown})

@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text"}), 400
    completion = client.chat.completions.create(
        model="padauk-agent",
        messages=[
            {"role": "system", "content": TRANSLATOR_SYSTEM},
            {"role": "user", "content": text}
        ],
        temperature=0.2,
        max_tokens=TRANSLATION_MAX_TOKENS,
        extra_body=REQUEST_EXTRA_BODY,
    )
    return jsonify({"result": completion.choices[0].message.content})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    history = data.get("messages") or []
    source_text = data.get("sourceText", "").strip()

    if not isinstance(history, list) or not history:
        return jsonify({"error": "No messages"}), 400

    messages = build_chat_messages(history, source_text)

    def generate():
        try:
            stream = client.chat.completions.create(
                model="padauk-agent",
                messages=messages,
                temperature=0.6,
                max_tokens=CHAT_MAX_TOKENS,
                extra_body=REQUEST_EXTRA_BODY,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield json.dumps({"delta": delta}, ensure_ascii=False) + "\n"

            yield json.dumps({"done": True}, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")


@app.route("/api/tutor/start", methods=["POST"])
def tutor_start():
    data = request.get_json() or {}
    source_text = data.get("sourceText", "").strip()

    if not source_text:
        return jsonify({"error": "No source text"}), 400

    messages = build_lesson_start_messages(source_text)

    def generate():
        try:
            stream = client.chat.completions.create(
                model="padauk-agent",
                messages=messages,
                temperature=0.6,
                max_tokens=CHAT_MAX_TOKENS,
                extra_body=REQUEST_EXTRA_BODY,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield json.dumps({"delta": delta}, ensure_ascii=False) + "\n"

            yield json.dumps({"done": True}, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n"

    return Response(stream_with_context(generate()), mimetype="application/x-ndjson")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
