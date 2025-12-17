"""Tests for Acontext observability module"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import time


class TestAcontextClient:
    """Test suite for AcontextClient class"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch('app.core.observability.settings') as mock:
            mock.acontext_url = "http://test:8029/api/v1"
            mock.acontext_api_key = "test-api-key"
            mock.acontext_enabled = True
            yield mock
    
    @pytest.fixture
    def mock_requests(self):
        """Mock requests module"""
        with patch('app.core.observability.requests') as mock:
            yield mock
    
    def test_client_initialization(self, mock_settings):
        """Test client initializes with settings"""
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        
        assert client.base_url == "http://test:8029/api/v1"
        assert client.api_key == "test-api-key"
        assert client._enabled == True
    
    def test_client_disabled_when_setting_false(self, mock_settings, mock_requests):
        """Test client respects disabled setting"""
        mock_settings.acontext_enabled = False
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        
        assert client.is_enabled == False
        # Should not make any HTTP requests
        mock_requests.get.assert_not_called()
    
    def test_client_connection_check_success(self, mock_settings, mock_requests):
        """Test successful connection check"""
        mock_requests.get.return_value.status_code = 200
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        
        assert client.is_enabled == True
        mock_requests.get.assert_called_once()
    
    def test_client_connection_check_failure(self, mock_settings, mock_requests):
        """Test failed connection check disables client"""
        mock_requests.get.side_effect = Exception("Connection refused")
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        
        assert client.is_enabled == False
    
    def test_create_session(self, mock_settings, mock_requests):
        """Test session creation"""
        mock_requests.get.return_value.status_code = 200
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.json.return_value = {"id": "session-123"}
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        session_id = client.create_session("test-session")
        
        assert session_id == "session-123"
        assert client._session_id == "session-123"
    
    def test_send_message(self, mock_settings, mock_requests):
        """Test message sending"""
        mock_requests.get.return_value.status_code = 200
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.json.return_value = {"id": "session-123"}
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        client._session_id = "session-123"
        
        result = client.send_message({"test": "data"})
        
        assert result == True
    
    def test_send_message_when_disabled(self, mock_settings, mock_requests):
        """Test message not sent when disabled"""
        mock_settings.acontext_enabled = False
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        result = client.send_message({"test": "data"})
        
        assert result == False
    
    def test_add_artifact(self, mock_settings, mock_requests):
        """Test artifact storage"""
        mock_requests.get.return_value.status_code = 200
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.raise_for_status = MagicMock()
        mock_requests.post.return_value.json.return_value = {"id": "disk-123"}
        
        from app.core.observability import AcontextClient
        
        client = AcontextClient()
        client._disk_id = "disk-123"
        
        result = client.add_artifact(
            filename="test.md",
            content=b"# Test",
            path="/outputs/"
        )
        
        assert result == True


class TestTracePipelineDecorator:
    """Test suite for @trace_pipeline decorator"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock AcontextClient"""
        with patch('app.core.observability.get_acontext_client') as mock:
            client = MagicMock()
            client.is_enabled = True
            client.get_or_create_session.return_value = "session-123"
            mock.return_value = client
            yield client
    
    def test_decorator_traces_function(self, mock_client):
        """Test decorator captures function execution"""
        from app.core.observability import trace_pipeline
        
        @trace_pipeline
        def sample_function(x: int) -> int:
            return x * 2
        
        result = sample_function(5)
        
        assert result == 10
        mock_client.send_message.assert_called_once()
        
        # Verify trace data
        call_args = mock_client.send_message.call_args
        trace_data = call_args[0][0]
        
        assert trace_data["function"] == "sample_function"
        assert "duration_ms" in trace_data
        assert trace_data["error"] is None
    
    def test_decorator_captures_errors(self, mock_client):
        """Test decorator captures function errors"""
        from app.core.observability import trace_pipeline
        
        @trace_pipeline
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Still sends trace with error info
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args
        trace_data = call_args[0][0]
        
        assert "Test error" in trace_data["error"]
    
    def test_decorator_noop_when_disabled(self):
        """Test decorator is no-op when client disabled"""
        with patch('app.core.observability.get_acontext_client') as mock:
            client = MagicMock()
            client.is_enabled = False
            mock.return_value = client
            
            from app.core.observability import trace_pipeline
            
            @trace_pipeline
            def sample_function():
                return "result"
            
            result = sample_function()
            
            assert result == "result"
            client.send_message.assert_not_called()


class TestExtractCodeBlocks:
    """Test suite for extract_code_blocks utility"""
    
    def test_extract_python_code_block(self):
        """Test extracting Python code blocks"""
        from app.core.observability import extract_code_blocks
        
        markdown = '''
# Documentation

```python
def hello():
    print("Hello, World!")
```

Some text.
'''
        
        blocks = extract_code_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["lang"] == "python"
        assert "def hello():" in blocks[0]["code"]
    
    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks"""
        from app.core.observability import extract_code_blocks
        
        markdown = '''
```javascript
console.log("JS");
```

```python
print("Python")
```
'''
        
        blocks = extract_code_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["lang"] == "javascript"
        assert blocks[1]["lang"] == "python"
    
    def test_extract_no_code_blocks(self):
        """Test handling markdown without code blocks"""
        from app.core.observability import extract_code_blocks
        
        markdown = "# Just a heading\n\nSome text."
        
        blocks = extract_code_blocks(markdown)
        
        assert len(blocks) == 0
    
    def test_extract_unlabeled_code_block(self):
        """Test extracting code block without language label"""
        from app.core.observability import extract_code_blocks
        
        markdown = '''
```
some code
```
'''
        
        blocks = extract_code_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["lang"] == "txt"


class TestSingletonClient:
    """Test suite for singleton client pattern"""
    
    def test_get_acontext_client_returns_singleton(self):
        """Test that get_acontext_client returns same instance"""
        from app.core.observability import get_acontext_client, reset_acontext_client
        
        # Reset first
        reset_acontext_client()
        
        with patch('app.core.observability.settings') as mock_settings:
            mock_settings.acontext_url = "http://test:8029/api/v1"
            mock_settings.acontext_api_key = "test-key"
            mock_settings.acontext_enabled = False  # Disabled to skip connection check
            
            client1 = get_acontext_client()
            client2 = get_acontext_client()
            
            assert client1 is client2
        
        reset_acontext_client()
    
    def test_reset_acontext_client_clears_singleton(self):
        """Test that reset_acontext_client clears the singleton"""
        from app.core.observability import get_acontext_client, reset_acontext_client
        
        with patch('app.core.observability.settings') as mock_settings:
            mock_settings.acontext_url = "http://test:8029/api/v1"
            mock_settings.acontext_api_key = "test-key"
            mock_settings.acontext_enabled = False
            
            client1 = get_acontext_client()
            reset_acontext_client()
            client2 = get_acontext_client()
            
            assert client1 is not client2
        
        reset_acontext_client()
