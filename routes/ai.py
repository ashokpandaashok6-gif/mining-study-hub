import requests
from flask import Blueprint, render_template, request, current_app, jsonify
from flask_login import login_required

bp = Blueprint("ai", __name__, url_prefix="/ai")

SYSTEM_PROMPT = (
    "You are a study assistant for Diploma in Mining Engineering students in India "
    "(SCTE&VT / Polytechnic syllabus). Give clear, exam-oriented answers. "
    "When asked for an N-mark answer, structure it with headings and bullet points. "
    "When asked to generate MCQs or viva questions, number them and clearly mark the answers. "
    "Keep mining engineering terminology technically accurate."
)


def call_anthropic(prompt, api_key, model):
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model or "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "system": SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    return "\n".join(
        block["text"]
        for block in payload["content"]
        if block["type"] == "text"
    )


def call_groq(prompt, api_key, model):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 1500
        },
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    return payload["choices"][0]["message"]["content"]


def call_gemini(prompt, api_key, model):
    model = model or "gemini-2.5-flash"

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        headers={
            "Content-Type": "application/json"
        },
        json={
            "systemInstruction": {
                "parts": [
                    {
                        "text": SYSTEM_PROMPT
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        },
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    return "\n".join(
        part["text"]
        for part in payload["candidates"][0]["content"]["parts"]
    )


QUICK_PROMPTS = [
    "Explain Longwall Mining",
    "Give a 7-mark answer on Roof Bolting",
    "Generate 5 MCQs on Mine Ventilation",
    "Generate 10 Viva Questions on Mine Surveying",
    "Summarize Bord and Pillar Method",
]


@bp.route("/")
@login_required
def assistant():
    return render_template(
        "ai_assistant.html",
        quick_prompts=QUICK_PROMPTS
    )


@bp.route("/ask", methods=["POST"])
@login_required
def ask():

    data = request.get_json(silent=True) or {}

    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({
            "error": "Please enter a question."
        }), 400

    provider = (
        current_app.config.get("AI_PROVIDER") or "groq"
    ).lower()

    api_key = current_app.config.get("AI_API_KEY")
    model = current_app.config.get("AI_MODEL")

    if not api_key:
        return jsonify({
            "error": "AI_API_KEY is missing in your .env file."
        }), 503

    try:

        if provider == "groq":
            answer = call_groq(prompt, api_key, model)

        elif provider == "anthropic":
            answer = call_anthropic(prompt, api_key, model)

        elif provider == "gemini":
            answer = call_gemini(prompt, api_key, model)

        else:
            return jsonify({
                "error": f"Unknown provider: {provider}"
            }), 500

        return jsonify({
            "answer": answer
        })

    except requests.exceptions.HTTPError as e:

        print("\n========== AI ERROR ==========")

        print("Status Code:", e.response.status_code)

        print(e.response.text)

        print("==============================\n")

        return jsonify({
            "error": e.response.text
        }), 502

    except Exception as e:

        print(e)

        return jsonify({
            "error": str(e)
        }), 500