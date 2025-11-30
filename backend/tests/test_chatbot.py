import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.chatbot import router
from app.models import UserSession, create_session


class TestChatbotEndpoints:
    """Test chatbot endpoints"""
    
    @patch('app.chatbot.get_credentials')
    @patch('app.chatbot.parse_natural_language_command')
    def test_process_message_greeting(self, mock_parse, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test processing a greeting message"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        response = client.post(
            "/api/chatbot/message",
            json={
                "message": "Hello",
                "session_id": sample_session.session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "action" in data
    
    @patch('app.chatbot.get_credentials')
    @patch('app.chatbot.parse_natural_language_command')
    @patch('app.chatbot.handle_read_emails')
    def test_process_message_read_emails(self, mock_read, mock_parse, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test processing a read emails command"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_parse.return_value = {
            "action": "read",
            "parameters": {"max_results": 5}
        }
        
        from app.chatbot import ChatResponse
        mock_read.return_value = ChatResponse(
            response="Here are your emails...",
            action="read",
            data={"emails": []}
        )
        
        response = client.post(
            "/api/chatbot/message",
            json={
                "message": "Show me my emails",
                "session_id": sample_session.session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "read"
    
    @patch('app.chatbot.get_credentials')
    @patch('app.chatbot.parse_natural_language_command')
    @patch('app.chatbot.handle_generate_replies')
    def test_process_message_generate_replies(self, mock_reply, mock_parse, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test processing a generate replies command"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_parse.return_value = {
            "action": "reply",
            "parameters": {}
        }
        
        from app.chatbot import ChatResponse
        mock_reply.return_value = ChatResponse(
            response="Here are the generated replies...",
            action="reply",
            data={"replies": []}
        )
        
        response = client.post(
            "/api/chatbot/message",
            json={
                "message": "Generate replies for my emails",
                "session_id": sample_session.session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reply"
    
    @patch('app.chatbot.get_credentials')
    @patch('app.chatbot.parse_natural_language_command')
    @patch('app.chatbot.handle_delete_email')
    def test_process_message_delete_email(self, mock_delete, mock_parse, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test processing a delete email command"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_parse.return_value = {
            "action": "delete",
            "parameters": {"email_number": 1}
        }
        
        from app.chatbot import ChatResponse
        mock_delete.return_value = ChatResponse(
            response="Email deleted successfully",
            action="delete"
        )
        
        response = client.post(
            "/api/chatbot/message",
            json={
                "message": "Delete email number 1",
                "session_id": sample_session.session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "delete"
    
    def test_process_message_invalid_session(self, client, env_vars):
        """Test processing message with invalid session"""
        response = client.post(
            "/api/chatbot/message",
            json={
                "message": "Hello",
                "session_id": "invalid_session"
            }
        )
        
        assert response.status_code == 401
    
    @patch('app.models.get_session')
    @patch('googleapiclient.discovery.build')
    def test_get_greeting_success(self, mock_build, mock_get_session, client, env_vars, temp_sessions_file, sample_session):
        """Test getting greeting with user info"""
        create_session(sample_session)
        mock_get_session.return_value = sample_session
        
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
        
        response = client.get(
            "/api/chatbot/greeting",
            headers={"X-Session-Id": sample_session.session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "greeting" in data
        assert "user" in data
        assert data["user"]["name"] == "Test User"

