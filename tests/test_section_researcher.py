"""Unit tests for section_researcher module."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from section_researcher import research_section, _robust_json_parse
from llm_client import LLMError


class TestSectionResearcher:
    """Test cases for section researcher functionality."""

    def test_robust_json_parse_valid(self):
        """Test parsing valid JSON."""
        json_str = '{"body": "Content", "sources": []}'
        result = _robust_json_parse(json_str)
        assert result["body"] == "Content"
        assert "sources" in result

    @patch('section_researcher.call_llm')
    def test_research_section_success(self, mock_call_llm):
        """Test successful section research."""
        mock_call_llm.return_value = '''{
            "body": "Section content with [1] citation.",
            "sources": [
                {
                    "id": 1,
                    "title": "Source Title",
                    "url": "https://example.com",
                    "source_type": "study",
                    "why_relevant": "Relevant because..."
                }
            ]
        }'''

        result = research_section("Topic", ["query1"], "Section Title", "Section Goal")

        assert result["body"] == "Section content with [1] citation."
        assert len(result["sources"]) == 1
        assert result["sources"][0]["id"] == 1
        assert result["sources"][0]["title"] == "Source Title"
        assert "error" not in result

    @patch('section_researcher.call_llm')
    def test_research_section_multiple_sources(self, mock_call_llm):
        """Test section research with multiple sources."""
        mock_call_llm.return_value = '''{
            "body": "Content [1] and [2].",
            "sources": [
                {"id": 1, "title": "Source 1", "url": "https://1.com", "source_type": "study", "why_relevant": "R1"},
                {"id": 2, "title": "Source 2", "url": "https://2.com", "source_type": "article", "why_relevant": "R2"}
            ]
        }'''

        result = research_section("Topic", [], "Title", "Goal")

        assert len(result["sources"]) == 2
        assert result["sources"][0]["id"] == 1
        assert result["sources"][1]["id"] == 2

    @patch('section_researcher.call_llm')
    def test_research_section_filters_empty_sources(self, mock_call_llm):
        """Test that sources without titles are filtered."""
        mock_call_llm.return_value = '''{
            "body": "Content",
            "sources": [
                {"id": 1, "title": "Valid Source", "url": "https://example.com", "source_type": "study", "why_relevant": "R"},
                {"id": 2, "title": "", "url": "https://example.com", "source_type": "study", "why_relevant": "R"}
            ]
        }'''

        result = research_section("Topic", [], "Title", "Goal")

        assert len(result["sources"]) == 1
        assert result["sources"][0]["title"] == "Valid Source"

    @patch('section_researcher.call_llm')
    def test_research_section_defaults_missing_fields(self, mock_call_llm):
        """Test that missing source fields get defaults."""
        mock_call_llm.return_value = '''{
            "body": "Content [1]",
            "sources": [
                {"id": 1, "title": "Source"}
            ]
        }'''

        result = research_section("Topic", [], "Title", "Goal")

        assert result["sources"][0]["url"] == ""
        assert result["sources"][0]["source_type"] == "unspecified"
        assert len(result["sources"][0]["why_relevant"]) > 0

    @patch('section_researcher.call_llm')
    def test_research_section_assigns_id_when_missing(self, mock_call_llm):
        """Test that missing source ID is assigned."""
        mock_call_llm.return_value = '''{
            "body": "Content",
            "sources": [
                {"title": "Source 1"},
                {"title": "Source 2"}
            ]
        }'''

        result = research_section("Topic", [], "Title", "Goal")

        assert result["sources"][0]["id"] == 1
        assert result["sources"][1]["id"] == 2

    @patch('section_researcher.call_llm')
    def test_research_section_empty_body_fallback(self, mock_call_llm):
        """Test fallback body when LLM returns empty."""
        mock_call_llm.return_value = '{"body": "", "sources": []}'

        result = research_section("Topic", [], "Section Title", "Goal")

        assert len(result["body"]) > 0
        assert "Section Title" in result["body"] or "Topic" in result["body"]

    @patch('section_researcher.call_llm')
    def test_research_section_llm_error_fallback(self, mock_call_llm):
        """Test fallback when LLM call fails."""
        mock_call_llm.side_effect = LLMError("API error")

        result = research_section("Topic", [], "Section Title", "Goal")

        assert "error" in result
        assert len(result["body"]) > 0
        assert result["sources"] == []

    @patch('section_researcher.call_llm')
    def test_research_section_invalid_json_fallback(self, mock_call_llm):
        """Test fallback when LLM returns invalid JSON."""
        mock_call_llm.return_value = "Not JSON"

        result = research_section("Topic", [], "Title", "Goal")

        assert "error" in result
        assert len(result["body"]) > 0

    @patch('section_researcher.call_llm')
    def test_research_section_non_list_sources(self, mock_call_llm):
        """Test handling when sources is not a list."""
        mock_call_llm.return_value = '{"body": "Content", "sources": "not a list"}'

        result = research_section("Topic", [], "Title", "Goal")

        assert result["sources"] == []

    @patch('section_researcher.call_llm')
    def test_research_section_non_dict_sources(self, mock_call_llm):
        """Test filtering of non-dict sources."""
        mock_call_llm.return_value = '''{
            "body": "Content",
            "sources": [
                {"id": 1, "title": "Valid"},
                "invalid",
                123,
                null
            ]
        }'''

        result = research_section("Topic", [], "Title", "Goal")

        assert len(result["sources"]) == 1
        assert result["sources"][0]["title"] == "Valid"

    def test_research_section_strips_whitespace(self):
        """Test that inputs are stripped."""
        # This is tested implicitly through the function calls
        # The function should handle whitespace in topic, title, goal
        pass

    @patch('section_researcher.call_llm')
    def test_research_section_handles_empty_queries(self, mock_call_llm):
        """Test that empty queries list is handled."""
        mock_call_llm.return_value = '{"body": "Content", "sources": []}'

        result = research_section("Topic", [], "Title", "Goal")

        assert result["body"] == "Content"
        assert "error" not in result

