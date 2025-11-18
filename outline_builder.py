import json
from typing import List, Dict, Any

from llm_client import call_llm, LLMError


OUTLINE_SYSTEM = """You are an academic research planning agent.
Your job: design a section outline for a deep, citation-backed research report.

Output JSON only in this schema:
{
  "sections": [
    {
      "title": "Background and Historical Context",
      "goal": "Explain origin, early discoveries, and key milestones...",
      "priority": 1
    },
    {
      "title": "Mechanisms / Technical Foundations",
      "goal": "Explain how this works at the conceptual, technical, or mechanistic level...",
      "priority": 2
    },
    {
      "title": "Evidence, Applications, or Case Studies",
      "goal": "Summarize key studies, deployments, outcomes, limitations...",
      "priority": 3
    },
    {
      "title": "Risks, Limitations, and Open Questions",
      "goal": "Discuss concerns, controversies, failure modes, and unknowns...",
      "priority": 4
    },
    {
      "title": "Future Directions and Conclusion",
      "goal": "Where this is going, why it matters, and a final synthesis.",
      "priority": 5
    }
  ]
}

Rules:
- Tailor titles and goals to the specific topic and its refined queries.
- 5 to 7 sections total.
- priority must be 1..N with no gaps.
- The outline should be suitable for a long-form, citation-backed research report.
- No commentary outside JSON.
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


def build_outline(topic: str, queries: List[str]) -> List[Dict[str, Any]]:
    """
    Take a refined topic and its sub-queries and return a list of sections:
    [
      {"title": "...", "goal": "...", "priority": 1},
      ...
    ]
    """
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Empty topic passed to build_outline")

    queries_text = "\n".join(f"- {q}" for q in (queries or []))

    user_prompt = f"""
Topic:
{topic}

Refined sub-questions to consider:
{queries_text}

Create a section plan for a long-form, citation-backed research report on this topic.

Each section should:
- Have a concise, informative title.
- Have a clear goal that describes what belongs in that section.
- Be ordered by priority from 1..N where 1 is the first section in the report.
"""

    try:
        raw = call_llm(
            [
                {"role": "system", "content": OUTLINE_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
            max_tokens=800,
        )

        data = _robust_json_parse(raw)
        sections = data.get("sections", [])

        norm_sections: List[Dict[str, Any]] = []
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                continue
            title = str(sec.get("title", "")).strip()
            goal = str(sec.get("goal", "")).strip()
            priority = sec.get("priority", i + 1)

            if not title:
                continue

            norm_sections.append(
                {
                    "title": title,
                    "goal": goal or f"Explain the key aspects of {title.lower()} in the context of {topic}.",
                    "priority": int(priority),
                }
            )

        if not norm_sections:
            raise ValueError("No valid sections produced")

        norm_sections.sort(key=lambda s: s["priority"])
        for idx, sec in enumerate(norm_sections, start=1):
            sec["priority"] = idx

        norm_sections = norm_sections[:7]
        if len(norm_sections) < 3:
            while len(norm_sections) < 3:
                norm_sections.append(
                    {
                        "title": f"Additional Analysis {len(norm_sections)+1}",
                        "goal": f"Provide further analysis related to {topic}.",
                        "priority": len(norm_sections) + 1,
                    }
                )

        return norm_sections

    except (LLMError, ValueError, json.JSONDecodeError):
        return [
            {
                "title": "Background and Context",
                "goal": f"Explain the foundational background and context for {topic}.",
                "priority": 1,
            },
            {
                "title": "Current State and Key Debates",
                "goal": f"Describe the current state of {topic}, major approaches, and key debates.",
                "priority": 2,
            },
            {
                "title": "Risks, Limitations, and Future Directions",
                "goal": f"Discuss limitations, open questions, and where {topic} may be heading.",
                "priority": 3,
            },
        ]
