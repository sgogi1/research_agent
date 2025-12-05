"""Unit tests for llm_client module."""
import os
import pytest
import requests
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_client import call_llm, LLMError, _check_api_key


class TestLLMClient:
    """Test cases for LLM client functionality."""

    def test_check_api_key_missing(self):
        """Test that missing API key raises LLMError."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('llm_client.OPENROUTER_API_KEY', None):
                with pytest.raises(LLMError, match="OPENROUTER_API_KEY is not set"):
                    _check_api_key()

    def test_check_api_key_present(self):
        """Test that present API key doesn't raise error."""
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'}):
            with patch('llm_client.OPENROUTER_API_KEY', 'test-key'):
                try:
                    _check_api_key()
                except LLMError:
                    pytest.fail("_check_api_key() raised LLMError unexpectedly")

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_success(self, mock_post):
        """Test successful LLM call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Test response"
                }
            }]
        }
        mock_post.return_value = mock_response

        result = call_llm([
            {"role": "user", "content": "Test prompt"}
        ])

        assert result == "Test response"
        assert mock_post.called
        call_args = mock_post.call_args
        assert call_args[1]['json']['messages'][0]['content'] == "Test prompt"

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_with_custom_params(self, mock_post):
        """Test LLM call with custom parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Response"
                }
            }]
        }
        mock_post.return_value = mock_response

        call_llm(
            [{"role": "system", "content": "System"}],
            model="custom-model",
            max_tokens=1000,
            temperature=0.5
        )

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "custom-model"
        assert payload['max_tokens'] == 1000
        assert payload['temperature'] == 0.5

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_http_error(self, mock_post):
        """Test LLM call with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="OpenRouter HTTP error"):
            call_llm([{"role": "user", "content": "Test"}])

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_invalid_response_format(self, mock_post):
        """Test LLM call with invalid response format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "structure"}
        mock_post.return_value = mock_response

        with pytest.raises(LLMError, match="Unexpected OpenRouter response format"):
            call_llm([{"role": "user", "content": "Test"}])

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_call_llm_retry_on_timeout(self, mock_sleep, mock_post):
        """Test that LLM call retries on timeout."""
        # First call times out, second succeeds
        mock_post.side_effect = [
            requests.Timeout("Connection timeout"),
            Mock(
                status_code=200,
                json=lambda: {
                    "choices": [{
                        "message": {"content": "Success after retry"}
                    }]
                }
            )
        ]

        result = call_llm([{"role": "user", "content": "Test"}], max_retries=2)

        assert result == "Success after retry"
        assert mock_post.call_count == 2
        assert mock_sleep.called

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    @patch('time.sleep')
    def test_call_llm_max_retries_exceeded(self, mock_sleep, mock_post):
        """Test that LLM call fails after max retries."""
        mock_post.side_effect = requests.Timeout("Connection timeout")

        with pytest.raises(LLMError, match="Network error"):
            call_llm([{"role": "user", "content": "Test"}], max_retries=2)

        assert mock_post.call_count == 3  # Initial + 2 retries

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_connection_error(self, mock_post):
        """Test LLM call with connection error."""
        mock_post.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(LLMError, match="Network error"):
            call_llm([{"role": "user", "content": "Test"}], max_retries=0)

    @patch('llm_client.requests.post')
    @patch('llm_client.OPENROUTER_API_KEY', 'test-key')
    def test_call_llm_headers(self, mock_post):
        """Test that correct headers are sent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Response"}
            }]
        }
        mock_post.return_value = mock_response

        call_llm([{"role": "user", "content": "Test"}])

        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer test-key'
        assert headers['Content-Type'] == 'application/json'
        assert 'HTTP-Referer' in headers
        assert 'X-Title' in headers

