import json
import os
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# JSON file path for storing sessions
SESSIONS_FILE = Path("sessions.json")


class UserSession:
    """User session model for JSON storage"""
    
    def __init__(self, session_id: str, user_email: str, access_token: str, 
                 refresh_token: Optional[str], expires_at: datetime, created_at: Optional[datetime] = None):
        self.session_id = session_id
        self.user_email = user_email
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON storage"""
        return {
            "session_id": self.session_id,
            "user_email": self.user_email,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSession':
        """Create session from dictionary"""
        return cls(
            session_id=data["session_id"],
            user_email=data["user_email"],
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if isinstance(data["expires_at"], str) else data["expires_at"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at")
        )


def load_sessions() -> Dict[str, Dict]:
    """Load all sessions from JSON file"""
    if not SESSIONS_FILE.exists():
        return {}
    
    try:
        with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading sessions: {str(e)}")
        return {}


def save_sessions(sessions: Dict[str, Dict]):
    """Save all sessions to JSON file"""
    try:
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error(f"Error saving sessions: {str(e)}")
        raise


def get_session(session_id: str) -> Optional[UserSession]:
    """Get a session by ID"""
    sessions = load_sessions()
    session_data = sessions.get(session_id)
    if not session_data:
        return None
    return UserSession.from_dict(session_data)


def create_session(session: UserSession):
    """Create a new session"""
    sessions = load_sessions()
    sessions[session.session_id] = session.to_dict()
    save_sessions(sessions)


def update_session(session: UserSession):
    """Update an existing session"""
    sessions = load_sessions()
    if session.session_id not in sessions:
        raise ValueError(f"Session {session.session_id} not found")
    sessions[session.session_id] = session.to_dict()
    save_sessions(sessions)


def delete_session(session_id: str):
    """Delete a session"""
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(sessions)


def get_all_sessions() -> Dict[str, UserSession]:
    """Get all sessions"""
    sessions = load_sessions()
    return {sid: UserSession.from_dict(data) for sid, data in sessions.items()}


# Compatibility function for FastAPI dependency injection
def get_db():
    """Dummy database dependency for compatibility"""
    # This is a no-op now, but kept for compatibility with existing code
    # The actual database operations are done through the functions above
    yield None
