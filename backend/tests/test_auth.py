import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.auth import router, get_credentials
from app.models import UserSession, create_session, get_session


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_google_auth_initiate(self, client, env_vars):
        """Test initiating Google OAuth flow"""
        with patch('app.auth.get_oauth_flow') as mock_flow:
            mock_flow_instance = Mock()
            mock_flow_instance.authorization_url.return_value = (
                "https://accounts.google.com/o/oauth2/auth?state=test",
                "test_state"
            )
            mock_flow.return_value = mock_flow_instance
            
            response = client.get("/api/auth/google")
            
            assert response.status_code == 200
            data = response.json()
            assert "authorization_url" in data
            assert "state" in data
    
    def test_google_callback_invalid_state(self, client, env_vars):
        """Test OAuth callback with invalid state"""
        response = client.get("/api/auth/callback/google?code=test_code&state=invalid_state")
        
        assert response.status_code == 400
        assert "Invalid state parameter" in response.json()["detail"]
    
    @patch('app.auth.build')
    @patch('app.auth.Flow')
    def test_google_callback_success(self, mock_flow_class, mock_build, client, env_vars, temp_sessions_file):
        """Test successful OAuth callback"""
        # Setup mock flow
        mock_flow = Mock()
        mock_flow_instance = Mock()
        mock_flow_instance.fetch_token = Mock()
        mock_flow_instance.credentials = Mock()
        mock_flow_instance.credentials.token = "access_token"
        mock_flow_instance.credentials.refresh_token = "refresh_token"
        mock_flow_instance.credentials.expiry = datetime.utcnow() + timedelta(hours=1)
        
        # Store flow in active_flows
        from app.auth import active_flows
        active_flows["test_state"] = mock_flow_instance
        
        # Mock user info service
        mock_userinfo = Mock()
        mock_userinfo.get.return_value.execute.return_value = {
            'email': 'test@example.com',
            'name': 'Test User'
        }
        mock_oauth2 = Mock()
        mock_oauth2.userinfo.return_value = mock_userinfo
        mock_build.return_value = mock_oauth2
        
        response = client.get("/api/auth/callback/google?code=test_code&state=test_state", follow_redirects=False)
        
        # Should redirect to frontend
        assert response.status_code in [302, 307]
        assert "dashboard" in response.headers.get("location", "")
        assert "session" in response.headers.get("location", "")
    
    def test_get_session_not_found(self, client, env_vars, temp_sessions_file):
        """Test getting a non-existent session"""
        response = client.get("/api/auth/session/nonexistent")
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_get_session_expired(self, client, env_vars, temp_sessions_file, expired_session):
        """Test getting an expired session"""
        create_session(expired_session)
        
        response = client.get(f"/api/auth/session/{expired_session.session_id}")
        
        assert response.status_code == 401
        assert "Session expired" in response.json()["detail"]
    
    def test_get_session_success(self, client, env_vars, temp_sessions_file, sample_session):
        """Test getting a valid session"""
        create_session(sample_session)
        
        response = client.get(f"/api/auth/session/{sample_session.session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == sample_session.session_id
        assert data["user_email"] == sample_session.user_email
        assert "expires_at" in data
    
    @patch('app.auth.build')
    def test_get_user_info_success(self, mock_build, client, env_vars, temp_sessions_file, sample_session):
        """Test getting user info"""
        create_session(sample_session)
        
        # Mock user info service
        mock_userinfo = Mock()
        mock_userinfo.get.return_value.execute.return_value = {
            'email': 'test@example.com',
            'name': 'Test User',
            'picture': 'https://example.com/pic.jpg'
        }
        mock_oauth2 = Mock()
        mock_oauth2.userinfo.return_value = mock_userinfo
        mock_build.return_value = mock_oauth2
        
        response = client.get(f"/api/auth/user/{sample_session.session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["picture"] == "https://example.com/pic.jpg"
    
    def test_get_user_info_not_found(self, client, env_vars, temp_sessions_file):
        """Test getting user info for non-existent session"""
        response = client.get("/api/auth/user/nonexistent")
        
        assert response.status_code == 404


class TestGetCredentials:
    """Test get_credentials function"""
    
    def test_get_credentials_not_found(self, temp_sessions_file):
        """Test getting credentials for non-existent session"""
        credentials = get_credentials("nonexistent")
        assert credentials is None
    
    def test_get_credentials_expired(self, temp_sessions_file, expired_session):
        """Test getting credentials for expired session"""
        create_session(expired_session)
        credentials = get_credentials(expired_session.session_id)
        assert credentials is None
    
    @patch('app.auth.GoogleRequest')
    def test_get_credentials_success(self, mock_request, temp_sessions_file, sample_session):
        """Test getting valid credentials"""
        create_session(sample_session)
        
        credentials = get_credentials(sample_session.session_id)
        
        assert credentials is not None
        assert credentials.token == sample_session.access_token
        assert credentials.refresh_token == sample_session.refresh_token
    
    @patch('app.auth.GoogleRequest')
    @patch('app.auth.update_session')
    def test_get_credentials_refresh(self, mock_update, mock_request, temp_sessions_file, sample_session):
        """Test refreshing expired credentials"""
        create_session(sample_session)
        
        # Mock expired credentials
        with patch('app.auth.Credentials') as mock_creds_class:
            mock_creds = Mock()
            mock_creds.expired = True
            mock_creds.token = "new_token"
            mock_creds.refresh_token = "new_refresh"
            mock_creds.refresh = Mock()
            mock_creds_class.return_value = mock_creds
            
            credentials = get_credentials(sample_session.session_id)
            
            assert credentials is not None
            mock_creds.refresh.assert_called_once()
            mock_update.assert_called_once()

