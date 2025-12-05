"""Unit tests for storage module."""
import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from storage import (
    ensure_session_dir,
    save_html,
    load_html,
    save_meta,
    load_meta,
    SESSIONS_DIR
)


class TestStorage:
    """Test cases for storage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary sessions directory
        self.test_sessions_dir = Path(tempfile.mkdtemp())
        self.sessions_patcher = patch('storage.SESSIONS_DIR', self.test_sessions_dir)
        self.sessions_patcher.start()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.sessions_patcher.stop()
        if self.test_sessions_dir.exists():
            shutil.rmtree(self.test_sessions_dir)

    def test_ensure_session_dir(self):
        """Test session directory creation."""
        session_id = "test123"
        session_dir = ensure_session_dir(session_id)

        assert session_dir.exists()
        assert session_dir.name == session_id
        assert session_dir.parent == self.test_sessions_dir

    def test_ensure_session_dir_existing(self):
        """Test that existing directory is not recreated."""
        session_id = "test123"
        session_dir1 = ensure_session_dir(session_id)
        session_dir2 = ensure_session_dir(session_id)

        assert session_dir1 == session_dir2

    def test_save_html(self):
        """Test saving HTML."""
        session_id = "test123"
        html_content = "<html><body>Test</body></html>"

        save_html(session_id, "report", html_content)

        html_path = self.test_sessions_dir / session_id / "report.html"
        assert html_path.exists()
        assert html_path.read_text(encoding='utf-8') == html_content


    def test_load_html_existing(self):
        """Test loading existing HTML."""
        session_id = "test123"
        html_content = "<html><body>Test</body></html>"

        save_html(session_id, "report", html_content)
        loaded = load_html(session_id, "report")

        assert loaded == html_content

    def test_load_html_nonexistent(self):
        """Test loading non-existent HTML."""
        loaded = load_html("nonexistent", "report")
        assert loaded is None

    def test_load_html_wrong_kind(self):
        """Test loading HTML with wrong kind."""
        session_id = "test123"
        save_html(session_id, "report", "<html>Report</html>")

        loaded = load_html(session_id, "nonexistent")
        assert loaded is None

    def test_save_meta(self):
        """Test saving metadata."""
        session_id = "test123"
        meta = {
            "id": session_id,
            "topic": "Test Topic",
            "report_type": "research"
        }

        save_meta(session_id, meta)

        meta_path = self.test_sessions_dir / session_id / "meta.json"
        assert meta_path.exists()
        loaded_meta = json.loads(meta_path.read_text(encoding='utf-8'))
        assert loaded_meta == meta

    def test_load_meta_existing(self):
        """Test loading existing metadata."""
        session_id = "test123"
        meta = {
            "id": session_id,
            "topic": "Test Topic"
        }

        save_meta(session_id, meta)
        loaded = load_meta(session_id)

        assert loaded == meta

    def test_load_meta_nonexistent(self):
        """Test loading non-existent metadata."""
        loaded = load_meta("nonexistent")
        assert loaded is None

    def test_save_meta_overwrites(self):
        """Test that save_meta overwrites existing metadata."""
        session_id = "test123"
        meta1 = {"id": session_id, "topic": "Topic 1"}
        meta2 = {"id": session_id, "topic": "Topic 2"}

        save_meta(session_id, meta1)
        save_meta(session_id, meta2)

        loaded = load_meta(session_id)
        assert loaded["topic"] == "Topic 2"

    def test_save_html_overwrites(self):
        """Test that save_html overwrites existing HTML."""
        session_id = "test123"
        html1 = "<html>Content 1</html>"
        html2 = "<html>Content 2</html>"

        save_html(session_id, "report", html1)
        save_html(session_id, "report", html2)

        loaded = load_html(session_id, "report")
        assert loaded == html2

