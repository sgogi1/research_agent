"""Unit tests for Flask app."""
import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, load_history_items, HISTORY_DIR


class TestApp:
    """Test cases for Flask application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        # Create temporary history directory
        self.test_history_dir = Path(tempfile.mkdtemp())
        self.history_patcher = patch('app.HISTORY_DIR', self.test_history_dir)
        self.history_patcher.start()
        self.test_history_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.history_patcher.stop()
        if self.test_history_dir.exists():
            shutil.rmtree(self.test_history_dir)

    def test_index_route(self):
        """Test home page route."""
        response = self.app.get('/')
        assert response.status_code == 200
        assert b'AI Research Agent' in response.data

    def test_index_route_with_history(self):
        """Test home page with history items."""
        # Create a mock history item
        meta = {
            "id": "test123",
            "user_topic": "Test Topic",
            "refined_topic": "Refined Topic",
            "report_type": "research",
            "created_at": "2024-01-01T00:00:00Z"
        }
        meta_path = self.test_history_dir / "test123.json"
        meta_path.write_text(json.dumps(meta), encoding='utf-8')

        response = self.app.get('/')
        assert response.status_code == 200
        assert b'Test Topic' in response.data or b'Refined Topic' in response.data

    def test_generate_route_missing_topic(self):
        """Test generate route with missing topic."""
        response = self.app.post('/generate',
                                data=json.dumps({}),
                                content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_generate_route_empty_topic(self):
        """Test generate route with empty topic."""
        response = self.app.post('/generate',
                                data=json.dumps({"topic": "   "}),
                                content_type='application/json')
        assert response.status_code == 400

    @patch('app.generate_full_report')
    def test_generate_route_success(self, mock_generate):
        """Test successful report generation."""
        mock_generate.return_value = {
            "id": "test123",
            "topic": "Topic",
            "html_path": "path",
            "meta_path": "meta"
        }

        response = self.app.post('/generate',
                                data=json.dumps({
                                    "topic": "Test Topic",
                                    "report_type": "research"
                                }),
                                content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == "test123"
        assert "report_url" in data
        assert mock_generate.called


    @patch('app.generate_full_report')
    def test_generate_route_error(self, mock_generate):
        """Test generate route with generation error."""
        mock_generate.side_effect = Exception("Generation failed")

        response = self.app.post('/generate',
                                data=json.dumps({
                                    "topic": "Test Topic",
                                    "report_type": "research"
                                }),
                                content_type='application/json')

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data

    def test_view_report_route_not_found(self):
        """Test view report route with non-existent report."""
        response = self.app.get('/report/nonexistent')
        assert response.status_code == 404

    def test_view_report_route_success(self):
        """Test viewing an existing report."""
        run_id = "test123"
        html_path = self.test_history_dir / f"{run_id}.html"
        meta_path = self.test_history_dir / f"{run_id}.json"

        html_path.write_text("<html>Test Report</html>", encoding='utf-8')
        meta_path.write_text(json.dumps({"id": run_id}), encoding='utf-8')

        response = self.app.get(f'/report/{run_id}')
        assert response.status_code == 200
        assert b'Test Report' in response.data

    def test_view_report_route_missing_html(self):
        """Test view report when HTML is missing."""
        run_id = "test123"
        meta_path = self.test_history_dir / f"{run_id}.json"
        meta_path.write_text(json.dumps({"id": run_id}), encoding='utf-8')

        response = self.app.get(f'/report/{run_id}')
        assert response.status_code == 404

    def test_load_history_items(self):
        """Test loading history items."""
        # Create multiple history items
        for i in range(3):
            meta = {
                "id": f"test{i}",
                "user_topic": f"Topic {i}",
                "refined_topic": f"Refined {i}",
                "report_type": "research",
                "created_at": f"2024-01-0{i+1}T00:00:00Z"
            }
            meta_path = self.test_history_dir / f"test{i}.json"
            meta_path.write_text(json.dumps(meta), encoding='utf-8')

        items = load_history_items()
        assert len(items) == 3
        # Should be sorted by created_at descending
        assert items[0]["id"] == "test2"

    def test_load_history_items_invalid_json(self):
        """Test loading history with invalid JSON."""
        invalid_path = self.test_history_dir / "invalid.json"
        invalid_path.write_text("not json", encoding='utf-8')

        items = load_history_items()
        # Should skip invalid JSON
        assert isinstance(items, list)

    def test_load_history_items_empty(self):
        """Test loading history when empty."""
        items = load_history_items()
        assert items == []

    def test_generate_route_always_uses_research(self):
        """Test that report_type is always research."""
        with patch('app.generate_full_report') as mock_generate:
            mock_generate.return_value = {
                "id": "test123",
                "topic": "Topic",
                "html_path": "path",
                "meta_path": "meta"
            }

            response = self.app.post('/generate',
                                    data=json.dumps({"topic": "Test Topic"}),
                                    content_type='application/json')

            assert response.status_code == 200
            call_args = mock_generate.call_args
            assert call_args[0][2] == "research"  # Always research

