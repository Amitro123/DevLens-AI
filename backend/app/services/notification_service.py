"""Notification service for sending email reminders and nudges"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications to users.
    
    MVP Implementation: Mock prints to console.
    Production: Integrate with SendGrid, SES, etc.
    """
    
    def __init__(self):
        """Initialize the notification service"""
        logger.info("NotificationService initialized (mock mode)")
    
    def send_reminder(self, email: str, meeting_title: str) -> bool:
        """
        Send a pre-meeting reminder to record the session.
        
        Args:
            email: Recipient email address
            meeting_title: Title of the upcoming meeting
        
        Returns:
            True if notification was sent successfully
        """
        message = f"📧 EMAIL TO {email}: Don't forget to record '{meeting_title}' for DevLens!"
        print(message)
        logger.info(f"Sent pre-meeting reminder to {email} for '{meeting_title}'")
        return True
    
    def send_upload_nudge(self, email: str, meeting_title: str, session_id: str) -> bool:
        """
        Send a post-meeting nudge to upload the recording.
        
        Args:
            email: Recipient email address
            meeting_title: Title of the completed meeting
            session_id: Session ID for the upload link
        
        Returns:
            True if notification was sent successfully
        """
        message = f"📧 EMAIL TO {email}: Meeting '{meeting_title}' ended. Click here to upload: /upload/{session_id}"
        print(message)
        logger.info(f"Sent upload nudge to {email} for session {session_id}")
        return True
    
    def send_completion_notification(self, email: str, meeting_title: str, session_id: str) -> bool:
        """
        Send a notification when documentation is ready.
        
        Args:
            email: Recipient email address
            meeting_title: Title of the meeting
            session_id: Session ID to view results
        
        Returns:
            True if notification was sent successfully
        """
        message = f"📧 EMAIL TO {email}: Documentation for '{meeting_title}' is ready! View: /results/{session_id}"
        print(message)
        logger.info(f"Sent completion notification to {email} for session {session_id}")
        return True


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create the NotificationService singleton"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
