from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import json
from typing import Optional

from app.config import settings
from app.models import UserSession, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Store active flows temporarily (in production, use Redis)
active_flows = {}


def get_oauth_flow():
    """Create OAuth flow"""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{settings.frontend_url}/api/auth/callback/google"]
            }
        },
        scopes=SCOPES,
        redirect_uri=f"{settings.frontend_url}/api/auth/callback/google"
    )


@router.get("/google")
async def google_auth():
    """Initiate Google OAuth flow"""
    flow = get_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store flow with state
    active_flows[state] = flow
    
    return {"authorization_url": authorization_url, "state": state}


@router.get("/callback/google")
async def google_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    if state not in active_flows:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    flow = active_flows[state]
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user info
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=credentials.expiry.timestamp() - datetime.utcnow().timestamp()) if credentials.expiry else datetime.utcnow() + timedelta(hours=1)
        
        # Store session in database
        db_session = UserSession(
            session_id=session_id,
            user_email=user_email,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_at=expires_at
        )
        db.add(db_session)
        db.commit()
        
        # Clean up flow
        del active_flows[state]
        
        # Redirect to frontend with session
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?session={session_id}",
            status_code=302
        )
        
    except Exception as e:
        del active_flows[state]
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session information"""
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    
    return {
        "session_id": session.session_id,
        "user_email": session.user_email,
        "expires_at": session.expires_at.isoformat()
    }


@router.get("/user/{session_id}")
async def get_user_info(session_id: str, db: Session = Depends(get_db)):
    """Get user profile information"""
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired")
    
    try:
        credentials = Credentials(
            token=session.access_token,
            refresh_token=session.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret
        )
        
        # Refresh if needed
        if credentials.expired:
            credentials.refresh(GoogleRequest())
            session.access_token = credentials.token
            if credentials.refresh_token:
                session.refresh_token = credentials.refresh_token
            db.commit()
        
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        return {
            "email": user_info.get('email'),
            "name": user_info.get('name'),
            "picture": user_info.get('picture')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to get user info: {str(e)}")


def get_credentials(session_id: str, db: Session) -> Optional[Credentials]:
    """Get credentials for a session"""
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    
    if not session or session.expires_at < datetime.utcnow():
        return None
    
    credentials = Credentials(
        token=session.access_token,
        refresh_token=session.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret
    )
    
    # Refresh if needed
    if credentials.expired:
        try:
            credentials.refresh(GoogleRequest())
            session.access_token = credentials.token
            if credentials.refresh_token:
                session.refresh_token = credentials.refresh_token
            db.commit()
        except Exception:
            return None
    
    return credentials

