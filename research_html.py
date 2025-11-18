from html import escape

BASE_STYLE = """
body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0;
    padding: 0;
    background: #0f172a;
    color: #e5e7eb;
}
.main {
    max-width: 900px;
    margin: 40px auto;
    padding: 32px;
    background: #020617;
    border-radius: 16px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.6);
}
h1, h2, h3 {
    color: #e5e7eb;
}
a {
    color: #38bdf8;
}
.meta {
    font-size: 0.85rem;
    color: #9ca3af;
    margin-bottom: 1.5rem;
}
hr {
    border: none;
    border-top: 1px solid #1f2937;
    margin: 2rem 0;
}
pre, code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    background: #020617;
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
}
"""

def render_report_html(topic: str, body_markdown: str, sources: list[str] | None = None) -> str:
    """
    body_markdown: markdown-ish text from LLM (we'll allow some HTML too)
    sources: optional list of strings
    """
    sources = sources or []
    sources_html = ""
    if sources:
        items = "".join(f"<li>{escape(s)}</li>" for s in sources)
        sources_html = f"""
        <hr />
        <h2>Sources &amp; References</h2>
        <ol>{items}</ol>
        """

    # We trust the LLM to mostly output HTML/markdown; keep it simple here.
    body_html = body_markdown.replace("\n", "<br/>\n")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Research Report – {escape(topic)}</title>
  <style>{BASE_STYLE}</style>
</head>
<body>
  <div class="main">
    <h1>Research Report</h1>
    <div class="meta">Topic: <strong>{escape(topic)}</strong></div>
    <div class="content">
      {body_html}
    </div>
    {sources_html}
  </div>
</body>
</html>
"""
