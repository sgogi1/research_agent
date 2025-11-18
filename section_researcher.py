import json
from typing import List, Dict, Any

from llm_client import call_llm, LLMError


SECTION_SYSTEM = """You are a deep research agent.
You write academically, like a high-level literature review.

You must:
- Go in depth on ONLY the requested section.
- Use numbered inline citations like [1], [2], etc. in the body.
- Base claims on real, citable sources.
- Return ONLY valid JSON in the schema below.

Schema:
{
  "body": "<detailed section text with inline [1]-style citations>",
  "sources": [
    {
      "id": 1,
      "title": "Paper / article / study title",
      "url": "https://...",
      "source_type": "clinical study / review / mechanism paper / policy report / etc.",
      "why_relevant": "one sentence explaining why this source matters"
    }
  ]
}

Rules:
- Focus only on the specified section's title and goal.
- Reuse the same id if you cite the same source multiple times in body.
- sources[].id must match the [id] markers in body.
- Use at least 3 distinct sources where possible.
- NEVER include commentary outside of the JSON.
"""


def _robust_json_parse(raw: str) -> Dict[str, Any]:
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    sliced = raw[start : end + 1]
    return json.loads(sliced)


def research_section(
    topic: str,
    queries: List[str],
    section_title: str,
    section_goal: str,
) -> Dict[str, Any]:
    """
    Research and write a single section of the report.

    Returns dict:
    {
      "body": "<text with [1] citations>",
      "sources": [
        {"id": 1, "title": "...", "url": "...", "source_type": "...", "why_relevant": "..."},
        ...
      ],
      "raw": "<raw LLM output>",
      "error": "<optional>"
    }
    """
    topic = (topic or "").strip()
    section_title = (section_title or "").strip()
    section_goal = (section_goal or "").strip()
    queries = queries or []

    queries_text = "\n".join(f"- {q}" for q in queries)

    user_prompt = f"""
Overall topic:
{topic}

Relevant research sub-queries (for context):
{queries_text}

Section to write:
"{section_title}"

Section goal / scope:
{section_goal}

Write a standalone section that would appear in a long-form research report.

Requirements:
- Cover this section's goal in depth, but avoid repeating a full introduction or conclusion of the entire topic.
- Use numbered inline citations like [1], [2], etc. that correspond to the sources you include.
- Prefer high-quality sources (systematic reviews, major studies, well-known reports) where possible.
- Return ONLY JSON as described in the schema.
"""

    try:
        raw = call_llm(
            [
                {"role": "system", "content": SECTION_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.35,
            max_tokens=1600,
        )

        data = _robust_json_parse(raw)

        body = str(data.get("body", "")).strip()
        sources_raw = data.get("sources", [])

        norm_sources = []
        if isinstance(sources_raw, List):
            for src in sources_raw:
                if not isinstance(src, dict):
                    continue
                src_id = src.get("id", None)
                title = str(src.get("title", "")).strip()
                url = str(src.get("url", "")).strip()
                source_type = str(src.get("source_type", "")).strip()
                why_relevant = str(src.get("why_relevant", "")).strip()

                if not title:
                    continue
                if src_id is None:
                    src_id = len(norm_sources) + 1

                norm_sources.append(
                    {
                        "id": int(src_id),
                        "title": title,
                        "url": url,
                        "source_type": source_type or "unspecified",
                        "why_relevant": why_relevant or f"Relevant to section '{section_title}'.",
                    }
                )

        if not body:
            body = (
                f"This section discusses {section_title.lower()} in the context of {topic}, "
                f"but the research assistant failed to provide detailed text."
            )

        return {
            "body": body,
            "sources": norm_sources,
            "raw": raw,
        }

    except (LLMError, ValueError, json.JSONDecodeError) as e:
        fallback_body = (
            f"This section was intended to cover '{section_title}' for the topic '{topic}', "
            "but an error occurred while generating detailed content."
        )
        return {
            "body": fallback_body,
            "sources": [],
            "error": str(e),
        }
