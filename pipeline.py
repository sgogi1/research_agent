from datetime import datetime
from pathlib import Path
import json
import re
from typing import Dict, Any, List, Tuple

from llm_client import call_llm
from query_refiner import refine_topic_to_queries
from outline_builder import build_outline
from section_researcher import research_section
from html_writer import save_html as write_pretty_html


BASE_DIR = Path(__file__).resolve().parent
HISTORY_DIR = BASE_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)


def _source_key(src: Dict[str, Any]) -> Tuple[str, str]:
    title = (src.get("title") or "").strip().lower()
    url = (src.get("url") or "").strip().lower()
    return (title, url)


def generate_full_report(user_topic: str, run_id: str, report_type: str = "research") -> Dict[str, Any]:
    """
    Entry point called from app.py.
    Generates research reports.
    """
    return _generate_research_report(user_topic, run_id, report_type="research")


def _generate_research_report(user_topic: str, run_id: str, report_type: str = "research") -> Dict[str, Any]:
    user_topic = (user_topic or "").strip()
    if not user_topic:
        raise ValueError("Topic is empty")

    # 0) Refinement
    refinement = refine_topic_to_queries(user_topic, n_queries=10)
    refined_topic = refinement["topic"]
    queries = refinement["queries"]

    # 1) Outline
    outline_sections = build_outline(refined_topic, queries)

    # 2) Research each section
    section_blocks: List[Dict[str, Any]] = []
    for sec in outline_sections:
        sec_title = sec["title"]
        sec_goal = sec["goal"]
        result = research_section(refined_topic, queries, sec_title, sec_goal)
        section_blocks.append(
            {
                "title": sec_title,
                "goal": sec_goal,
                "body": result["body"],
                "sources": result.get("sources", []),
            }
        )

    # 3) Build global_sources (dedup) and normalized bodies
    global_sources: List[Dict[str, Any]] = []
    source_key_to_global_id: Dict[Tuple[str, str], int] = {}

    for block in section_blocks:
        for src in block["sources"]:
            key = _source_key(src)
            if not key[0] and not key[1]:
                continue
            if key in source_key_to_global_id:
                continue
            global_id = len(global_sources) + 1
            source_key_to_global_id[key] = global_id
            global_sources.append(
                {
                    "global_id": global_id,
                    "title": src.get("title", "Untitled source"),
                    "url": (src.get("url") or "").strip(),
                    "source_type": src.get("source_type", "unspecified"),
                    "why_relevant": src.get("why_relevant", ""),
                }
            )

    citation_pattern = re.compile(r"\[(\d+)\]")

    global_sections: List[Dict[str, str]] = []

    for block in section_blocks:
        body = block["body"]

        def _replace(match):
            local_id_str = match.group(1)
            try:
                local_id = int(local_id_str)
            except ValueError:
                return match.group(0)

            src = next(
                (s for s in block["sources"] if int(s.get("id", -1)) == local_id),
                None,
            )
            if not src:
                return match.group(0)

            key = _source_key(src)
            global_id = source_key_to_global_id.get(key)
            if not global_id:
                return match.group(0)

            return f"[{global_id}]"

        normalized_body = citation_pattern.sub(_replace, body)

        global_sections.append(
            {
                "title": block["title"],
                "body": normalized_body,
            }
        )

    # 4) Write pretty HTML
    html_path = HISTORY_DIR / f"{run_id}.html"
    write_pretty_html(
        topic=refined_topic,
        sections=global_sections,
        sources=global_sources,
        output_path=str(html_path),
    )

    # 5) Write metadata JSON
    meta = {
        "id": run_id,
        "user_topic": user_topic,
        "refined_topic": refined_topic,
        "report_type": report_type,
        "queries": queries,
        "outline_sections": outline_sections,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "html_filename": f"{run_id}.html",
    }
    meta_path = HISTORY_DIR / f"{run_id}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "id": run_id,
        "topic": refined_topic,
        "html_path": str(html_path),
        "meta_path": str(meta_path),
    }


