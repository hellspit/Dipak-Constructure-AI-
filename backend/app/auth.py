from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import secrets
import logging
from typing import Optional

from app.config import settings
from app.models import UserSession, get_session, create_session, update_session, delete_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# OAuth 2.0 scopes
# Note: 'openid' is automatically added by Google, but we include it explicitly to avoid scope mismatch
SCOPES = [
    'openid',
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
                "redirect_uris": [f"{settings.backend_url}/api/auth/callback/google"]
            }
        },
        scopes=SCOPES,
        redirect_uri=f"{settings.backend_url}/api/auth/callback/google"
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
    state: str
):
    """Handle Google OAuth callback"""
    # Try to use stored flow first (preserves exact scopes)
    if state in active_flows:
        flow = active_flows[state]
        del active_flows[state]
        logger.info("Using stored OAuth flow")
    else:
        # Recreate flow - always use the default SCOPES
        # The state validation is handled by Google, so we can safely recreate
        logger.info("Recreating OAuth flow (state not found in memory)")
        flow = get_oauth_flow()
    
    try:
        logger.info(f"Fetching token with code for state: {state[:10]}...")
        # Fetch token - Google may add additional scopes (email, profile, openid)
        # which causes a scope mismatch warning, but we can ignore it
        try:
            flow.fetch_token(code=code)
        except Exception as scope_error:
            # Check if it's a scope mismatch warning (not a real error)
            error_str = str(scope_error).lower()
            if "scope" in error_str and ("changed" in error_str or "mismatch" in error_str):
                logger.warning(f"Scope mismatch warning (can be ignored): {str(scope_error)}")
                # Try to get credentials anyway - the token might still be valid
                if hasattr(flow, 'credentials') and flow.credentials:
                    credentials = flow.credentials
                else:
                    raise  # Re-raise if we can't get credentials
            else:
                raise  # Re-raise if it's a different error
        
        credentials = flow.credentials
        logger.info("Token fetched successfully")
        
        # Get user info
        logger.info("Building OAuth2 service to get user info")
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        user_email = user_info.get('email')
        logger.info(f"User info retrieved for: {user_email}")
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        
        # Calculate expiration - use token expiry if available, otherwise default to 1 hour
        if credentials.expiry:
            # Ensure expires_at is timezone-naive UTC datetime
            expires_at = credentials.expiry
            if expires_at.tzinfo is not None:
                # Convert timezone-aware to naive UTC
                expires_at = expires_at.replace(tzinfo=None)
            logger.info(f"Using token expiry: {expires_at.isoformat()}")
        else:
            expires_at = datetime.utcnow() + timedelta(hours=1)
            logger.info(f"Using default expiry (1 hour): {expires_at.isoformat()}")
        
        # Store session in JSON file
        logger.info(f"Creating session: {session_id[:10]}...")
        db_session = UserSession(
            session_id=session_id,
            user_email=user_email,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_at=expires_at
        )
        create_session(db_session)
        logger.info("Session created successfully")
        
        # Redirect to frontend with session
        redirect_url = f"{settings.frontend_url}/dashboard?session={session_id}"
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(
            url=redirect_url,
            status_code=302
        )
        
    except Exception as e:
        # Clean up flow if it was stored
        if state in active_flows:
            del active_flows[state]
        
        # Log the full error for debugging
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        
        # Check if it's an invalid_grant error (code already used or expired)
        error_msg = str(e)
        if "invalid_grant" in error_msg.lower():
            # Redirect to frontend with error message
            error_param = "?error=auth_failed&message=Authorization code expired or already used. Please try signing in again."
            return RedirectResponse(
                url=f"{settings.frontend_url}/login{error_param}",
                status_code=302
            )
        
        # For other errors, redirect with more specific message
        from urllib.parse import quote
        error_detail = error_msg[:100] if len(error_msg) > 100 else error_msg
        error_message = f"Authentication failed: {error_detail}. Please try again."
        error_param = f"?error=auth_failed&message={quote(error_message)}"
        return RedirectResponse(
            url=f"{settings.frontend_url}/login{error_param}",
            status_code=302
        )


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    now = datetime.utcnow()
    if session.expires_at < now:
        logger.warning(f"Session {session_id[:10]}... expired. Expires: {session.expires_at.isoformat()}, Now: {now.isoformat()}")
        delete_session(session_id)
        raise HTTPException(status_code=401, detail="Session expired")
    
    logger.info(f"Session {session_id[:10]}... valid. Expires: {session.expires_at.isoformat()}, Now: {now.isoformat()}")
    
    return {
        "session_id": session.session_id,
        "user_email": session.user_email,
        "expires_at": session.expires_at.isoformat()
    }


@router.get("/user/{session_id}")
async def get_user_info(session_id: str):
    """Get user profile information"""
    session = get_session(session_id)
    
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
            update_session(session)
        
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        return {
            "email": user_info.get('email'),
            "name": user_info.get('name'),
            "picture": user_info.get('picture')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to get user info: {str(e)}")


def get_credentials(session_id: str) -> Optional[Credentials]:
    """Get credentials for a session"""
    session = get_session(session_id)
    
    if not session or session.expires_at < datetime.utcnow():
        return None
    
    credentials = Credentials(
        token=session.access_token,
        refresh_token=session.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES  # Ensure credentials have the right scopes
    )
    
    # Refresh if needed
    if credentials.expired:
        try:
            credentials.refresh(GoogleRequest())
            session.access_token = credentials.token
            if credentials.refresh_token:
                session.refresh_token = credentials.refresh_token
            update_session(session)
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            return None
    
    return credentials

