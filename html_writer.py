import html
from typing import List, Dict

STYLE_BLOCK = """
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Segoe UI", Roboto, Arial, sans-serif;
    background-color: #fafafa;
    color: #1a1a1a;
    display: flex;
    justify-content: center;
    padding: 3rem 1rem 6rem;
    line-height: 1.6;
  }

  main.article {
    background: #fff;
    max-width: 720px;
    width: 100%;
    box-shadow: 0 30px 60px rgba(0,0,0,0.06);
    border-radius: 8px;
    padding: 3rem 2rem 4rem;
  }

  header.article-header h1 {
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.25;
    color: #000;
    margin: 0 0 0.5rem 0;
  }

  header.article-header .subtitle {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 2rem;
  }

  section.article-section {
    margin-bottom: 2rem;
  }

  section.article-section h2 {
    font-size: 1.25rem;
    font-weight: 600;
    line-height: 1.4;
    color: #000;
    margin: 0 0 0.75rem 0;
  }

  section.article-section p {
    font-size: 1rem;
    color: #1a1a1a;
    margin: 0 0 1rem 0;
    white-space: pre-wrap;
  }

  hr.references-split {
    border: none;
    border-top: 1px solid #e5e5e5;
    margin: 3rem 0 1.5rem 0;
  }

  h3.references-heading {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #666;
    letter-spacing: 0.05em;
    margin: 0 0 1rem 0;
  }

  ol.references-list {
    padding-left: 1.2rem;
    color: #444;
    font-size: 0.9rem;
    line-height: 1.5;
  }

  ol.references-list li {
    margin-bottom: 0.75rem;
    word-break: break-word;
  }

  ol.references-list a {
    color: #0a7cff;
    text-decoration: none;
  }

  ol.references-list a:hover {
    text-decoration: underline;
  }

  footer.footer-note {
    margin-top: 2.5rem;
    font-size: 0.8rem;
    color: #999;
    line-height: 1.4;
  }
</style>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
{style}
</head>
<body>
<main class="article">
  <header class="article-header">
    <h1>{title_escaped}</h1>
    <div class="subtitle">An automated research report with inline citations and sources.</div>
  </header>

  {sections_html}

  <hr class="references-split"/>
  <h3 class="references-heading">References</h3>
  <ol class="references-list">
    {references_html}
  </ol>

  <footer class="footer-note">
    This report was generated automatically by an AI research agent. Do not treat this as medical, legal, or financial advice. Always verify primary sources.
  </footer>
</main>
</body>
</html>
"""


def _render_sections(sections: List[Dict[str, str]]) -> str:
    parts = []
    for sec in sections:
        sec_title = html.escape(sec["title"])
        body_raw = sec["body"]
        para_chunks = [p.strip() for p in body_raw.split("\n\n") if p.strip()]

        para_html_chunks = []
        for para in para_chunks:
            para_html_chunks.append(f"<p>{html.escape(para)}</p>")

        section_block = f"""
        <section class="article-section">
          <h2>{sec_title}</h2>
          {''.join(para_html_chunks)}
        </section>
        """
        parts.append(section_block)
    return "\n".join(parts)


def _render_references(sources: List[Dict[str, str]]) -> str:
    refs = []
    for s in sources:
        title = html.escape(s.get("title", ""))
        url = s.get("url", "").strip()
        source_type = html.escape(s.get("source_type", ""))
        why = html.escape(s.get("why_relevant", ""))

        if url:
            link_html = f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>'
        else:
            link_html = ""

        refs.append(f"""
        <li>
          <strong>[{s['global_id']}] {title}</strong><br/>
          <em>{source_type}</em><br/>
          {why}<br/>
          {link_html}
        </li>
        """.strip())
    return "\n".join(refs)


def save_html(
    topic: str,
    sections: List[Dict[str, str]],
    sources: List[Dict[str, str]],
    output_path: str,
) -> str:

    sections_html = _render_sections(sections)
    references_html = _render_references(sources)

    final_html = HTML_TEMPLATE.format(
        title=html.escape(topic),
        title_escaped=html.escape(topic),
        style=STYLE_BLOCK,
        sections_html=sections_html,
        references_html=references_html,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    return output_path
