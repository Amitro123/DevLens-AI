"""Unit tests for SessionManager"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def session_manager():
    """Create a fresh SessionManager for each test"""
    # Reset the singleton to get a fresh instance
    from app.services import session_manager as sm_module
    sm_module._session_manager = None
    
    with patch("app.services.session_manager.get_storage_service") as mock_storage:
        mock_storage.return_value.get_history.return_value = []
        mock_storage.return_value.get_session_result.return_value = None
        
        from app.services.session_manager import get_session_manager
        mgr = get_session_manager()
        mgr._storage = mock_storage.return_value
        yield mgr


class TestSessionCreate:
    """Tests for session creation"""
    
    def test_create_session_basic(self, session_manager):
        result = session_manager.create_session("test_123", {
            "project_name": "Test Project",
            "mode": "general_doc"
        })
        
        assert result["session_id"] == "test_123"
        assert result["status"] == "draft"
        assert result["title"] == "Test Project"
        assert result["mode"] == "general_doc"
        assert result["progress"] == 0
    
    def test_create_session_with_title(self, session_manager):
        result = session_manager.create_session("test_456", {
            "title": "Custom Title",
            "mode": "bug_report"
        })
        
        assert result["title"] == "Custom Title"
        assert result["mode"] == "bug_report"


class TestSessionProcessing:
    """Tests for session lifecycle"""
    
    def test_start_processing(self, session_manager):
        session_manager.create_session("proc_test", {"title": "Test"})
        session_manager.start_processing("proc_test")
        
        status = session_manager.get_status("proc_test")
        assert status["status"] == "processing"
        assert status["progress"] == 0
        assert status["stage"] == "initializing"
    
    def test_update_progress(self, session_manager):
        session_manager.create_session("prog_test", {"title": "Test"})
        session_manager.start_processing("prog_test")
        session_manager.update_progress("prog_test", "extracting_frames", 50)
        
        status = session_manager.get_status("prog_test")
        assert status["progress"] == 50
        assert status["stage"] == "extracting_frames"
    
    def test_progress_clamped(self, session_manager):
        session_manager.create_session("clamp_test", {"title": "Test"})
        session_manager.update_progress("clamp_test", "test", 150)
        
        status = session_manager.get_status("clamp_test")
        assert status["progress"] == 100  # Clamped to max
        
        session_manager.update_progress("clamp_test", "test", -10)
        status = session_manager.get_status("clamp_test")
        assert status["progress"] == 0  # Clamped to min


class TestSessionCompletion:
    """Tests for session completion and failure"""
    
    def test_complete(self, session_manager):
        session_manager.create_session("comp_test", {"title": "Test"})
        session_manager.start_processing("comp_test")
        session_manager.complete("comp_test", "/path/to/doc.md", "# Documentation")
        
        status = session_manager.get_status("comp_test")
        assert status["status"] == "completed"
        assert status["progress"] == 100
        assert status["stage"] == "completed"
    
    def test_fail(self, session_manager):
        session_manager.create_session("fail_test", {"title": "Test"})
        session_manager.start_processing("fail_test")
        session_manager.fail("fail_test", "Something went wrong")
        
        status = session_manager.get_status("fail_test")
        assert status["status"] == "failed"
        assert status["error"] == "Something went wrong"
    
    def test_cancel(self, session_manager):
        session_manager.create_session("cancel_test", {"title": "Test"})
        session_manager.start_processing("cancel_test")
        
        result = session_manager.cancel("cancel_test")
        assert result is True
        
        status = session_manager.get_status("cancel_test")
        assert status["status"] == "cancelled"
    
    def test_cancel_already_completed(self, session_manager):
        session_manager.create_session("nocancel_test", {"title": "Test"})
        session_manager.complete("nocancel_test", "/path", "doc")
        
        result = session_manager.cancel("nocancel_test")
        assert result is False  # Can't cancel completed session


class TestSessionStatus:
    """Tests for status queries"""
    
    def test_get_status_not_found(self, session_manager):
        status = session_manager.get_status("nonexistent")
        assert status is None
    
    def test_get_status_structure(self, session_manager):
        session_manager.create_session("struct_test", {
            "title": "Structure Test",
            "mode": "general_doc",
            "mode_name": "General Documentation"
        })
        
        status = session_manager.get_status("struct_test")
        
        # Verify all expected fields are present
        assert "status" in status
        assert "progress" in status
        assert "stage" in status
        assert "title" in status
        assert "mode" in status
        assert "created_at" in status
        assert "last_updated" in status


class TestActiveSession:
    """Tests for active session recovery"""
    
    def test_get_active_session_none(self, session_manager):
        result = session_manager.get_active_session()
        assert result is None
    
    def test_get_active_session_processing(self, session_manager):
        session_manager.create_session("active_test", {"title": "Active Test"})
        session_manager.start_processing("active_test")
        
        result = session_manager.get_active_session()
        assert result is not None
        assert result["session_id"] == "active_test"
        assert result["status"] == "processing"
    
    def test_get_active_session_ignores_completed(self, session_manager):
        session_manager.create_session("done_test", {"title": "Done"})
        session_manager.complete("done_test", "/path", "doc")
        
        result = session_manager.get_active_session()
        assert result is None
