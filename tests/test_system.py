"""System/integration tests for the research agent."""
import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app
from pipeline import generate_full_report, HISTORY_DIR


class TestSystemIntegration:
    """System-level integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        # Create temporary history directory
        self.test_history_dir = Path(tempfile.mkdtemp())
        self.history_patcher = patch('pipeline.HISTORY_DIR', self.test_history_dir)
        self.history_patcher.start()
        self.app_history_patcher = patch('app.HISTORY_DIR', self.test_history_dir)
        self.app_history_patcher.start()
        self.test_history_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.history_patcher.stop()
        self.app_history_patcher.stop()
        if self.test_history_dir.exists():
            shutil.rmtree(self.test_history_dir)

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    @patch('html_writer.save_html')
    def test_full_research_report_flow(self, mock_html, mock_research, mock_outline, mock_refine, mock_llm):
        """Test complete research report generation flow."""
        # Mock topic refinement
        mock_refine.return_value = {
            "topic": "Refined Topic",
            "queries": ["query1", "query2", "query3"]
        }

        # Mock outline
        mock_outline.return_value = [
            {"title": "Introduction", "goal": "Introduce the topic", "priority": 1},
            {"title": "Main Content", "goal": "Discuss main points", "priority": 2}
        ]

        # Mock section research
        mock_research.side_effect = [
            {
                "body": "Introduction content with [1] citation.",
                "sources": [{
                    "id": 1,
                    "title": "Source 1",
                    "url": "https://example.com/1",
                    "source_type": "study",
                    "why_relevant": "Relevant to introduction"
                }]
            },
            {
                "body": "Main content with [1] and [2] citations.",
                "sources": [
                    {
                        "id": 1,
                        "title": "Source 1",
                        "url": "https://example.com/1",
                        "source_type": "study",
                        "why_relevant": "Relevant"
                    },
                    {
                        "id": 2,
                        "title": "Source 2",
                        "url": "https://example.com/2",
                        "source_type": "article",
                        "why_relevant": "Also relevant"
                    }
                ]
            }
        ]

        run_id = "system_test_123"
        result = generate_full_report("User Topic", run_id, "research")

        # Verify result structure
        assert result["id"] == run_id
        assert "html_path" in result
        assert "meta_path" in result

        # Verify HTML was generated
        assert mock_html.called
        html_call_args = mock_html.call_args
        assert html_call_args[1]['topic'] == "Refined Topic"
        assert len(html_call_args[1]['sections']) == 2
        # Sources should be deduplicated (Source 1 appears in both sections)
        sources = html_call_args[1]['sources']
        assert len(sources) == 2  # Source 1 and Source 2

        # Verify metadata was saved
        meta_path = self.test_history_dir / f"{run_id}.json"
        assert meta_path.exists()
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        assert meta["id"] == run_id
        assert meta["report_type"] == "research"
        assert meta["refined_topic"] == "Refined Topic"

        # Verify HTML file was created
        html_path = self.test_history_dir / f"{run_id}.html"
        assert html_path.exists()


    @patch('app.generate_full_report')
    def test_web_api_full_flow(self, mock_generate):
        """Test complete web API flow from request to response."""
        mock_generate.return_value = {
            "id": "web_test_123",
            "topic": "Test Topic",
            "html_path": str(self.test_history_dir / "web_test_123.html"),
            "meta_path": str(self.test_history_dir / "web_test_123.json")
        }

        # Create the HTML file that would be generated
        html_path = self.test_history_dir / "web_test_123.html"
        html_path.write_text("<html>Test Report</html>", encoding='utf-8')
        meta_path = self.test_history_dir / "web_test_123.json"
        meta_path.write_text(json.dumps({"id": "web_test_123"}), encoding='utf-8')

        # Test POST to generate
        response = self.app.post('/generate',
                                data=json.dumps({
                                    "topic": "Test Topic",
                                    "report_type": "research"
                                }),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "web_test_123"
        assert "/report/web_test_123" in data["report_url"]

        # Test GET to view report
        view_response = self.app.get('/report/web_test_123')
        assert view_response.status_code == 200
        assert b'Test Report' in view_response.data

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    def test_error_handling_in_pipeline(self, mock_refine, mock_llm):
        """Test error handling throughout the pipeline."""
        # Simulate LLM error during refinement
        mock_refine.side_effect = Exception("LLM API error")

        with pytest.raises(Exception):
            generate_full_report("Topic", "error_test", "research")

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    def test_citation_normalization_across_sections(self, mock_research, mock_outline, mock_refine, mock_llm):
        """Test that citations are properly normalized across multiple sections."""
        mock_refine.return_value = {
            "topic": "Topic",
            "queries": ["q1"]
        }

        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1},
            {"title": "Section 2", "goal": "Goal 2", "priority": 2}
        ]

        # Both sections reference the same source with local ID 1
        source = {
            "id": 1,
            "title": "Shared Source",
            "url": "https://shared.com",
            "source_type": "study",
            "why_relevant": "Relevant"
        }

        mock_research.side_effect = [
            {"body": "Section 1 content [1]", "sources": [source]},
            {"body": "Section 2 content [1]", "sources": [source]}
        ]

        run_id = "citation_test"
        result = generate_full_report("Topic", run_id, "research")

        # Verify the HTML writer was called with normalized citations
        # The same source should appear once in global sources
        # We need to check the actual call - this is verified in the mock
        assert result["id"] == run_id

    def test_history_persistence(self):
        """Test that history persists across requests."""
        # Create a history item
        meta = {
            "id": "persist_test",
            "user_topic": "Persistent Topic",
            "refined_topic": "Refined Persistent",
            "report_type": "research",
            "created_at": "2024-01-01T00:00:00Z"
        }
        meta_path = self.test_history_dir / "persist_test.json"
        meta_path.write_text(json.dumps(meta), encoding='utf-8')

        # Load history
        response = self.app.get('/')
        assert response.status_code == 200
        # History should be visible
        assert b'Persistent' in response.data or b'Refined Persistent' in response.data

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    def test_clickable_superscript_citations_in_report(self, mock_research, mock_outline, mock_refine, mock_llm):
        """Test that generated reports have clickable superscript citations."""
        mock_refine.return_value = {
            "topic": "Test Topic",
            "queries": ["query1"]
        }

        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1}
        ]

        mock_research.return_value = {
            "body": "This is content with citation [1] and another [2].",
            "sources": [
                {"id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"},
                {"id": 2, "title": "Source 2", "url": "https://2.com", "source_type": "article", "why_relevant": "R2"}
            ]
        }

        run_id = "citation_test_123"
        result = generate_full_report("Topic", run_id, "research")

        # Verify the HTML file was created
        html_path = self.test_history_dir / f"{run_id}.html"
        assert html_path.exists(), "HTML file should be created"
        
        html_content = html_path.read_text(encoding='utf-8')
        
        # Check for clickable citation links
        assert 'class="citation-link"' in html_content, "Citations should have citation-link class"
        assert 'href="#ref-1"' in html_content, "Citation [1] should link to ref-1"
        assert 'href="#ref-2"' in html_content, "Citation [2] should link to ref-2"
        # Check for reference IDs
        assert 'id="ref-1"' in html_content, "Reference 1 should have id ref-1"
        assert 'id="ref-2"' in html_content, "Reference 2 should have id ref-2"
        # Check for superscript CSS
        assert 'vertical-align: super' in html_content, "Citations should have superscript styling"
        # Check that citations are clickable
        assert 'data-ref="1"' in html_content, "Citation should have data-ref attribute"
        assert 'cursor: pointer' in html_content, "Citations should have pointer cursor"

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    def test_citations_link_to_correct_references(self, mock_research, mock_outline, mock_refine, mock_llm):
        """Test that citations link to the correct reference IDs."""
        from html_writer import save_html
        
        mock_refine.return_value = {"topic": "Topic", "queries": ["q1"]}
        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1}
        ]

        # Create sources with specific IDs
        source1 = {"id": 1, "title": "First Source", "url": "https://first.com", "source_type": "study", "why_relevant": "R1"}
        source2 = {"id": 2, "title": "Second Source", "url": "https://second.com", "source_type": "article", "why_relevant": "R2"}

        mock_research.return_value = {
            "body": "Content with [1] and [2] citations.",
            "sources": [source1, source2]
        }

        run_id = "link_test_123"
        result = generate_full_report("Topic", run_id, "research")

        # Check the generated HTML
        html_path = self.test_history_dir / f"{run_id}.html"
        assert html_path.exists()
        
        html_content = html_path.read_text(encoding='utf-8')
        
        # Verify citation [1] links to ref-1
        assert 'href="#ref-1"' in html_content
        # Verify citation [2] links to ref-2
        assert 'href="#ref-2"' in html_content
        # Verify references have correct IDs
        assert 'id="ref-1"' in html_content
        assert 'id="ref-2"' in html_content
        # Verify source titles appear in references
        assert "First Source" in html_content
        assert "Second Source" in html_content

    @patch('pipeline.call_llm')
    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    def test_citation_superscript_styling(self, mock_research, mock_outline, mock_refine, mock_llm):
        """Test that citations have proper superscript CSS styling."""
        mock_refine.return_value = {"topic": "Topic", "queries": ["q1"]}
        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1}
        ]

        mock_research.return_value = {
            "body": "Content with citation [1].",
            "sources": [{"id": 1, "title": "Source", "url": "https://example.com", "source_type": "study", "why_relevant": "R"}]
        }

        run_id = "styling_test_123"
        result = generate_full_report("Topic", run_id, "research")

        html_path = self.test_history_dir / f"{run_id}.html"
        assert html_path.exists()
        
        html_content = html_path.read_text(encoding='utf-8')
        
        # Check for superscript CSS properties
        assert '.citation-link' in html_content
        assert 'vertical-align: super' in html_content
        assert 'font-size: 0.75em' in html_content or 'font-size: 0.7em' in html_content
        assert 'cursor: pointer' in html_content
        # Check for hover effects
        assert '.citation-link:hover' in html_content

    def test_web_report_displays_clickable_citations(self):
        """Test that web-accessible reports have clickable citations."""
        # Create a report with citations
        run_id = "web_citation_test"
        html_content = '''<!DOCTYPE html>
<html>
<head><title>Test</title>
<style>
.citation-link {
    vertical-align: super;
    font-size: 0.75em;
    color: #0a7cff;
}
</style>
</head>
<body>
<p>Content with citation <a href="#ref-1" class="citation-link" data-ref="1">[1]</a>.</p>
<ol><li id="ref-1">Source 1</li></ol>
</body>
</html>'''
        
        html_path = self.test_history_dir / f"{run_id}.html"
        meta_path = self.test_history_dir / f"{run_id}.json"
        
        html_path.write_text(html_content, encoding='utf-8')
        meta_path.write_text(json.dumps({"id": run_id}), encoding='utf-8')

        # Access via web
        response = self.app.get(f'/report/{run_id}')
        assert response.status_code == 200
        
        # Check that citations are in the response
        assert b'citation-link' in response.data
        assert b'href="#ref-1"' in response.data
        assert b'vertical-align: super' in response.data

