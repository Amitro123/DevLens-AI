"""Tests for active session recovery functionality"""

import pytest
from unittest.mock import MagicMock, patch


def test_get_active_session_none(client):
    """Test when no sessions are active"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_active_session.return_value = None
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_draft_sessions.return_value = []
            mock_get_watcher.return_value = mock_watcher
            
            response = client.get("/api/v1/active-session")
            assert response.status_code == 200
            assert response.json() is None


def test_get_active_session_from_session_manager(client):
    """Test when SessionManager has an active session"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_active_session.return_value = {
            "session_id": "active_123",
            "status": "processing",
            "title": "Active Session",
            "mode": "general_doc",
            "progress": 50
        }
        mock_get_mgr.return_value = mock_mgr
        
        response = client.get("/api/v1/active-session")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "active_123"
        assert data["status"] == "processing"
        assert data["title"] == "Active Session"
        assert data["progress"] == 50


def test_get_active_session_calendar_fallback(client):
    """Test fallback to calendar when SessionManager has no active session"""
    mock_session = MagicMock()
    mock_session.session_id = "cal_session_456"
    mock_session.status = "processing"
    mock_session.title = "Calendar Meeting"
    mock_session.suggested_mode = "bug_report"
    
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_active_session.return_value = None
        mock_mgr.get_status.return_value = {"progress": 60}
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_draft_sessions.return_value = [mock_session]
            mock_get_watcher.return_value = mock_watcher
            
            response = client.get("/api/v1/active-session")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "cal_session_456"
            assert data["status"] == "processing"
            assert data["progress"] == 60


def test_get_status_from_session_manager(client):
    """Test that get_status uses SessionManager"""
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_status.return_value = {
            "status": "processing",
            "progress": 75,
            "stage": "generating_docs",
            "title": "Test",
            "mode": "general_doc",
            "mode_name": "General Documentation",
            "error": None,
            "created_at": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:01:00"
        }
        mock_get_mgr.return_value = mock_mgr
        
        response = client.get("/api/v1/status/test_session_123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 75


def test_get_status_calendar_fallback(client):
    """Test that get_status falls back to calendar when SessionManager returns None"""
    mock_session = MagicMock()
    mock_session.status = "downloading_from_drive"
    
    with patch("app.api.routes.get_session_manager") as mock_get_mgr:
        mock_mgr = MagicMock()
        mock_mgr.get_status.return_value = None
        mock_get_mgr.return_value = mock_mgr
        
        with patch("app.services.calendar_service.get_calendar_watcher") as mock_get_watcher:
            mock_watcher = MagicMock()
            mock_watcher.get_session.return_value = mock_session
            mock_get_watcher.return_value = mock_watcher
            
            response = client.get("/api/v1/status/cal_session_123")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "downloading_from_drive"
            assert data["progress"] == 30
