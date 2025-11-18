from html import escape
from research_html import BASE_STYLE  # reuse same CSS


def render_oped_html(topic: str, oped_text: str) -> str:
    oped_html = oped_text.replace("\n", "<br/>\n")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Op-Ed – {escape(topic)}</title>
  <style>{BASE_STYLE}</style>
</head>
<body>
  <div class="main">
    <h1>Op-Ed</h1>
    <div class="meta">Topic: <strong>{escape(topic)}</strong></div>
    <div class="content">
      {oped_html}
    </div>
  </div>
</body>
</html>
"""
