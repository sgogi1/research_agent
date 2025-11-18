from datetime import datetime

from llm_client import call_llm, LLMError
from research_html import render_report_html
from oped_html import render_oped_html
from storage import save_html, save_meta
from query_refiner import refine_topic_to_queries


def generate_report_and_oped(user_topic: str, session_id: str) -> None:
    """
    High-level pipeline:
    - Use Query Refiner to normalize topic and generate sub-queries.
    - Use LLM to generate a research-style report body + sources.
    - Use LLM to generate an opinionated op-ed.
    - Wrap both in HTML and save to storage/session.
    """

    # 0) Query refinement
    refinement = refine_topic_to_queries(user_topic, n_queries=10)
    refined_topic = refinement["topic"]
    queries = refinement["queries"]

    queries_bulleted = "\n".join(f"- {q}" for q in queries)

    # 1) Research report
    report_messages = [
        {
            "role": "system",
            "content": (
                "You are a meticulous research assistant.\n"
                "Write a structured, neutral research report suitable for an informed reader.\n"
                "Use clear headings, bullet points where helpful, and avoid excessive hype.\n"
                "Explicitly address the research sub-questions provided."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Core topic:\n"
                f"{refined_topic}\n\n"
                f"Research sub-questions to cover (treat these as angles to investigate):\n"
                f"{queries_bulleted}\n\n"
                "Instructions:\n"
                "- Organize the report into clear sections.\n"
                "- Cover background, current state, key debates, risks & limitations, and future directions.\n"
                "- Explicitly weave the sub-questions into the narrative; don't just list them.\n"
                "- At the end, list 5–10 concise source or reference notes I could search for "
                "(e.g., paper titles, author + year, notable reports).\n"
            ),
        },
    ]

    report_raw = call_llm(report_messages, temperature=0.35, max_tokens=4000)

    # Very simple hack: split off a 'Sources:' section if present
    sources = []
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

    report_html = render_report_html(refined_topic, body_text, sources)
    save_html(session_id, "report", report_html)

    # 2) Op-ed
    oped_messages = [
        {
            "role": "system",
            "content": (
                "You are a thoughtful op-ed writer.\n"
                "Write a persuasive, opinionated article that builds on the research "
                "but clearly marks opinion as opinion."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Write an op-ed about:\n{refined_topic}\n\n"
                "Context:\n"
                f"- The research report addressed the following sub-questions:\n{queries_bulleted}\n\n"
                "Instructions:\n"
                "- Assume the reader has read a neutral research report.\n"
                "- Take a clear stance, use a strong voice, and acknowledge uncertainties.\n"
                "- Reference the key debates and trade-offs implied by the sub-questions.\n"
                "- Finish with a memorable closing paragraph, not a generic summary."
            ),
        },
    ]
    oped_text = call_llm(oped_messages, temperature=0.6, max_tokens=2000)
    oped_html = render_oped_html(refined_topic, oped_text)
    save_html(session_id, "oped", oped_html)

    # 3) Meta
    meta = {
        "user_topic": user_topic,
        "refined_topic": refined_topic,
        "queries": queries,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    # Optionally also store the raw refiner output / error
    if "raw" in refinement:
        meta["refiner_raw"] = refinement["raw"]
    if "error" in refinement:
        meta["refiner_error"] = refinement["error"]

    save_meta(session_id, meta)
