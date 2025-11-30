import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.models import (
    UserSession,
    load_sessions,
    save_sessions,
    get_session,
    create_session,
    update_session,
    delete_session,
    get_all_sessions
)


class TestUserSession:
    """Test UserSession model"""
    
    def test_user_session_creation(self):
        """Test creating a UserSession"""
        session = UserSession(
            session_id="test123",
            user_email="test@example.com",
            access_token="token123",
            refresh_token="refresh123",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert session.session_id == "test123"
        assert session.user_email == "test@example.com"
        assert session.access_token == "token123"
        assert session.refresh_token == "refresh123"
        assert isinstance(session.created_at, datetime)
    
    def test_user_session_to_dict(self):
        """Test converting session to dictionary"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        session = UserSession(
            session_id="test123",
            user_email="test@example.com",
            access_token="token123",
            refresh_token="refresh123",
            expires_at=expires_at
        )
        
        data = session.to_dict()
        
        assert data["session_id"] == "test123"
        assert data["user_email"] == "test@example.com"
        assert data["access_token"] == "token123"
        assert data["refresh_token"] == "refresh123"
        assert isinstance(data["expires_at"], str)
        assert isinstance(data["created_at"], str)
    
    def test_user_session_from_dict(self):
        """Test creating session from dictionary"""
        data = {
            "session_id": "test123",
            "user_email": "test@example.com",
            "access_token": "token123",
            "refresh_token": "refresh123",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        session = UserSession.from_dict(data)
        
        assert session.session_id == "test123"
        assert session.user_email == "test@example.com"
        assert session.access_token == "token123"
        assert isinstance(session.expires_at, datetime)
        assert isinstance(session.created_at, datetime)


class TestSessionStorage:
    """Test session storage functions"""
    
    def test_load_sessions_empty_file(self, temp_sessions_file):
        """Test loading sessions from empty file"""
        sessions = load_sessions()
        assert sessions == {}
    
    def test_save_and_load_sessions(self, temp_sessions_file):
        """Test saving and loading sessions"""
        test_data = {
            "session1": {
                "session_id": "session1",
                "user_email": "user1@example.com",
                "access_token": "token1",
                "refresh_token": "refresh1",
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        save_sessions(test_data)
        loaded = load_sessions()
        
        assert loaded == test_data
    
    def test_create_session(self, temp_sessions_file):
        """Test creating a new session"""
        session = UserSession(
            session_id="new_session",
            user_email="new@example.com",
            access_token="new_token",
            refresh_token="new_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        create_session(session)
        
        loaded = get_session("new_session")
        assert loaded is not None
        assert loaded.user_email == "new@example.com"
    
    def test_get_session_not_found(self, temp_sessions_file):
        """Test getting a non-existent session"""
        session = get_session("nonexistent")
        assert session is None
    
    def test_update_session(self, temp_sessions_file):
        """Test updating an existing session"""
        session = UserSession(
            session_id="update_test",
            user_email="original@example.com",
            access_token="original_token",
            refresh_token="original_refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        create_session(session)
        
        # Update the session
        session.access_token = "updated_token"
        update_session(session)
        
        updated = get_session("update_test")
        assert updated.access_token == "updated_token"
    
    def test_update_session_not_found(self, temp_sessions_file):
        """Test updating a non-existent session"""
        session = UserSession(
            session_id="nonexistent",
            user_email="test@example.com",
            access_token="token",
            refresh_token="refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        with pytest.raises(ValueError):
            update_session(session)
    
    def test_delete_session(self, temp_sessions_file):
        """Test deleting a session"""
        session = UserSession(
            session_id="delete_test",
            user_email="delete@example.com",
            access_token="token",
            refresh_token="refresh",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        create_session(session)
        delete_session("delete_test")
        
        deleted = get_session("delete_test")
        assert deleted is None
    
    def test_get_all_sessions(self, temp_sessions_file):
        """Test getting all sessions"""
        # Create multiple sessions
        for i in range(3):
            session = UserSession(
                session_id=f"session_{i}",
                user_email=f"user{i}@example.com",
                access_token=f"token_{i}",
                refresh_token=f"refresh_{i}",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            create_session(session)
        
        all_sessions = get_all_sessions()
        assert len(all_sessions) == 3
        assert "session_0" in all_sessions
        assert "session_1" in all_sessions
        assert "session_2" in all_sessions

