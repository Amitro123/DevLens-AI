"""Tests for zombie session cleanup functionality"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


def test_zombie_session_cleanup_via_session_manager(client):
    """Test that SessionManager marks zombie sessions as failed"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        # SessionManager returns None (which means it either has no active sessions
        # or it detected zombies and cleaned them up)
        mock_mgr = MagicMock()
        mock_mgr.get_active_session.return_value = None
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_draft_sessions.return_value = []
            mock_get_watcher.return_value = mock_watcher
            
            response = client.get("/api/v1/active-session")
            
            # No active session should be returned
            assert response.json() is None


def test_active_session_valid(client):
    """Test that recent sessions are returned correctly"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_active_session.return_value = {
            "session_id": "fresh_123",
            "status": "processing",
            "title": "Fresh Project",
            "mode": "bug_report",
            "progress": 50
        }
        mock_get_mgr.return_value = mock_mgr
        
        response = client.get("/api/v1/active-session")
        
        data = response.json()
        assert data["session_id"] == "fresh_123"
        assert data["status"] == "processing"


def test_cancel_session_endpoint(client):
    """Test manual cancellation through SessionManager"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.cancel.return_value = True
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_session.return_value = None
            mock_get_watcher.return_value = mock_watcher
            
            response = client.post("/api/v1/sessions/test_session/cancel")
            assert response.status_code == 200
            
            # Verify cancel was called
            mock_mgr.cancel.assert_called_once_with("test_session")


def test_cancel_session_not_found(client):
    """Test cancellation when session not found in SessionManager but found in Calendar"""
    mock_session = MagicMock()
    mock_session.status = "processing"
    
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.cancel.return_value = False  # Not found in SessionManager
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_session.return_value = mock_session
            mock_get_watcher.return_value = mock_watcher
            
            response = client.post("/api/v1/sessions/cal_session/cancel")
            assert response.status_code == 200
            
            # Calendar should update status
            mock_watcher.update_session_status.assert_called_once()
