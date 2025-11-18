import os
import json
import time
from typing import List, Dict, Any, Optional

import requests


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default model, can be overridden with env var:
#   export OPENROUTER_MODEL="perplexity/sonar"
DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "perplexity/sonar")


class LLMError(Exception):
    """Raised for any LLM / OpenRouter related error."""
    pass


def _check_api_key() -> None:
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set in the environment.")


def call_llm(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    timeout: int = 60,
    max_retries: int = 2,
) -> str:
    """
    Call OpenRouter chat completions and return the assistant message text.

    messages: list of { "role": "system"|"user"|"assistant", "content": "text" }
    model: override model name (defaults to env OPENROUTER_MODEL or 'perplexity/sonar')
    max_tokens: requested max_tokens for the response
    temperature: sampling temperature
    timeout: per-request timeout in seconds
    max_retries: number of retries on transient network / 5xx errors

    raises LLMError on any logical / API error.
    """
    _check_api_key()

    payload: Dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-domain-or-ip",
        "X-Title": "AI Research Agent",
    }

    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            try:
                resp.raise_for_status()
            except requests.HTTPError as http_err:
                snippet = resp.text[:300]
                raise LLMError(
                    f"OpenRouter HTTP error {resp.status_code}: {http_err}; "
                    f"body snippet: {snippet}"
                ) from http_err

            data = resp.json()

            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise LLMError(
                    "Unexpected OpenRouter response format. "
                    f"Raw body: {json.dumps(data)[:500]}"
                ) from e

        except (requests.Timeout, requests.ConnectionError) as net_err:
            last_exc = net_err
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise LLMError(f"Network error calling OpenRouter: {net_err}") from net_err

        except requests.RequestException as req_err:
            raise LLMError(f"Request error calling OpenRouter: {req_err}") from req_err

    raise LLMError(f"Failed to call OpenRouter after {max_retries + 1} attempts: {last_exc}")
