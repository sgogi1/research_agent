import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")


class LLMError(Exception):
    pass


def _check_api_key():
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set in the environment.")


def call_llm(messages, model: str | None = None) -> str:
    """
    Call OpenRouter chat completions and return the assistant message text.

    messages: list of {role: "system"|"user"|"assistant", content: str}
    """
    _check_api_key()

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional but nice:
        "HTTP-Referer": "https://your-domain-or-ip",
        "X-Title": "AI Research Agent",
    }

    resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)

    if resp.status_code != 200:
        raise LLMError(f"OpenRouter error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected OpenRouter response format: {e}; body={json.dumps(data)[:400]}")
