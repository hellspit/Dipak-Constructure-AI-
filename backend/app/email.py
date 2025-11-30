from fastapi import APIRouter, HTTPException, Header
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Optional
from pydantic import BaseModel
import base64
import re
from email.utils import parseaddr
import logging

from app.auth import get_credentials
from app.ai import generate_email_summary, generate_email_reply


class GenerateRepliesRequest(BaseModel):
    email_ids: List[str]


class SendReplyRequest(BaseModel):
    email_id: str
    reply_text: str


class SearchEmailsRequest(BaseModel):
    query: str
    max_results: int = 5

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


def get_gmail_service(session_id: str):
    """Get Gmail service for a session"""
    credentials = get_credentials(session_id)
    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return build('gmail', 'v1', credentials=credentials)


def decode_email_body(message_data: Dict) -> str:
    """Decode email body from Gmail API format"""
    body = ""
    
    if 'parts' in message_data['payload']:
        for part in message_data['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                # Simple HTML to text conversion
                body += re.sub('<[^<]+?>', '', html_body)
    else:
        if message_data['payload']['mimeType'] == 'text/plain':
            data = message_data['payload']['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif message_data['payload']['mimeType'] == 'text/html':
            data = message_data['payload']['body']['data']
            html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            body = re.sub('<[^<]+?>', '', html_body)
    
    return body.strip()


def get_header(headers: List[Dict], name: str) -> str:
    """Get header value from headers list"""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""


@router.get("/list")
async def list_emails(
    max_results: int = 5,
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Get list of recent emails with AI summaries"""
    try:
        service = get_gmail_service(session_id)
        
        # Get message list
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"emails": []}
        
        emails = []
        
        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                payload = message['payload']
                headers = payload.get('headers', [])
                
                sender = get_header(headers, 'From')
                subject = get_header(headers, 'Subject')
                date = get_header(headers, 'Date')
                
                # Parse sender name and email
                sender_name, sender_email = parseaddr(sender)
                if not sender_name:
                    sender_name = sender_email
                
                # Decode body
                body = decode_email_body(message)
                
                # Generate AI summary
                summary = await generate_email_summary(body, subject, sender_name)
                
                emails.append({
                    "id": msg['id'],
                    "thread_id": message.get('threadId'),
                    "sender": sender_name,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date,
                    "body": body[:500],  # Truncate for response
                    "summary": summary,
                    "snippet": message.get('snippet', '')
                })
            except Exception as e:
                logger.error(f"Error processing email {msg.get('id')}: {str(e)}")
                continue
        
        return {"emails": emails}
        
    except HTTPException:
        raise
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/reply/generate")
async def generate_replies(
    request: GenerateRepliesRequest,
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Generate AI replies for specified emails"""
    try:
        service = get_gmail_service(session_id)
        replies = []
        
        for email_id in request.email_ids:
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=email_id,
                    format='full'
                ).execute()
                
                payload = message['payload']
                headers = payload.get('headers', [])
                
                sender = get_header(headers, 'From')
                subject = get_header(headers, 'Subject')
                body = decode_email_body(message)
                
                original_email = {
                    "id": email_id,
                    "sender": sender,
                    "subject": subject,
                    "body": body
                }
                
                reply_text = await generate_email_reply(original_email)
                
                replies.append({
                    "email_id": email_id,
                    "original_subject": subject,
                    "original_sender": sender,
                    "reply": reply_text
                })
            except Exception as e:
                logger.error(f"Error generating reply for {email_id}: {str(e)}")
                replies.append({
                    "email_id": email_id,
                    "error": str(e)
                })
        
        return {"replies": replies}
        
    except Exception as e:
        logger.error(f"Error generating replies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/reply/send")
async def send_reply(
    request: SendReplyRequest,
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Send a reply email"""
    try:
        service = get_gmail_service(session_id)
        
        # Get original message to reply to
        message = service.users().messages().get(
            userId='me',
            id=request.email_id,
            format='metadata',
            metadataHeaders=['From', 'To', 'Subject']
        ).execute()
        
        headers = message['payload'].get('headers', [])
        original_from = get_header(headers, 'From')
        original_subject = get_header(headers, 'Subject')
        thread_id = message.get('threadId')
        
        # Create reply message
        to_email = parseaddr(original_from)[1]
        subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject
        
        message_body = f"To: {to_email}\r\n"
        message_body += f"Subject: {subject}\r\n"
        message_body += "Content-Type: text/plain; charset=utf-8\r\n"
        message_body += "\r\n"
        message_body += request.reply_text
        
        email_message = {
            'raw': base64.urlsafe_b64encode(message_body.encode('utf-8')).decode('utf-8'),
            'threadId': thread_id
        }
        
        sent_message = service.users().messages().send(
            userId='me',
            body=email_message
        ).execute()
        
        return {
            "success": True,
            "message_id": sent_message['id'],
            "message": "Email sent successfully"
        }
        
    except HttpError as e:
        logger.error(f"Gmail API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending reply: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/delete/{email_id}")
async def delete_email(
    email_id: str,
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Delete an email"""
    try:
        service = get_gmail_service(session_id)
        
        service.users().messages().delete(
            userId='me',
            id=email_id
        ).execute()
        
        return {
            "success": True,
            "message": "Email deleted successfully"
        }
        
    except HttpError as e:
        error_details = str(e)
        logger.error(f"Gmail API error: {error_details}")
        
        # Check if it's a scope/permission issue
        if "insufficient" in error_details.lower() or "permission" in error_details.lower():
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions. Please sign out and sign in again to grant email deletion permissions."
            )
        
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {error_details}")
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/search")
async def search_emails(
    request: SearchEmailsRequest,
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Search emails by query (sender, subject, etc.)"""
    try:
        service = get_gmail_service(session_id)
        
        results = service.users().messages().list(
            userId='me',
            q=request.query,
            maxResults=request.max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"emails": []}
        
        emails = []
        for msg in messages[:request.max_results]:
            try:
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = message['payload'].get('headers', [])
                sender = get_header(headers, 'From')
                subject = get_header(headers, 'Subject')
                date = get_header(headers, 'Date')
                
                sender_name, sender_email = parseaddr(sender)
                
                emails.append({
                    "id": msg['id'],
                    "sender": sender_name or sender_email,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date,
                    "snippet": message.get('snippet', '')
                })
            except Exception as e:
                logger.error(f"Error processing email: {str(e)}")
                continue
        
        return {"emails": emails}
        
    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

