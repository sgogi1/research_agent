import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "storage" / "sessions"


def ensure_session_dir(session_id: str) -> Path:
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def save_html(session_id: str, kind: str, html: str) -> None:
    """
    kind: 'report'
    """
    session_dir = ensure_session_dir(session_id)
    target = session_dir / f"{kind}.html"
    target.write_text(html, encoding="utf-8")


def load_html(session_id: str, kind: str) -> str | None:
    session_dir = SESSIONS_DIR / session_id
    target = session_dir / f"{kind}.html"
    if not target.exists():
        return None
    return target.read_text(encoding="utf-8")


def save_meta(session_id: str, meta: dict) -> None:
    session_dir = ensure_session_dir(session_id)
    target = session_dir / "meta.json"
    target.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_meta(session_id: str) -> dict | None:
    session_dir = SESSIONS_DIR / session_id
    target = session_dir / "meta.json"
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))
