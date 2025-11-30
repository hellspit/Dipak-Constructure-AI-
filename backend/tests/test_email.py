import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.email import router, get_gmail_service, decode_email_body, get_header
from app.models import UserSession, create_session
from app.auth import get_credentials


class TestEmailHelpers:
    """Test email helper functions"""
    
    def test_get_header(self):
        """Test getting header value"""
        headers = [
            {'name': 'From', 'value': 'sender@example.com'},
            {'name': 'Subject', 'value': 'Test Subject'},
            {'name': 'Date', 'value': 'Mon, 1 Jan 2024 10:00:00'}
        ]
        
        assert get_header(headers, 'From') == 'sender@example.com'
        assert get_header(headers, 'Subject') == 'Test Subject'
        assert get_header(headers, 'Nonexistent') == ''
    
    def test_decode_email_body_plain(self):
        """Test decoding plain text email body"""
        message_data = {
            'payload': {
                'mimeType': 'text/plain',
                'body': {'data': 'dGVzdCBlbWFpbCBib2R5'}
            }
        }
        
        body = decode_email_body(message_data)
        assert body == 'test email body'
    
    def test_decode_email_body_html(self):
        """Test decoding HTML email body"""
        message_data = {
            'payload': {
                'mimeType': 'text/html',
                'body': {'data': 'PHA+VGVzdCBib2R5PC9wPg=='}
            }
        }
        
        body = decode_email_body(message_data)
        assert 'Test body' in body
    
    def test_decode_email_body_multipart(self):
        """Test decoding multipart email body"""
        message_data = {
            'payload': {
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': 'dGVzdCBib2R5'}
                    }
                ]
            }
        }
        
        body = decode_email_body(message_data)
        assert body == 'test body'


class TestEmailEndpoints:
    """Test email endpoints"""
    
    @patch('app.email.get_credentials')
    @patch('app.email.build')
    def test_list_emails_success(self, mock_build, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test listing emails successfully"""
        create_session(sample_session)
        
        # Mock credentials
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        # Mock Gmail service
        mock_service = Mock()
        mock_messages = Mock()
        mock_messages.list.return_value.execute.return_value = {
            'messages': [
                {'id': 'msg1', 'threadId': 'thread1'},
                {'id': 'msg2', 'threadId': 'thread2'}
            ]
        }
        
        def mock_get(userId, id, format=None, metadataHeaders=None):
            mock_msg = Mock()
            mock_msg.execute.return_value = {
                'id': id,
                'threadId': f'thread{id[-1]}',
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'Subject', 'value': 'Test Subject'},
                        {'name': 'Date', 'value': 'Mon, 1 Jan 2024 10:00:00'}
                    ],
                    'body': {'data': 'dGVzdCBib2R5'},
                    'mimeType': 'text/plain'
                },
                'snippet': 'Test snippet'
            }
            return mock_msg
        
        mock_messages.get = mock_get
        mock_service.users.return_value.messages.return_value = mock_messages
        mock_build.return_value = mock_service
        
        with patch('app.email.generate_email_summary') as mock_summary:
            mock_summary.return_value = "AI generated summary"
            
            response = client.get(
                "/api/email/list?max_results=2",
                headers={"X-Session-Id": sample_session.session_id}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "emails" in data
            assert len(data["emails"]) == 2
    
    @patch('app.email.get_credentials')
    def test_list_emails_invalid_session(self, mock_get_creds, client, env_vars):
        """Test listing emails with invalid session"""
        mock_get_creds.return_value = None
        
        response = client.get(
            "/api/email/list",
            headers={"X-Session-Id": "invalid_session"}
        )
        
        assert response.status_code == 401
    
    @patch('app.email.get_credentials')
    @patch('app.email.build')
    @patch('app.email.generate_email_reply')
    def test_generate_replies_success(self, mock_reply, mock_build, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test generating email replies"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_service = Mock()
        mock_messages = Mock()
        
        def mock_get(userId, id, format=None, metadataHeaders=None):
            mock_msg = Mock()
            mock_msg.execute.return_value = {
                'id': id,
                'payload': {
                    'headers': [
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'Subject', 'value': 'Test Subject'}
                    ],
                    'body': {'data': 'dGVzdCBib2R5'},
                    'mimeType': 'text/plain'
                }
            }
            return mock_msg
        
        mock_messages.get = mock_get
        mock_service.users.return_value.messages.return_value = mock_messages
        mock_build.return_value = mock_service
        mock_reply.return_value = "Generated reply text"
        
        response = client.post(
            "/api/email/reply/generate",
            json={"email_ids": ["msg1", "msg2"]},
            headers={"X-Session-Id": sample_session.session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "replies" in data
        assert len(data["replies"]) == 2
    
    @patch('app.email.get_credentials')
    @patch('app.email.build')
    def test_send_reply_success(self, mock_build, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test sending a reply"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_service = Mock()
        mock_messages = Mock()
        
        # Mock get message
        mock_get_msg = Mock()
        mock_get_msg.execute.return_value = {
            'id': 'msg1',
            'threadId': 'thread1',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Subject', 'value': 'Test Subject'}
                ]
            }
        }
        mock_messages.get.return_value = mock_get_msg
        
        # Mock send
        mock_send = Mock()
        mock_send.execute.return_value = {'id': 'sent_msg_id'}
        mock_messages.send.return_value = mock_send
        
        mock_service.users.return_value.messages.return_value = mock_messages
        mock_build.return_value = mock_service
        
        response = client.post(
            "/api/email/reply/send",
            json={
                "email_id": "msg1",
                "reply_text": "This is a test reply"
            },
            headers={"X-Session-Id": sample_session.session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message_id" in data
    
    @patch('app.email.get_credentials')
    @patch('app.email.build')
    def test_delete_email_success(self, mock_build, mock_get_creds, client, env_vars, temp_sessions_file, sample_session):
        """Test deleting an email"""
        create_session(sample_session)
        
        mock_creds = Mock()
        mock_get_creds.return_value = mock_creds
        
        mock_service = Mock()
        mock_messages = Mock()
        mock_delete = Mock()
        mock_delete.execute.return_value = None
        mock_messages.delete.return_value = mock_delete
        
        mock_service.users.return_value.messages.return_value = mock_messages
        mock_build.return_value = mock_service
        
        response = client.delete(
            "/api/email/delete/msg1",
            headers={"X-Session-Id": sample_session.session_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

