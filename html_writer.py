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

  .citation-link {
    color: #0a7cff;
    text-decoration: none;
    font-weight: normal;
    cursor: pointer;
    vertical-align: super;
    font-size: 0.75em;
    line-height: 0;
    position: relative;
    top: -0.4em;
    margin-left: 2px;
    padding: 0;
    display: inline-block;
  }

  .citation-link:hover {
    color: #0056b3;
    text-decoration: underline;
    background-color: #f0f7ff;
    border-radius: 2px;
    padding: 1px 2px;
    margin: -1px -2px;
  }

  .citation-sup {
    display: none; /* Hide the old citation-sup, we use citation-link for superscript */
  }

  footer.footer-note {
    margin-top: 2.5rem;
    font-size: 0.8rem;
    color: #999;
    line-height: 1.4;
  }

  /* Smooth scrolling for citation links */
  html {
    scroll-behavior: smooth;
  }

  /* Highlight reference when linked to */
  ol.references-list li:target {
    background-color: #f0f7ff;
    padding: 0.5rem;
    margin-left: -0.5rem;
    border-left: 3px solid #0a7cff;
    transition: background-color 0.3s ease;
  }
</style>
<script>
  // Add click handler for citation links to highlight the reference
  document.addEventListener('DOMContentLoaded', function() {
    const citationLinks = document.querySelectorAll('.citation-link');
    citationLinks.forEach(link => {
      link.addEventListener('click', function(e) {
        const refId = this.getAttribute('data-ref');
        const targetRef = document.getElementById('ref-' + refId);
        if (targetRef) {
          // Remove any existing highlight
          document.querySelectorAll('.references-list li').forEach(li => {
            li.style.backgroundColor = '';
          });
          // Highlight the target reference
          targetRef.style.backgroundColor = '#f0f7ff';
          setTimeout(() => {
            targetRef.style.backgroundColor = '';
          }, 2000);
        }
      });
    });
  });
</script>
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
    import re
    parts = []
    for sec in sections:
        sec_title = html.escape(sec["title"])
        body_raw = sec["body"]
        para_chunks = [p.strip() for p in body_raw.split("\n\n") if p.strip()]

        para_html_chunks = []
        for para in para_chunks:
            # First escape HTML to prevent XSS
            para_escaped = html.escape(para)
            
            # Pattern to match [1], [2], [12], etc. - find all citations
            citation_pattern = re.compile(r'\[(\d+)\]')
            
            # Find all citation positions in original text
            citations = list(citation_pattern.finditer(para_escaped))
            
            if not citations:
                # No citations, just output as-is
                para_html_chunks.append(f"<p>{para_escaped}</p>")
                continue
            
            # Wikipedia-style: Replace [1] with superscript clickable link right where it appears
            # Process from end to start to maintain positions
            result = para_escaped
            for match in reversed(citations):
                citation_id = match.group(1)
                start_pos = match.start()
                end_pos = match.end()
                
                # Replace [1] with superscript clickable link
                superscript_link = f'<a href="#ref-{citation_id}" class="citation-link" data-ref="{citation_id}">[{citation_id}]</a>'
                result = result[:start_pos] + superscript_link + result[end_pos:]
            
            para_html_chunks.append(f"<p>{result}</p>")

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
        ref_id = s.get("global_id", "")

        if url:
            link_html = f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>'
        else:
            link_html = ""

        refs.append(f"""
        <li id="ref-{ref_id}">
          <strong>[{ref_id}] {title}</strong><br/>
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
