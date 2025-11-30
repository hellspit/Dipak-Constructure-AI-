import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models import UserSession, SESSIONS_FILE, load_sessions, save_sessions


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def temp_sessions_file(tmp_path, monkeypatch):
    """Create a temporary sessions.json file for testing"""
    test_file = tmp_path / "sessions.json"
    monkeypatch.setattr("app.models.SESSIONS_FILE", test_file)
    yield test_file
    # Cleanup
    if test_file.exists():
        test_file.unlink()


@pytest.fixture
def sample_session():
    """Create a sample user session"""
    return UserSession(
        session_id="test_session_123",
        user_email="test@example.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        created_at=datetime.utcnow()
    )


@pytest.fixture
def expired_session():
    """Create an expired user session"""
    return UserSession(
        session_id="expired_session_123",
        user_email="test@example.com",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() - timedelta(hours=1),
        created_at=datetime.utcnow() - timedelta(hours=2)
    )


@pytest.fixture
def mock_google_credentials():
    """Mock Google OAuth credentials"""
    credentials = Mock()
    credentials.token = "mock_access_token"
    credentials.refresh_token = "mock_refresh_token"
    credentials.expiry = datetime.utcnow() + timedelta(hours=1)
    credentials.expired = False
    return credentials


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail service"""
    service = Mock()
    
    # Mock messages list
    messages_list = {
        'messages': [
            {'id': 'msg1', 'threadId': 'thread1'},
            {'id': 'msg2', 'threadId': 'thread2'},
        ]
    }
    
    # Mock message get
    def mock_get_message(userId, id, format=None, metadataHeaders=None):
        mock_msg = Mock()
        mock_msg.execute.return_value = {
            'id': id,
            'threadId': f'thread{id[-1]}',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 10:00:00 -0800'}
                ],
                'body': {'data': 'dGVzdCBlbWFpbCBib2R5'},
                'mimeType': 'text/plain'
            },
            'snippet': 'Test email snippet'
        }
        return mock_msg
    
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = messages_list
    service.users.return_value.messages.return_value.get = mock_get_message
    service.users.return_value.messages.return_value.send.return_value.execute.return_value = {'id': 'sent_msg_id'}
    service.users.return_value.messages.return_value.delete.return_value.execute.return_value = None
    
    return service


@pytest.fixture
def mock_groq_client():
    """Mock Groq AI client"""
    client = Mock()
    
    # Mock chat completion response
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Mock AI response"
    
    client.chat.completions.create.return_value = mock_response
    return client


@pytest.fixture
def env_vars(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_12345678901234567890")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")

