
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import task_results, STALE_TIMEOUT_SECONDS
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_task_results():
    """Isolate task_results for each test"""
    with patch.dict("app.api.routes.task_results", {}, clear=True):
        yield

def test_active_session_recovery_zombie_cleanup():
    """Test that stale sessions are marked as failed"""
    # 1. Inject a stale session into in-memory task_results
    stale_id = str(uuid.uuid4())
    # We need to access the *actual* dict being used by the app, which is now patched
    # But since we patched it in the fixture, we can just import it and use it?
    # No, patch.dict patches the object in place.
    from app.api.routes import task_results as tr
    
    tr[stale_id] = {
        "status": "processing",
        "project_name": "Zombie Project",
        "mode": "bug_report",
        "progress": 50,
        "last_updated": datetime.now() - timedelta(seconds=STALE_TIMEOUT_SECONDS + 60) # 11 mins ago
    }
    
    # 2. Call active-session
    response = client.get("/api/v1/active-session")
    
    # 3. Should return None (no active session) because it was expired
    assert response.json() is None
    
    # 4. Verify it was marked failed in memory
    assert tr[stale_id]["status"] == "failed"
    assert "Zombie" in tr[stale_id]["error"]

def test_active_session_valid():
    """Test that recent sessions are NOT cleaned up"""
    # 1. Inject a fresh session
    fresh_id = str(uuid.uuid4())
    from app.api.routes import task_results as tr
    
    tr[fresh_id] = {
        "status": "processing",
        "project_name": "Fresh Project",
        "mode": "bug_report",
        "progress": 50,
        "last_updated": datetime.now() # Just now
    }
    
    # 2. Call active-session
    response = client.get("/api/v1/active-session")
    
    # 3. Should match fresh_id
    data = response.json()
    assert data["session_id"] == fresh_id
    assert data["status"] == "processing"

def test_cancel_session_endpoint():
    """Test manual cancellation"""
    # 1. Inject active session
    cancel_id = str(uuid.uuid4())
    from app.api.routes import task_results as tr
    
    tr[cancel_id] = {
        "status": "processing",
        "last_updated": datetime.now()
    }
    
    # 2. Call cancel
    response = client.post(f"/api/v1/sessions/{cancel_id}/cancel")
    assert response.status_code == 200
    
    # 3. Verify status
    assert tr[cancel_id]["status"] == "cancelled"
