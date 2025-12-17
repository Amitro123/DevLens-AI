"""
Observability module for DevLens AI pipeline tracing.

Provides AcontextClient for logging pipeline operations to Acontext
and @trace_pipeline decorator for automatic function instrumentation.
"""

import time
import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class AcontextError(Exception):
    """Exception for Acontext API errors"""
    pass


class AcontextClient:
    """
    Client for interacting with Acontext Context Data Platform.
    
    Provides session management for tracing and artifact storage
    for persisting pipeline outputs.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None
    ):
        """
        Initialize the Acontext client.
        
        Args:
            base_url: Acontext API base URL (default from settings)
            api_key: API key for authentication (default from settings)
            enabled: Whether tracing is enabled (default from settings)
        """
        self.base_url = base_url or getattr(settings, 'acontext_url', 'http://localhost:8029/api/v1')
        self.api_key = api_key or getattr(settings, 'acontext_api_key', 'sk-ac-your-root-api-bearer-token')
        self._enabled = enabled if enabled is not None else getattr(settings, 'acontext_enabled', True)
        
        self._session_id: Optional[str] = None
        self._disk_id: Optional[str] = None
        self._connected: Optional[bool] = None
        
    @property
    def is_enabled(self) -> bool:
        """Check if tracing is enabled and Acontext is reachable"""
        if not self._enabled:
            return False
        
        # Cache connection status
        if self._connected is None:
            self._connected = self._check_connection()
        
        return self._connected
    
    def _check_connection(self) -> bool:
        """Verify Acontext service is reachable"""
        try:
            response = requests.get(
                f"{self.base_url}/ping",
                headers=self._get_headers(),
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Acontext not reachable: {e}. Tracing disabled.")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_session(self, name: Optional[str] = None) -> Optional[str]:
        """
        Create a new tracing session.
        
        Args:
            name: Optional session name
            
        Returns:
            Session ID if successful, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/sessions",
                headers=self._get_headers(),
                json={"name": name or f"devlens-{int(time.time())}"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            self._session_id = data.get("id")
            logger.info(f"Created Acontext session: {self._session_id}")
            return self._session_id
        except Exception as e:
            logger.warning(f"Failed to create Acontext session: {e}")
            return None
    
    def get_or_create_session(self, name: Optional[str] = None) -> Optional[str]:
        """Get existing session or create a new one"""
        if self._session_id:
            return self._session_id
        return self.create_session(name)
    
    def send_message(
        self,
        content: Dict[str, Any],
        role: str = "assistant",
        session_id: Optional[str] = None
    ) -> bool:
        """
        Log a message to the session.
        
        Args:
            content: Message content (will be JSON serialized)
            role: Message role (user/assistant)
            session_id: Session ID (uses current if not provided)
            
        Returns:
            True if successful
        """
        if not self.is_enabled:
            return False
        
        sid = session_id or self._session_id
        if not sid:
            sid = self.create_session()
            if not sid:
                return False
        
        try:
            # Format as OpenAI-compatible message
            message = {
                "role": role,
                "content": json.dumps(content) if isinstance(content, dict) else str(content)
            }
            
            response = requests.post(
                f"{self.base_url}/sessions/{sid}/messages",
                headers=self._get_headers(),
                json={"blob": message, "format": "openai"},
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to Acontext: {e}")
            return False
    
    def create_disk(self, name: Optional[str] = None) -> Optional[str]:
        """
        Create a disk for artifact storage.
        
        Args:
            name: Optional disk name
            
        Returns:
            Disk ID if successful
        """
        if not self.is_enabled:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/disks",
                headers=self._get_headers(),
                json={"name": name or f"devlens-artifacts-{int(time.time())}"},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            self._disk_id = data.get("id")
            logger.info(f"Created Acontext disk: {self._disk_id}")
            return self._disk_id
        except Exception as e:
            logger.warning(f"Failed to create Acontext disk: {e}")
            return None
    
    def get_or_create_disk(self, name: Optional[str] = None) -> Optional[str]:
        """Get existing disk or create a new one"""
        if self._disk_id:
            return self._disk_id
        return self.create_disk(name)
    
    def add_artifact(
        self,
        filename: str,
        content: bytes,
        path: str = "/",
        disk_id: Optional[str] = None
    ) -> bool:
        """
        Store an artifact file.
        
        Args:
            filename: Name of the artifact file
            content: File content as bytes
            path: Storage path (e.g., "/outputs/")
            disk_id: Disk ID (uses current if not provided)
            
        Returns:
            True if successful
        """
        if not self.is_enabled:
            return False
        
        did = disk_id or self._disk_id
        if not did:
            did = self.create_disk()
            if not did:
                return False
        
        try:
            # Use multipart form for file upload
            files = {
                'file': (filename, content, 'application/octet-stream')
            }
            data = {
                'file_path': path
            }
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.post(
                f"{self.base_url}/disks/{did}/artifacts",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Stored artifact: {path}{filename}")
            return True
        except Exception as e:
            logger.warning(f"Failed to store artifact in Acontext: {e}")
            return False
    
    def close_session(self) -> None:
        """Mark the current session as complete"""
        self._session_id = None


# Singleton client instance
_acontext_client: Optional[AcontextClient] = None


def get_acontext_client() -> AcontextClient:
    """Get or create the singleton Acontext client"""
    global _acontext_client
    if _acontext_client is None:
        _acontext_client = AcontextClient()
    return _acontext_client


def reset_acontext_client() -> None:
    """Reset the singleton client (for testing)"""
    global _acontext_client
    _acontext_client = None


def _summarize_value(value: Any, max_length: int = 200) -> str:
    """Create a summary of a value for logging"""
    if value is None:
        return "None"
    
    if isinstance(value, (str, bytes)):
        length = len(value)
        if length > max_length:
            if isinstance(value, bytes):
                return f"<bytes: {length} bytes>"
            return f"{value[:max_length]}... ({length} chars)"
        return str(value)
    
    if isinstance(value, list):
        return f"<list: {len(value)} items>"
    
    if isinstance(value, dict):
        return f"<dict: {len(value)} keys>"
    
    return str(value)[:max_length]


def _summarize_args(args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Summarize function arguments for logging"""
    summary = {}
    
    for i, arg in enumerate(args):
        summary[f"arg_{i}"] = _summarize_value(arg)
    
    for key, value in kwargs.items():
        summary[key] = _summarize_value(value)
    
    return summary


def trace_pipeline(func: Callable) -> Callable:
    """
    Decorator to trace function execution to Acontext.
    
    Captures:
    - Function name
    - Input arguments summary
    - Output summary
    - Execution duration
    - Any errors
    
    Usage:
        @trace_pipeline
        def my_pipeline_step(input_data: str) -> str:
            return process(input_data)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = get_acontext_client()
        
        # If tracing is disabled, just run the function
        if not client.is_enabled:
            return func(*args, **kwargs)
        
        # Ensure session exists
        client.get_or_create_session()
        
        # Capture start time
        start_time = time.time()
        error_info = None
        result = None
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_info = str(e)
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Build trace message
            trace_data = {
                "function": func.__name__,
                "module": func.__module__,
                "duration_ms": round(duration_ms, 2),
                "input": _summarize_args(args, kwargs),
                "output": _summarize_value(result) if error_info is None else None,
                "error": error_info,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            # Send to Acontext
            client.send_message(trace_data, role="assistant")
            
            # Log locally too
            status = "ERROR" if error_info else "OK"
            logger.debug(
                f"[TRACE] {func.__name__} - {status} - {duration_ms:.2f}ms"
            )
    
    return wrapper


@contextmanager
def trace_session(name: Optional[str] = None):
    """
    Context manager for grouping traces into a session.
    
    Usage:
        with trace_session("video_processing"):
            extract_audio(...)
            generate_docs(...)
    """
    client = get_acontext_client()
    
    if client.is_enabled:
        client.create_session(name)
    
    try:
        yield client
    finally:
        if client.is_enabled:
            client.close_session()


def extract_code_blocks(markdown: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown content.
    
    Args:
        markdown: Markdown text with code blocks
        
    Returns:
        List of dicts with 'lang' and 'code' keys
    """
    import re
    
    pattern = r'```(\w*)\n(.*?)```'
    matches = re.findall(pattern, markdown, re.DOTALL)
    
    return [
        {"lang": lang or "txt", "code": code.strip()}
        for lang, code in matches
    ]
