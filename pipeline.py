from datetime import datetime

from llm_client import call_llm, LLMError
from research_html import render_report_html
from oped_html import render_oped_html
from storage import save_html, save_meta


def generate_report_and_oped(topic: str, session_id: str) -> None:
    """
    High-level pipeline:
    - Use LLM to generate a research-style report body + sources.
    - Use LLM to generate an opinionated op-ed.
    - Wrap both in HTML and save to storage/session.
    """
    # 1) Research report
    report_messages = [
        {
            "role": "system",
            "content": (
                "You are a meticulous research assistant. "
                "Write a structured, neutral research report suitable for an informed reader. "
                "Use clear headings, bullet points where helpful, and avoid excessive hype."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Topic: {topic}\n\n"
                "Write a detailed research report in sections. "
                "Include background, current state, key debates, risks & limitations, and potential future directions. "
                "At the end, list 5–10 concise source or reference notes I could search for (e.g., paper titles, author + year)."
            ),
        },
    ]
    report_raw = call_llm(report_messages)

    # Very simple hack: split off a 'Sources:' section if present
    sources = []
    body_text = report_raw
    lower = report_raw.lower()
    for marker in ["sources:", "references:", "reference list:"]:
        idx = lower.rfind(marker)
        if idx != -1:
            body_text = report_raw[:idx].strip()
            src_block = report_raw[idx + len(marker) :].strip()
            sources = [line.strip("-• ").strip() for line in src_block.splitlines() if line.strip()]
            break

    report_html = render_report_html(topic, body_text, sources)
    save_html(session_id, "report", report_html)

    # 2) Op-ed
    oped_messages = [
        {
            "role": "system",
            "content": (
                "You are a thoughtful op-ed writer. "
                "Write a persuasive, opinionated article that builds on the research but clearly marks opinion as opinion."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Write an op-ed about: {topic}\n\n"
                "Assume the reader has read a neutral research report. "
                "Take a clear stance, use a strong voice, and finish with a memorable closing paragraph."
            ),
        },
    ]
    oped_text = call_llm(oped_messages)
    oped_html = render_oped_html(topic, oped_text)
    save_html(session_id, "oped", oped_html)

    # Meta
    meta = {
        "topic": topic,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    save_meta(session_id, meta)
