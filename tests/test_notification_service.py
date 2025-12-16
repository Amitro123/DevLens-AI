"""Tests for Notification Service and Scheduler"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.notification_service import NotificationService, get_notification_service
from app.services.calendar_service import (
    CalendarWatcher, 
    DraftSession, 
    CalendarEvent,
    get_calendar_watcher
)


class TestNotificationService:
    """Test suite for NotificationService class"""
    
    def test_notification_service_init(self):
        """Test NotificationService initializes correctly"""
        service = NotificationService()
        assert service is not None

    def test_send_reminder(self, capsys):
        """Test pre-meeting reminder is sent"""
        service = NotificationService()
        result = service.send_reminder("user@example.com", "Design Review")
        
        captured = capsys.readouterr()
        assert result is True
        assert "📧 EMAIL TO user@example.com" in captured.out
        assert "Design Review" in captured.out
        assert "Don't forget to record" in captured.out

    def test_send_upload_nudge(self, capsys):
        """Test post-meeting upload nudge is sent"""
        service = NotificationService()
        result = service.send_upload_nudge(
            "user@example.com", 
            "Bug Triage", 
            "session_123"
        )
        
        captured = capsys.readouterr()
        assert result is True
        assert "📧 EMAIL TO user@example.com" in captured.out
        assert "Bug Triage" in captured.out
        assert "/upload/session_123" in captured.out

    def test_send_completion_notification(self, capsys):
        """Test completion notification is sent"""
        service = NotificationService()
        result = service.send_completion_notification(
            "user@example.com",
            "Feature Demo",
            "session_456"
        )
        
        captured = capsys.readouterr()
        assert result is True
        assert "📧 EMAIL TO user@example.com" in captured.out
        assert "Feature Demo" in captured.out
        assert "/results/session_456" in captured.out

    def test_get_notification_service_singleton(self):
        """Test singleton pattern for NotificationService"""
        service1 = get_notification_service()
        service2 = get_notification_service()
        assert service1 is service2


class TestNotificationScheduler:
    """Test suite for notification scheduler triggers"""
    
    @pytest.fixture
    def calendar_watcher(self):
        """Create a fresh CalendarWatcher instance"""
        watcher = CalendarWatcher()
        return watcher

    def test_pre_meeting_reminder_trigger(self, calendar_watcher, capsys):
        """Test pre-meeting reminder triggers at correct time"""
        now = datetime.now()
        
        # Create a session with event starting in 10 minutes
        session = DraftSession(
            session_id="test_session_1",
            event_id="evt_1",
            title="Upcoming Meeting",
            attendees=["alice@example.com"],
            context_keywords=["test"],
            status="waiting_for_upload",
            created_at=now,
            metadata={
                "event_start": (now + timedelta(minutes=10)).isoformat(),
                "event_end": (now + timedelta(minutes=70)).isoformat()
            },
            reminder_sent=False,
            nudge_sent=False
        )
        
        calendar_watcher.draft_sessions[session.session_id] = session
        
        # Trigger check
        calendar_watcher.check_notification_triggers()
        
        captured = capsys.readouterr()
        assert "📧 EMAIL TO alice@example.com" in captured.out
        assert "Upcoming Meeting" in captured.out
        assert session.reminder_sent is True

    def test_post_meeting_nudge_trigger(self, calendar_watcher, capsys):
        """Test post-meeting nudge triggers at correct time"""
        now = datetime.now()
        
        # Create a session with event ended 5 minutes ago
        session = DraftSession(
            session_id="test_session_2",
            event_id="evt_2",
            title="Completed Meeting",
            attendees=["bob@example.com"],
            context_keywords=["demo"],
            status="waiting_for_upload",
            created_at=now - timedelta(hours=2),
            metadata={
                "event_start": (now - timedelta(hours=1, minutes=10)).isoformat(),
                "event_end": (now - timedelta(minutes=5)).isoformat()
            },
            reminder_sent=True,
            nudge_sent=False
        )
        
        calendar_watcher.draft_sessions[session.session_id] = session
        
        # Trigger check
        calendar_watcher.check_notification_triggers()
        
        captured = capsys.readouterr()
        assert "📧 EMAIL TO bob@example.com" in captured.out
        assert "Completed Meeting" in captured.out
        assert session.nudge_sent is True

    def test_no_duplicate_reminders(self, calendar_watcher, capsys):
        """Test reminders don't send twice"""
        now = datetime.now()
        
        session = DraftSession(
            session_id="test_session_3",
            event_id="evt_3",
            title="Already Reminded",
            attendees=["user@example.com"],
            context_keywords=["test"],
            status="waiting_for_upload",
            created_at=now,
            metadata={
                "event_start": (now + timedelta(minutes=10)).isoformat(),
                "event_end": (now + timedelta(minutes=70)).isoformat()
            },
            reminder_sent=True,  # Already sent
            nudge_sent=False
        )
        
        calendar_watcher.draft_sessions[session.session_id] = session
        
        # Trigger check
        calendar_watcher.check_notification_triggers()
        
        captured = capsys.readouterr()
        # Should NOT send reminder again
        assert "Already Reminded" not in captured.out

    def test_completed_sessions_skipped(self, calendar_watcher, capsys):
        """Test completed sessions don't trigger notifications"""
        now = datetime.now()
        
        session = DraftSession(
            session_id="test_session_4",
            event_id="evt_4",
            title="Completed Session",
            attendees=["user@example.com"],
            context_keywords=["test"],
            status="completed",  # Already completed
            created_at=now,
            metadata={
                "event_start": (now - timedelta(hours=1)).isoformat(),
                "event_end": (now - timedelta(minutes=5)).isoformat()
            },
            reminder_sent=False,
            nudge_sent=False
        )
        
        calendar_watcher.draft_sessions[session.session_id] = session
        
        # Trigger check
        calendar_watcher.check_notification_triggers()
        
        captured = capsys.readouterr()
        # Should NOT send any notifications
        assert "Completed Session" not in captured.out
