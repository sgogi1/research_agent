import json
from typing import Dict, Any, List

from llm_client import call_llm, LLMError


REFINER_SYSTEM_INSTRUCTIONS = """You are a Query Refiner Agent.

Your job: take the user's research topic and generate a cleaned, concise topic
plus a set of high-quality, specific, research-oriented search queries.

Rules:
- Do NOT add explanations.
- Output valid JSON ONLY.
- JSON schema:
{
  "topic": "<cleaned topic title>",
  "queries": [
    "<query 1>",
    "<query 2>",
    ...
  ]
}
- "queries" should be distinct, information-dense, and cover different angles:
  historical, technical, economic, social, policy, ethical, and future outlook.
"""


def _robust_json_parse(raw: str) -> Dict[str, Any]:
    """
    Try to parse JSON directly; if that fails, attempt to slice out the first {...} block.
    Raise ValueError if we still can't parse anything.
    """
    raw = raw.strip()

    # First attempt: straightforward
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first {...} region
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    sliced = raw[start : end + 1]
    return json.loads(sliced)


def refine_topic_to_queries(user_topic: str, n_queries: int = 10) -> Dict[str, Any]:
    """
    Take a user topic string and return:
    {
      "topic": "<normalized topic>",
      "queries": ["q1", "q2", ..., "qN"]
    }

    If anything goes wrong, we fall back to a minimal, safe structure.
    """
    user_topic = (user_topic or "").strip()
    if not user_topic:
        raise ValueError("Empty topic passed to refine_topic_to_queries")

    user_prompt = f"""
User topic: "{user_topic}"

Return ONLY JSON following the schema:

{{
  "topic": "<cleaned topic title>",
  "queries": [
    "<query 1>",
    "<query 2>",
    "... up to about {n_queries} queries ..."
  ]
}}

Guidelines:
- "topic": make it concise, specific, and academic in tone.
- "queries": {n_queries} distinct, relevant, information-dense queries that would
  help investigate this topic scientifically, historically, clinically, economically,
  technically, and ethically.
"""

    try:
        raw = call_llm(
            [
                {"role": "system", "content": REFINER_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": user_prompt},
            ],
            # lower temperature for more structured, less creative output
            temperature=0.2,
            max_tokens=800,
        )
        data = _robust_json_parse(raw)

        topic = str(data.get("topic", user_topic)).strip() or user_topic

        queries_raw = data.get("queries", [])
        if not isinstance(queries_raw, list):
            queries_raw = [str(queries_raw)]

        # Clean queries: cast to str, strip empties, dedupe, cap length
        cleaned: List[str] = []
        seen = set()
        for q in queries_raw:
            q_str = str(q).strip()
            if not q_str:
                continue
            if q_str in seen:
                continue
            seen.add(q_str)
            cleaned.append(q_str)
            if len(cleaned) >= n_queries:
                break

        # Ensure we always have at least one query
        if not cleaned:
            cleaned = [topic]

        return {
            "topic": topic,
            "queries": cleaned,
            "raw": raw,  # optional: keep raw LLM response for debugging
        }

    except (LLMError, ValueError, json.JSONDecodeError) as e:
        # Graceful fallback: don't kill the whole pipeline
        # You can log `e` somewhere if you want.
        return {
            "topic": user_topic,
            "queries": [user_topic],
            "error": str(e),
        }
