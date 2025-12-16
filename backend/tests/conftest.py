import pytest
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def mock_genai():
    with patch('google.generativeai.GenerativeModel') as mock:
        yield mock

@pytest.fixture
def mock_flash_response():
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "relevant_segments": [
            {"start": 10.0, "end": 20.0, "reason": "Technical discussion"},
            {"start": 30.0, "end": 40.0, "reason": "Bug analysis"}
        ],
        "technical_percentage": 50.0
    })
    return mock_resp

@pytest.fixture
def mock_pro_response():
    mock_resp = MagicMock()
    mock_resp.text = "# Generated Documentation\n\nThis is a mock doc."
    return mock_resp

@pytest.fixture
def client():
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)
