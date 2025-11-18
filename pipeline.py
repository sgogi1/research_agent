from datetime import datetime
from typing import List, Dict, Any

from llm_client import call_llm
from research_html import render_report_html
from oped_html import render_oped_html
from storage import save_html, save_meta
from query_refiner import refine_topic_to_queries
from outline_builder import build_outline


def _split_body_and_sources(report_raw: str) -> tuple[str, List[str]]:
    """
    Very simple heuristic: look for a trailing 'Sources:' or 'References:' section
    and split it off into a list. If nothing is found, return the whole text as body
    and an empty sources list.
    """
    if not report_raw:
        return "", []

    sources: List[str] = []
    body_text = report_raw

    lower = report_raw.lower()
    for marker in ["sources:", "references:", "reference list:"]:
        idx = lower.rfind(marker)
        if idx != -1:
            body_text = report_raw[:idx].strip()
            src_block = report_raw[idx + len(marker) :].strip()
            sources = [
                line.strip("-• ").strip()
                for line in src_block.splitlines()
                if line.strip()
            ]
            break

    return body_text, sources


def generate_report_and_oped(user_topic: str, session_id: str) -> None:
    """
    High-level pipeline for a single research session.

    Steps:
    0) Use Query Refiner to normalize the topic and propose sub-queries.
    1) Use Outline Builder to propose a section plan for the research report.
    2) Ask the LLM to write a structured research report following that plan.
    3) Ask the LLM to write an op-ed that builds on the research.
    4) Render both as HTML and save them, along with structured metadata.
    """
    user_topic = (user_topic or "").strip()
    if not user_topic:
        raise ValueError("Topic is empty in generate_report_and_oped")

    # 0) Refinement: normalized topic + sub-queries
    refinement: Dict[str, Any] = refine_topic_to_queries(user_topic, n_queries=10)
    refined_topic: str = refinement.get("topic", user_topic)
    queries: List[str] = refinement.get("queries", [refined_topic])

    queries_bulleted = "\n".join(f"- {q}" for q in queries)

    # 1) Outline building: structured section plan
    sections: List[Dict[str, Any]] = build_outline(refined_topic, queries)
    sections_bulleted = "\n".join(
        f"{sec['priority']}. {sec['title']} — {sec['goal']}"
        for sec in sections
    )

    # 2) Research report
    report_messages = [
        {
            "role": "system",
            "content": (
                "You are a meticulous research assistant.\n"
                "Write a structured, neutral research report suitable for an informed reader.\n"
                "Use clear headings that correspond to the provided section plan.\n"
                "Avoid excessive hype, and keep opinion clearly separated from evidence."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Core topic:\n"
                f"{refined_topic}\n\n"
                f"Research sub-questions to address:\n"
                f"{queries_bulleted}\n\n"
                "Planned sections for the report (in order):\n"
                f"{sections_bulleted}\n\n"
                "Instructions:\n"
                "- Follow the section plan closely; each section of the report should map to one of these items.\n"
                "- Use clear headings matching the section titles (or very close variations).\n"
                "- Within each section, use paragraphs and bullet points where helpful.\n"
                "- Be explicit about uncertainties, limitations, and open questions where relevant.\n"
                "- At the end, add a final section titled 'Sources and References' that lists 5–10 concise notes\n"
                "  I could search for (e.g., paper titles, author + year, major reports or guidelines).\n"
            ),
        },
    ]

    report_raw: str = call_llm(
        report_messages,
        temperature=0.35,
        max_tokens=4000,
    )

    body_text, sources = _split_body_and_sources(report_raw)
    report_html = render_report_html(refined_topic, body_text, sources)
    save_html(session_id, "report", report_html)

    # 3) Op-ed
    oped_messages = [
        {
            "role": "system",
            "content": (
                "You are a thoughtful op-ed writer.\n"
                "Write a persuasive, opinionated article that builds on a prior neutral research report.\n"
                "Make your stance clear, but acknowledge uncertainties and opposing views."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Write an op-ed about the following topic:\n"
                f"{refined_topic}\n\n"
                "Context:\n"
                f"- The research report addressed these sub-questions:\n{queries_bulleted}\n\n"
                f"- The report was structured according to these sections:\n{sections_bulleted}\n\n"
                "Instructions for the op-ed:\n"
                "- Assume the reader has read the neutral research report.\n"
                "- Take a clear, defensible stance on the topic.\n"
                "- Refer to important debates, trade-offs, and uncertainties, but do not rehash the entire report.\n"
                "- Use a strong but reasonable voice, not clickbait.\n"
                "- End with a memorable closing paragraph that leaves the reader with a clear takeaway."
            ),
        },
    ]

    oped_text: str = call_llm(
        oped_messages,
        temperature=0.6,   # more opinionated / expressive
        max_tokens=2000,
    )
    oped_html = render_oped_html(refined_topic, oped_text)
    save_html(session_id, "oped", oped_html)

    # 4) Metadata
    meta: Dict[str, Any] = {
        "user_topic": user_topic,
        "refined_topic": refined_topic,
        "queries": queries,
        "sections": sections,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    if "raw" in refinement:
        meta["refiner_raw"] = refinement["raw"]
    if "error" in refinement:
        meta["refiner_error"] = refinement["error"]

    save_meta(session_id, meta)
