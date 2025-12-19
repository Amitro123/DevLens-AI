
import pytest
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
import os

# Use the client fixture from conftest.py implicitly or create a new one if needed
# We'll use TestClient directly for simplicity in this unit test file
client = TestClient(app)

@pytest.fixture
def mock_video_file(tmp_path):
    """Create a dummy video file for testing streaming"""
    # Create a mock video file (1MB)
    video_dir = tmp_path / "uploads" / "test_stream_task"
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = video_dir / "video.mp4"
    
    # Write random bytes
    with open(video_path, "wb") as f:
        f.write(os.urandom(1024 * 1024))
        
    # Patch settings to point to this temp dir
    from app.core.config import settings
    original_upload_dir = settings.upload_dir
    settings.upload_dir = str(tmp_path / "uploads")
    
    yield "test_stream_task"
    
    # Cleanup
    settings.upload_dir = original_upload_dir

def test_stream_video_range_request(mock_video_file):
    """Test that the streaming endpoint handles Range requests correctly (206)"""
    task_id = mock_video_file
    
    # Request first 100 bytes
    headers = {"Range": "bytes=0-99"}
    response = client.get(f"/api/v1/stream/{task_id}", headers=headers)
    
    assert response.status_code == 206
    assert response.headers["content-range"].startswith("bytes 0-99/")
    assert len(response.content) == 100
    assert response.headers["accept-ranges"] == "bytes"

def test_stream_video_full_request(mock_video_file):
    """Test full file request (206 with full range implicitly or 200 depending on impl)"""
    # Our impl returns 206 for generic streaming too mostly
    task_id = mock_video_file
    response = client.get(f"/api/v1/stream/{task_id}")
    
    # Standard streaming often defaults to 206 or 200. 
    # Our implementation in streaming.py handles Range header. 
    # If no Range header, it defaults to 0-end.
    
    assert response.status_code == 206
    assert "content-range" in response.headers
    assert response.headers["accept-ranges"] == "bytes"

def test_stream_video_not_found():
    """Test streaming specific 404 behavior"""
    response = client.get("/api/v1/stream/non_existent_task")
    assert response.status_code == 404
