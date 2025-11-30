from fastapi import APIRouter, HTTPException, Header
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

from app.auth import get_credentials
from app.email import get_gmail_service, decode_email_body, get_header
from app.ai import (
    parse_natural_language_command,
    generate_email_summary,
    generate_email_reply
)
from email.utils import parseaddr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])


class ChatMessage(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None
    data: Optional[Dict] = None


@router.post("/message", response_model=ChatResponse)
async def process_chat_message(
    chat_message: ChatMessage
):
    """
    Process natural language chat messages and execute email operations.
    This is the main chatbot endpoint that handles user commands.
    """
    try:
        user_message = chat_message.message.lower().strip()
        session_id = chat_message.session_id
        
        # Verify session
        credentials = get_credentials(session_id)
        if not credentials:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        # Parse the natural language command
        try:
            parsed_command = await parse_natural_language_command(chat_message.message)
            action = parsed_command.get("action", "unknown")
            parameters = parsed_command.get("parameters", {})
            logger.info(f"AI parsed command: action={action}, parameters={parameters}")
        except Exception as e:
            logger.error(f"Error parsing command with AI: {str(e)}")
            action = "unknown"
            parameters = {}
        
        # Fallback: If AI parsing fails, try simple keyword matching
        if action == "unknown":
            user_lower = user_message
            if any(word in user_lower for word in ["read", "show", "list", "get", "fetch", "display", "see"]):
                if any(word in user_lower for word in ["email", "mail", "message", "inbox"]):
                    action = "read"
                    # Try to extract number
                    import re
                    numbers = re.findall(r'\d+', user_message)
                    if numbers:
                        parameters["max_results"] = int(numbers[0])
            elif any(word in user_lower for word in ["reply", "respond", "answer", "generate"]):
                if any(word in user_lower for word in ["email", "mail", "message"]):
                    action = "reply"
            elif any(word in user_lower for word in ["delete", "remove", "trash"]):
                if any(word in user_lower for word in ["email", "mail", "message"]):
                    action = "delete"
                    # Try to extract email number
                    import re
                    numbers = re.findall(r'\d+', user_message)
                    if numbers:
                        parameters["email_number"] = int(numbers[0])
        
        # Handle different actions
        if action == "read":
            return await handle_read_emails(session_id, parameters)
        elif action == "reply":
            return await handle_generate_replies(session_id, parameters)
        elif action == "delete":
            return await handle_delete_email(session_id, parameters)
        elif "greeting" in user_message or "hello" in user_message or "hi" in user_message:
            return ChatResponse(
                response="Hello! I'm your email assistant. I can help you:\n"
                        "- Read your recent emails (e.g., 'show me my last 5 emails')\n"
                        "- Generate AI-powered replies (e.g., 'generate replies for my emails')\n"
                        "- Delete emails (e.g., 'delete email number 2' or 'delete the latest email from [sender]')\n\n"
                        "What would you like to do?",
                action="greeting"
            )
        elif "help" in user_message or "capabilities" in user_message:
            return ChatResponse(
                response="I can help you manage your emails:\n\n"
                        "📧 **Read Emails**: Ask me to show your recent emails\n"
                        "  Example: 'Show me my last 5 emails' or 'Read my emails'\n\n"
                        "✍️ **Generate Replies**: I can create professional replies for your emails\n"
                        "  Example: 'Generate replies for my emails' or 'Create a reply for email 1'\n\n"
                        "🗑️ **Delete Emails**: I can delete specific emails\n"
                        "  Example: 'Delete email number 2' or 'Delete the latest email from john@example.com'\n\n"
                        "Just tell me what you'd like to do in natural language!",
                action="help"
            )
        else:
            return ChatResponse(
                response="I'm not sure what you'd like to do. Try asking me to:\n"
                        "- Read your emails\n"
                        "- Generate replies\n"
                        "- Delete an email\n"
                        "Or type 'help' to see all capabilities.",
                action="unknown"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


async def handle_read_emails(session_id: str, parameters: Dict) -> ChatResponse:
    """Handle read emails command"""
    try:
        service = get_gmail_service(session_id)
        max_results = parameters.get("max_results", 5)
        
        # Get message list
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return ChatResponse(
                response="You don't have any recent emails in your inbox.",
                action="read",
                data={"emails": []}
            )
        
        emails = []
        response_text = f"Here are your last {len(messages)} emails:\n\n"
        
        for idx, msg in enumerate(messages, 1):
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
                
                sender_name, sender_email = parseaddr(sender)
                if not sender_name:
                    sender_name = sender_email
                
                body = decode_email_body(message)
                
                # Generate AI summary
                summary = await generate_email_summary(body, subject, sender_name)
                
                email_data = {
                    "id": msg['id'],
                    "thread_id": message.get('threadId'),
                    "sender": sender_name,
                    "sender_email": sender_email,
                    "subject": subject,
                    "date": date,
                    "summary": summary,
                    "snippet": message.get('snippet', '')
                }
                emails.append(email_data)
                
                response_text += f"**Email {idx}:**\n"
                response_text += f"From: {sender_name} ({sender_email})\n"
                response_text += f"Subject: {subject}\n"
                response_text += f"Summary: {summary}\n\n"
                
            except Exception as e:
                logger.error(f"Error processing email {msg.get('id')}: {str(e)}")
                continue
        
        return ChatResponse(
            response=response_text,
            action="read",
            data={"emails": emails}
        )
        
    except Exception as e:
        logger.error(f"Error reading emails: {str(e)}")
        return ChatResponse(
            response=f"Sorry, I couldn't read your emails. Error: {str(e)}",
            action="read",
            data={"error": str(e)}
        )


async def handle_generate_replies(session_id: str, parameters: Dict) -> ChatResponse:
    """Handle generate replies command"""
    try:
        service = get_gmail_service(session_id)
        
        # First, get recent emails if email_ids not specified
        email_ids = parameters.get("email_ids", [])
        email_number = parameters.get("email_number")
        
        if email_number:
            # Get the specific email
            results = service.users().messages().list(
                userId='me',
                maxResults=email_number
            ).execute()
            messages = results.get('messages', [])
            if messages and len(messages) >= email_number:
                email_ids = [messages[email_number - 1]['id']]
        
        if not email_ids:
            # Get last 5 emails by default
            results = service.users().messages().list(
                userId='me',
                maxResults=5
            ).execute()
            messages = results.get('messages', [])
            email_ids = [msg['id'] for msg in messages]
        
        if not email_ids:
            return ChatResponse(
                response="No emails found to generate replies for.",
                action="reply"
            )
        
        replies = []
        response_text = "Here are the generated replies:\n\n"
        
        for email_id in email_ids:
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
                
                sender_name, sender_email = parseaddr(sender)
                
                replies.append({
                    "email_id": email_id,
                    "original_subject": subject,
                    "original_sender": sender_name or sender_email,
                    "reply": reply_text
                })
                
                response_text += f"**Reply for: {subject}**\n"
                response_text += f"From: {sender_name or sender_email}\n"
                response_text += f"Reply:\n{reply_text}\n\n"
                
            except Exception as e:
                logger.error(f"Error generating reply for {email_id}: {str(e)}")
                continue
        
        return ChatResponse(
            response=response_text,
            action="reply",
            data={"replies": replies}
        )
        
    except Exception as e:
        logger.error(f"Error generating replies: {str(e)}")
        return ChatResponse(
            response=f"Sorry, I couldn't generate replies. Error: {str(e)}",
            action="reply",
            data={"error": str(e)}
        )


async def handle_delete_email(session_id: str, parameters: Dict) -> ChatResponse:
    """Handle delete email command"""
    try:
        service = get_gmail_service(session_id)
        
        email_id = parameters.get("email_id")
        email_number = parameters.get("email_number")
        sender = parameters.get("sender")
        subject_keyword = parameters.get("subject_keyword")
        
        # Find the email to delete
        if email_id:
            target_email_id = email_id
        elif email_number:
            # Get the specific email by number
            results = service.users().messages().list(
                userId='me',
                maxResults=email_number
            ).execute()
            messages = results.get('messages', [])
            if not messages or len(messages) < email_number:
                return ChatResponse(
                    response=f"Email number {email_number} not found.",
                    action="delete"
                )
            target_email_id = messages[email_number - 1]['id']
        elif sender:
            # Search by sender
            query = f"from:{sender}"
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            messages = results.get('messages', [])
            if not messages:
                return ChatResponse(
                    response=f"No emails found from {sender}.",
                    action="delete"
                )
            target_email_id = messages[0]['id']
        elif subject_keyword:
            # Search by subject
            query = f'subject:"{subject_keyword}"'
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            messages = results.get('messages', [])
            if not messages:
                return ChatResponse(
                    response=f"No emails found with subject containing '{subject_keyword}'.",
                    action="delete"
                )
            target_email_id = messages[0]['id']
        else:
            return ChatResponse(
                response="Please specify which email to delete. You can delete by:\n"
                        "- Email number (e.g., 'delete email 2')\n"
                        "- Sender (e.g., 'delete email from john@example.com')\n"
                        "- Subject keyword (e.g., 'delete email with subject meeting')",
                action="delete"
            )
        
        # Get email info before deleting
        try:
            message = service.users().messages().get(
                userId='me',
                id=target_email_id,
                format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()
            headers = message['payload'].get('headers', [])
            subject = get_header(headers, 'Subject')
            sender = get_header(headers, 'From')
        except:
            subject = "Unknown"
            sender = "Unknown"
        
        # Delete the email
        service.users().messages().delete(
            userId='me',
            id=target_email_id
        ).execute()
        
        return ChatResponse(
            response=f"✅ Successfully deleted email:\n"
                    f"Subject: {subject}\n"
                    f"From: {sender}",
            action="delete",
            data={"deleted_email_id": target_email_id}
        )
        
    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        return ChatResponse(
            response=f"Sorry, I couldn't delete the email. Error: {str(e)}",
            action="delete",
            data={"error": str(e)}
        )


@router.get("/greeting")
async def get_greeting(
    session_id: str = Header(..., alias="X-Session-Id")
):
    """Get initial greeting message with user info"""
    try:
        from app.models import get_session
        from datetime import datetime
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
        from googleapiclient.discovery import build
        from app.config import settings
        
        session = get_session(session_id)
        
        if not session or session.expires_at < datetime.utcnow():
            return {
                "greeting": "Hello! I'm your AI email assistant. How can I help you today?",
                "user": None
            }
        
        try:
            credentials = Credentials(
                token=session.access_token,
                refresh_token=session.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret
            )
            
            if credentials.expired:
                credentials.refresh(GoogleRequest())
            
            user_info_service = build('oauth2', 'v2', credentials=credentials)
            user_info = user_info_service.userinfo().get().execute()
            
            greeting = f"Hello {user_info.get('name', 'there')}! 👋\n\n"
            greeting += "I'm your AI email assistant. I can help you:\n"
            greeting += "• Read your recent emails with AI summaries\n"
            greeting += "• Generate professional email replies\n"
            greeting += "• Delete specific emails\n\n"
            greeting += "Just tell me what you'd like to do in natural language!"
            
            return {
                "greeting": greeting,
                "user": {
                    "email": user_info.get('email'),
                    "name": user_info.get('name'),
                    "picture": user_info.get('picture')
                }
            }
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return {
                "greeting": "Hello! I'm your AI email assistant. How can I help you today?",
                "user": None
            }
            
    except Exception as e:
        logger.error(f"Error getting greeting: {str(e)}")
        return {
            "greeting": "Hello! I'm your AI email assistant. How can I help you today?",
            "user": None
        }

