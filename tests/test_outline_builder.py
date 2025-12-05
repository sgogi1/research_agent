"""Unit tests for outline_builder module."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from outline_builder import build_outline, _robust_json_parse
from llm_client import LLMError


class TestOutlineBuilder:
    """Test cases for outline builder functionality."""

    def test_robust_json_parse_valid(self):
        """Test parsing valid JSON."""
        json_str = '{"sections": [{"title": "Section 1", "goal": "Goal 1", "priority": 1}]}'
        result = _robust_json_parse(json_str)
        assert "sections" in result
        assert len(result["sections"]) == 1

    @patch('outline_builder.call_llm')
    def test_build_outline_success(self, mock_call_llm):
        """Test successful outline building."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 1", "goal": "Goal 1", "priority": 1},
                {"title": "Section 2", "goal": "Goal 2", "priority": 2},
                {"title": "Section 3", "goal": "Goal 3", "priority": 3}
            ]
        }'''

        result = build_outline("Test Topic", ["query1", "query2"])

        assert len(result) == 3
        assert result[0]["title"] == "Section 1"
        assert result[0]["priority"] == 1
        assert all(sec["priority"] == i + 1 for i, sec in enumerate(result))

    @patch('outline_builder.call_llm')
    def test_build_outline_sorts_by_priority(self, mock_call_llm):
        """Test that sections are sorted by priority."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 3", "goal": "Goal 3", "priority": 3},
                {"title": "Section 1", "goal": "Goal 1", "priority": 1},
                {"title": "Section 2", "goal": "Goal 2", "priority": 2}
            ]
        }'''

        result = build_outline("Topic", [])

        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 3

    @patch('outline_builder.call_llm')
    def test_build_outline_normalizes_priorities(self, mock_call_llm):
        """Test that priorities are normalized to 1..N."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 1", "goal": "Goal 1", "priority": 5},
                {"title": "Section 2", "goal": "Goal 2", "priority": 10},
                {"title": "Section 3", "goal": "Goal 3", "priority": 15}
            ]
        }'''

        result = build_outline("Topic", [])

        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2
        assert result[2]["priority"] == 3

    @patch('outline_builder.call_llm')
    def test_build_outline_limits_to_7_sections(self, mock_call_llm):
        """Test that outline is limited to 7 sections."""
        sections = [{"title": f"Section {i}", "goal": f"Goal {i}", "priority": i} for i in range(1, 11)]
        mock_call_llm.return_value = f'{{"sections": {sections}}}'

        result = build_outline("Topic", [])

        assert len(result) == 7

    @patch('outline_builder.call_llm')
    def test_build_outline_minimum_3_sections(self, mock_call_llm):
        """Test that fallback ensures minimum 3 sections."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 1", "goal": "Goal 1", "priority": 1}
            ]
        }'''

        result = build_outline("Topic", [])

        assert len(result) >= 3

    @patch('outline_builder.call_llm')
    def test_build_outline_fallback_on_error(self, mock_call_llm):
        """Test fallback outline when LLM call fails."""
        mock_call_llm.side_effect = LLMError("API error")

        result = build_outline("Test Topic", [])

        assert len(result) == 3
        assert all("title" in sec and "goal" in sec and "priority" in sec for sec in result)
        assert result[0]["priority"] == 1

    @patch('outline_builder.call_llm')
    def test_build_outline_filters_invalid_sections(self, mock_call_llm):
        """Test that invalid sections are filtered out."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Valid Section", "goal": "Goal", "priority": 1},
                {"title": "", "goal": "Goal", "priority": 2},
                {"invalid": "section"},
                {"title": "Another Valid", "goal": "Goal", "priority": 3}
            ]
        }'''

        result = build_outline("Topic", [])

        assert len(result) >= 2
        assert all(sec["title"] for sec in result)

    @patch('outline_builder.call_llm')
    def test_build_outline_default_goal(self, mock_call_llm):
        """Test that default goal is provided when missing."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 1", "priority": 1}
            ]
        }'''

        result = build_outline("Test Topic", [])

        assert result[0]["goal"] is not None
        assert len(result[0]["goal"]) > 0

    def test_build_outline_empty_topic(self):
        """Test that empty topic raises ValueError."""
        with pytest.raises(ValueError, match="Empty topic"):
            build_outline("", [])

    @patch('outline_builder.call_llm')
    def test_build_outline_handles_missing_priority(self, mock_call_llm):
        """Test that missing priority uses index."""
        mock_call_llm.return_value = '''{
            "sections": [
                {"title": "Section 1", "goal": "Goal 1"},
                {"title": "Section 2", "goal": "Goal 2"}
            ]
        }'''

        result = build_outline("Topic", [])

        assert result[0]["priority"] == 1
        assert result[1]["priority"] == 2

    @patch('outline_builder.call_llm')
    def test_build_outline_invalid_json_fallback(self, mock_call_llm):
        """Test fallback when LLM returns invalid JSON."""
        mock_call_llm.return_value = "Not JSON at all"

        result = build_outline("Topic", [])

        assert len(result) == 3  # Fallback outline

