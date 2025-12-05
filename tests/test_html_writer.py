"""Unit tests for html_writer module."""
import pytest
import sys
import tempfile
import os
from pathlib import Path
import html

sys.path.insert(0, str(Path(__file__).parent.parent))

from html_writer import save_html, _render_sections, _render_references


class TestHTMLWriter:
    """Test cases for HTML writer functionality."""

    def test_render_sections_single_section(self):
        """Test rendering a single section."""
        sections = [{
            "title": "Test Section",
            "body": "This is paragraph one.\n\nThis is paragraph two."
        }]

        result = _render_sections(sections)

        assert "Test Section" in result
        assert "paragraph one" in result
        assert "paragraph two" in result
        assert "<h2>" in result
        assert "<p>" in result

    def test_render_sections_multiple_sections(self):
        """Test rendering multiple sections."""
        sections = [
            {"title": "Section 1", "body": "Content 1"},
            {"title": "Section 2", "body": "Content 2"}
        ]

        result = _render_sections(sections)

        assert "Section 1" in result
        assert "Section 2" in result
        assert result.count("<section") == 2

    def test_render_sections_html_escaping(self):
        """Test that HTML is properly escaped."""
        sections = [{
            "title": "Test <script>alert('xss')</script>",
            "body": "Content with <tags> & special chars"
        }]

        result = _render_sections(sections)

        assert "&lt;script&gt;" in result
        assert "&lt;tags&gt;" in result
        assert "&amp;" in result
        assert "<script>" not in result

    def test_render_sections_paragraph_splitting(self):
        """Test that paragraphs are split correctly."""
        sections = [{
            "title": "Section",
            "body": "Para 1\n\nPara 2\n\nPara 3"
        }]

        result = _render_sections(sections)

        assert result.count("<p>") == 3

    def test_render_sections_filters_empty_paragraphs(self):
        """Test that empty paragraphs are filtered."""
        sections = [{
            "title": "Section",
            "body": "Para 1\n\n\n\nPara 2"
        }]

        result = _render_sections(sections)

        assert result.count("<p>") == 2

    def test_render_references_single_source(self):
        """Test rendering a single reference."""
        sources = [{
            "global_id": 1,
            "title": "Test Source",
            "url": "https://example.com",
            "source_type": "study",
            "why_relevant": "Relevant because..."
        }]

        result = _render_references(sources)

        assert "[1]" in result
        assert "Test Source" in result
        assert "https://example.com" in result
        assert "study" in result
        assert "Relevant because" in result

    def test_render_references_multiple_sources(self):
        """Test rendering multiple references."""
        sources = [
            {"global_id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"},
            {"global_id": 2, "title": "Source 2", "url": "https://2.com", "source_type": "article", "why_relevant": "R2"}
        ]

        result = _render_references(sources)

        assert "[1]" in result
        assert "[2]" in result
        assert "Source 1" in result
        assert "Source 2" in result

    def test_render_references_no_url(self):
        """Test reference without URL."""
        sources = [{
            "global_id": 1,
            "title": "Source",
            "url": "",
            "source_type": "study",
            "why_relevant": "Relevant"
        }]

        result = _render_references(sources)

        assert "Source" in result
        assert "<a href" not in result

    def test_render_references_html_escaping(self):
        """Test that reference content is HTML escaped."""
        sources = [{
            "global_id": 1,
            "title": "Source <script>alert('xss')</script>",
            "url": "https://example.com?q=<test>",
            "source_type": "study & research",
            "why_relevant": "Relevant <tag>"
        }]

        result = _render_references(sources)

        assert "&lt;script&gt;" in result
        assert "&lt;test&gt;" in result
        assert "&amp;" in result

    def test_render_references_url_escaping(self):
        """Test that URLs are properly escaped in links."""
        sources = [{
            "global_id": 1,
            "title": "Source",
            "url": "https://example.com?q=test&param=value",
            "source_type": "study",
            "why_relevant": "Relevant"
        }]

        result = _render_references(sources)

        assert "href=" in result
        assert html.escape("https://example.com?q=test&param=value") in result

    def test_save_html_creates_file(self):
        """Test that save_html creates a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Test Topic",
                sections=[{"title": "Section", "body": "Content"}],
                sources=[{
                    "global_id": 1,
                    "title": "Source",
                    "url": "https://example.com",
                    "source_type": "study",
                    "why_relevant": "Relevant"
                }],
                output_path=temp_path
            )

            assert os.path.exists(temp_path)
            content = open(temp_path, 'r', encoding='utf-8').read()
            assert "Test Topic" in content
            assert "Section" in content
            assert "Source" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_html_complete_structure(self):
        """Test that saved HTML has complete structure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Test Topic",
                sections=[{"title": "Section", "body": "Content"}],
                sources=[],
                output_path=temp_path
            )

            content = open(temp_path, 'r', encoding='utf-8').read()
            assert "<!DOCTYPE html>" in content
            assert "<html" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "<main class=\"article\">" in content
            assert "<header" in content
            assert "<h1>" in content
            assert "<hr class=\"references-split\"/>" in content
            assert "<footer" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_html_returns_path(self):
        """Test that save_html returns the output path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            result = save_html(
                topic="Test",
                sections=[],
                sources=[],
                output_path=temp_path
            )

            assert result == temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_html_handles_empty_sections(self):
        """Test HTML generation with empty sections."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Topic",
                sections=[],
                sources=[],
                output_path=temp_path
            )

            content = open(temp_path, 'r', encoding='utf-8').read()
            assert "Topic" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_html_handles_empty_sources(self):
        """Test HTML generation with empty sources."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Topic",
                sections=[{"title": "Section", "body": "Content"}],
                sources=[],
                output_path=temp_path
            )

            content = open(temp_path, 'r', encoding='utf-8').read()
            assert "<ol class=\"references-list\">" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_render_sections_with_citations(self):
        """Test that citations are rendered as clickable links."""
        sections = [{
            "title": "Test Section",
            "body": "This is a test sentence with citation [1]. Another [2] citation here."
        }]

        result = _render_sections(sections)

        # Check that citations are converted to links
        assert 'class="citation-link"' in result
        assert 'href="#ref-1"' in result
        assert 'href="#ref-2"' in result
        assert 'data-ref="1"' in result
        assert 'data-ref="2"' in result
        # Check that citation numbers are in the links
        assert '<a href="#ref-1" class="citation-link" data-ref="1">[1]</a>' in result
        assert '<a href="#ref-2" class="citation-link" data-ref="2">[2]</a>' in result

    def test_render_sections_citations_are_inline(self):
        """Test that citations appear inline, not at the end."""
        sections = [{
            "title": "Test",
            "body": "The term woke [1] originates from AAVE [2] and has been used [1]."
        }]

        result = _render_sections(sections)

        # Citations should appear inline where they are in the text
        assert "woke" in result
        assert "AAVE" in result
        # Check that citations appear after the words, not at the end
        assert result.find("woke") < result.find('href="#ref-1"')
        assert result.find("AAVE") < result.find('href="#ref-2"')

    def test_render_sections_multiple_citations(self):
        """Test handling of multiple citations in one paragraph."""
        sections = [{
            "title": "Test",
            "body": "First [1] second [2] third [3] fourth [1]."
        }]

        result = _render_sections(sections)

        # All citations should be converted
        assert result.count('class="citation-link"') == 4
        assert 'href="#ref-1"' in result
        assert 'href="#ref-2"' in result
        assert 'href="#ref-3"' in result
        # Same citation can appear multiple times
        assert result.count('href="#ref-1"') == 2

    def test_render_sections_citation_css_class(self):
        """Test that citations have the correct CSS class for superscript styling."""
        sections = [{
            "title": "Test",
            "body": "Test citation [1]."
        }]

        result = _render_sections(sections)

        assert 'class="citation-link"' in result
        # The CSS should be in the style block (tested separately)

    def test_render_references_have_ids(self):
        """Test that references have IDs that citations can link to."""
        sources = [
            {"global_id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"},
            {"global_id": 2, "title": "Source 2", "url": "https://2.com", "source_type": "article", "why_relevant": "R2"}
        ]

        result = _render_references(sources)

        # References should have IDs matching citation links
        assert 'id="ref-1"' in result
        assert 'id="ref-2"' in result

    def test_save_html_citations_link_to_references(self):
        """Test that saved HTML has citations linking to references."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Test Topic",
                sections=[{
                    "title": "Section",
                    "body": "Content with citation [1] and another [2]."
                }],
                sources=[
                    {"global_id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"},
                    {"global_id": 2, "title": "Source 2", "url": "https://2.com", "source_type": "article", "why_relevant": "R2"}
                ],
                output_path=temp_path
            )

            content = open(temp_path, 'r', encoding='utf-8').read()
            # Check citations are clickable links
            assert 'href="#ref-1"' in content
            assert 'href="#ref-2"' in content
            assert 'class="citation-link"' in content
            # Check references have matching IDs
            assert 'id="ref-1"' in content
            assert 'id="ref-2"' in content
            # Check CSS for superscript styling
            assert 'vertical-align: super' in content
            assert 'font-size: 0.75em' in content or 'font-size: 0.7em' in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_html_citation_css_styling(self):
        """Test that citation CSS styling is included in HTML."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as f:
            temp_path = f.name

        try:
            save_html(
                topic="Test",
                sections=[{"title": "Section", "body": "Content [1]."}],
                sources=[{"global_id": 1, "title": "Source", "url": "", "source_type": "study", "why_relevant": "R"}],
                output_path=temp_path
            )

            content = open(temp_path, 'r', encoding='utf-8').read()
            # Check for citation CSS
            assert '.citation-link' in content
            assert 'vertical-align: super' in content
            assert 'cursor: pointer' in content
            assert 'color: #0a7cff' in content or 'color:#0a7cff' in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_render_sections_no_citations(self):
        """Test that text without citations is rendered normally."""
        sections = [{
            "title": "Test",
            "body": "This text has no citations at all."
        }]

        result = _render_sections(sections)

        assert "This text has no citations at all." in result
        assert 'citation-link' not in result
        assert '<a href="#ref-' not in result

    def test_render_sections_citations_preserve_text(self):
        """Test that citation conversion doesn't break the text."""
        sections = [{
            "title": "Test",
            "body": "The term woke [1] originates from African American Vernacular English [2]."
        }]

        result = _render_sections(sections)

        # Original text should be preserved (with HTML escaping)
        assert "The term woke" in result
        assert "originates from" in result
        assert "African American Vernacular English" in result
        # Citations should be converted to links
        assert 'href="#ref-1"' in result
        assert 'href="#ref-2"' in result

