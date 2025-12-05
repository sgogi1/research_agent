"""Unit tests for pipeline module."""
import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import (
    generate_full_report,
    _generate_research_report,
    _source_key,
    HISTORY_DIR
)


class TestPipeline:
    """Test cases for pipeline functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary history directory for tests
        self.test_history_dir = Path(tempfile.mkdtemp())
        # Patch HISTORY_DIR to use test directory
        self.history_patcher = patch('pipeline.HISTORY_DIR', self.test_history_dir)
        self.history_patcher.start()
        self.test_history_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.history_patcher.stop()
        if self.test_history_dir.exists():
            shutil.rmtree(self.test_history_dir)

    def test_source_key(self):
        """Test source key generation."""
        src1 = {"title": "Test", "url": "https://example.com"}
        src2 = {"title": "test", "url": "HTTPS://EXAMPLE.COM"}
        src3 = {"title": "Different", "url": "https://example.com"}

        key1 = _source_key(src1)
        key2 = _source_key(src2)
        key3 = _source_key(src3)

        assert key1 == key2  # Case insensitive
        assert key1 != key3  # Different titles

    def test_source_key_empty(self):
        """Test source key with empty values."""
        src = {"title": "", "url": ""}
        key = _source_key(src)
        assert key == ("", "")

    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    @patch('html_writer.save_html')
    def test_generate_research_report_success(self, mock_html, mock_research, mock_outline, mock_refine):
        """Test successful research report generation."""
        # Setup mocks
        mock_refine.return_value = {
            "topic": "Refined Topic",
            "queries": ["query1", "query2"]
        }

        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1},
            {"title": "Section 2", "goal": "Goal 2", "priority": 2}
        ]

        mock_research.side_effect = [
            {
                "body": "Content [1]",
                "sources": [{"id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"}]
            },
            {
                "body": "Content [1]",
                "sources": [{"id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"}]
            }
        ]

        run_id = "test123"

        result = _generate_research_report("User Topic", run_id)

        assert result["id"] == run_id
        assert "html_path" in result
        assert "meta_path" in result
        assert mock_refine.called
        assert mock_outline.called
        assert mock_research.call_count == 2
        assert mock_html.called

    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    @patch('html_writer.save_html')
    def test_generate_research_report_source_deduplication(self, mock_html, mock_research, mock_outline, mock_refine):
        """Test that sources are deduplicated across sections."""
        mock_refine.return_value = {"topic": "Topic", "queries": ["q1"]}
        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1},
            {"title": "Section 2", "goal": "Goal 2", "priority": 2}
        ]

        # Same source in both sections
        source = {"id": 1, "title": "Same Source", "url": "https://example.com", "source_type": "study", "why_relevant": "R"}
        mock_research.side_effect = [
            {"body": "Content [1]", "sources": [source]},
            {"body": "Content [1]", "sources": [source]}
        ]

        run_id = "test123"
        result = _generate_research_report("Topic", run_id)

        # Check that HTML was called with deduplicated sources
        call_args = mock_html.call_args
        sources = call_args[1]['sources']
        assert len(sources) == 1  # Should be deduplicated
        assert sources[0]["global_id"] == 1

    @patch('pipeline.refine_topic_to_queries')
    @patch('pipeline.build_outline')
    @patch('pipeline.research_section')
    @patch('html_writer.save_html')
    def test_generate_research_report_citation_normalization(self, mock_html, mock_research, mock_outline, mock_refine):
        """Test that citations are normalized to global IDs."""
        mock_refine.return_value = {"topic": "Topic", "queries": ["q1"]}
        mock_outline.return_value = [
            {"title": "Section 1", "goal": "Goal 1", "priority": 1}
        ]

        source1 = {"id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"}
        source2 = {"id": 1, "title": "Source 2", "url": "https://2.com", "source_type": "study", "why_relevant": "R2"}

        mock_research.return_value = {
            "body": "Content [1] and [1]",
            "sources": [source1, source2]
        }

        run_id = "test123"
        result = _generate_research_report("Topic", run_id)

        # Check that citations were normalized
        call_args = mock_html.call_args
        sections = call_args[1]['sections']
        # Both sources should have different global IDs
        assert len(call_args[1]['sources']) == 2

    def test_generate_research_report_empty_topic(self):
        """Test that empty topic raises ValueError."""
        with pytest.raises(ValueError, match="Topic is empty"):
            _generate_research_report("", "test123")

    @patch('pipeline._generate_research_report')
    def test_generate_full_report_research(self, mock_research):
        """Test generate_full_report generates research report."""
        mock_research.return_value = {"id": "test123", "topic": "Topic", "html_path": "path", "meta_path": "meta"}

        result = generate_full_report("Topic", "test123", "research")

        assert result["id"] == "test123"
        mock_research.assert_called_once_with("Topic", "test123", report_type="research")

    @patch('pipeline._generate_research_report')
    def test_generate_full_report_defaults_to_research(self, mock_research):
        """Test that invalid report_type defaults to research."""
        mock_research.return_value = {"id": "test123", "topic": "Topic", "html_path": "path", "meta_path": "meta"}

        generate_full_report("Topic", "test123", "invalid")

        mock_research.assert_called_once_with("Topic", "test123", report_type="research")

    @patch('pipeline._generate_research_report')
    def test_generate_full_report_metadata_saved(self, mock_research):
        """Test that metadata is saved correctly."""
        mock_research.return_value = {"id": "test123", "topic": "Topic", "html_path": "path", "meta_path": "meta"}

        generate_full_report("Topic", "test123", "research")

        meta_path = self.test_history_dir / "test123.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            assert meta["id"] == "test123"
            assert meta["report_type"] == "research"

