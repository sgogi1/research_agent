"""Unit tests for query_refiner module."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from query_refiner import refine_topic_to_queries, _robust_json_parse
from llm_client import LLMError


class TestQueryRefiner:
    """Test cases for query refiner functionality."""

    def test_robust_json_parse_valid_json(self):
        """Test parsing valid JSON."""
        json_str = '{"topic": "Test", "queries": ["q1", "q2"]}'
        result = _robust_json_parse(json_str)
        assert result["topic"] == "Test"
        assert result["queries"] == ["q1", "q2"]

    def test_robust_json_parse_with_extra_text(self):
        """Test parsing JSON with extra text around it."""
        json_str = 'Some text {"topic": "Test", "queries": ["q1"]} more text'
        result = _robust_json_parse(json_str)
        assert result["topic"] == "Test"
        assert result["queries"] == ["q1"]

    def test_robust_json_parse_no_json(self):
        """Test parsing string with no JSON."""
        with pytest.raises(ValueError, match="No JSON object found"):
            _robust_json_parse("No JSON here")

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_success(self, mock_call_llm):
        """Test successful topic refinement."""
        mock_call_llm.return_value = '{"topic": "Refined Topic", "queries": ["query1", "query2", "query3"]}'

        result = refine_topic_to_queries("Original topic", n_queries=5)

        assert result["topic"] == "Refined Topic"
        assert len(result["queries"]) == 3
        assert "query1" in result["queries"]
        assert "error" not in result

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_deduplication(self, mock_call_llm):
        """Test that duplicate queries are removed."""
        mock_call_llm.return_value = '{"topic": "Topic", "queries": ["q1", "q1", "q2", "q2", "q3"]}'

        result = refine_topic_to_queries("Topic", n_queries=10)

        assert len(result["queries"]) == 3
        assert result["queries"] == ["q1", "q2", "q3"]

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_limit(self, mock_call_llm):
        """Test that query count is limited to n_queries."""
        queries = [f"query{i}" for i in range(20)]
        mock_call_llm.return_value = f'{{"topic": "Topic", "queries": {queries}}}'

        result = refine_topic_to_queries("Topic", n_queries=10)

        assert len(result["queries"]) == 10

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_empty_queries(self, mock_call_llm):
        """Test fallback when no queries are returned."""
        mock_call_llm.return_value = '{"topic": "Topic", "queries": []}'

        result = refine_topic_to_queries("Original topic")

        assert result["queries"] == ["Original topic"]

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_llm_error(self, mock_call_llm):
        """Test error handling when LLM call fails."""
        mock_call_llm.side_effect = LLMError("API error")

        result = refine_topic_to_queries("Topic")

        assert result["topic"] == "Topic"
        assert result["queries"] == ["Topic"]
        assert "error" in result

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_invalid_json(self, mock_call_llm):
        """Test error handling when LLM returns invalid JSON."""
        mock_call_llm.return_value = "Not valid JSON at all"

        result = refine_topic_to_queries("Topic")

        assert result["topic"] == "Topic"
        assert result["queries"] == ["Topic"]
        assert "error" in result

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_non_list_queries(self, mock_call_llm):
        """Test handling when queries is not a list."""
        mock_call_llm.return_value = '{"topic": "Topic", "queries": "single query"}'

        result = refine_topic_to_queries("Topic")

        assert len(result["queries"]) == 1
        assert result["queries"][0] == "single query"

    def test_refine_topic_to_queries_empty_topic(self):
        """Test that empty topic raises ValueError."""
        with pytest.raises(ValueError, match="Empty topic"):
            refine_topic_to_queries("")

    def test_refine_topic_to_queries_whitespace_topic(self):
        """Test that whitespace-only topic raises ValueError."""
        with pytest.raises(ValueError):
            refine_topic_to_queries("   ")

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_strips_whitespace(self, mock_call_llm):
        """Test that queries are stripped of whitespace."""
        mock_call_llm.return_value = '{"topic": "Topic", "queries": ["  q1  ", " q2 ", "q3"]}'

        result = refine_topic_to_queries("Topic")

        assert result["queries"] == ["q1", "q2", "q3"]

    @patch('query_refiner.call_llm')
    def test_refine_topic_to_queries_filters_empty(self, mock_call_llm):
        """Test that empty queries are filtered out."""
        mock_call_llm.return_value = '{"topic": "Topic", "queries": ["q1", "", "  ", "q2"]}'

        result = refine_topic_to_queries("Topic")

        assert result["queries"] == ["q1", "q2"]

