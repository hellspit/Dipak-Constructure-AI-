from groq import Groq
from app.config import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)


async def generate_email_summary(email_body: str, subject: str, sender: str) -> str:
    """Generate AI summary of an email"""
    try:
        prompt = f"""Summarize the following email in 2-3 sentences. Be concise and highlight the key points.

From: {sender}
Subject: {subject}
Body: {email_body[:1000]}

Summary:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes emails concisely."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating email summary: {error_msg}")
        # If model is decommissioned, suggest alternative
        if "decommissioned" in error_msg.lower() or "model" in error_msg.lower():
            logger.warning("Model may be unavailable. Consider updating to llama-3.1-8b-instant or mixtral-8x7b-32768")
        return f"Summary unavailable. Subject: {subject}"


async def generate_email_reply(original_email: Dict, context: str = "") -> str:
    """Generate AI-powered reply to an email"""
    try:
        sender = original_email.get('sender', 'Unknown')
        subject = original_email.get('subject', 'No Subject')
        body = original_email.get('body', '')
        
        prompt = f"""Generate a professional and contextually appropriate email reply. The reply should be:
- Professional and courteous
- Contextually aware of the original email
- Ready to send (complete and well-formatted)
- Appropriate in tone

Original Email:
From: {sender}
Subject: {subject}
Body: {body[:1500]}

{context}

Generate a professional reply:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional email assistant that writes clear, contextually appropriate email replies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating email reply: {str(e)}")
        return "I apologize, but I'm unable to generate a reply at this time. Please try again later."


async def parse_natural_language_command(command: str) -> Dict:
    """Parse natural language command to determine intent"""
    try:
        prompt = f"""Analyze the following user command and determine the intent. Return JSON with:
- action: "read", "reply", "delete", or "unknown"
- parameters: relevant parameters like sender, subject, email_number, etc.

Command: "{command}"

Return only valid JSON:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a command parser. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error parsing command: {str(e)}")
        return {"action": "unknown", "parameters": {}}


async def generate_daily_digest(emails: List[Dict]) -> str:
    """Generate a daily digest of emails"""
    try:
        emails_text = "\n\n".join([
            f"From: {e.get('sender', 'Unknown')}\nSubject: {e.get('subject', 'No Subject')}\n{e.get('summary', e.get('body', '')[:200])}"
            for e in emails[:20]
        ])
        
        prompt = f"""Create a daily email digest summarizing the key emails and suggesting actions or follow-ups.

Emails:
{emails_text}

Generate a concise daily digest with:
1. Key emails summary
2. Suggested actions or follow-ups

Digest:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates email digests."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error generating digest: {str(e)}")
        return "Unable to generate digest at this time."


async def categorize_emails(emails: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize emails into groups"""
    try:
        emails_text = "\n\n".join([
            f"{i+1}. From: {e.get('sender', 'Unknown')}\n   Subject: {e.get('subject', 'No Subject')}\n   Summary: {e.get('summary', e.get('body', '')[:200])}"
            for i, e in enumerate(emails)
        ])
        
        prompt = f"""Categorize the following emails into groups: Work, Promotions, Personal, Urgent, or Other.
Return JSON with categories as keys and arrays of email numbers (1-indexed) as values.

Emails:
{emails_text}

Return only valid JSON:"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that categorizes emails. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        import json
        categories = json.loads(response.choices[0].message.content)
        
        # Map back to actual emails
        result = {}
        for category, indices in categories.items():
            result[category] = [emails[int(i)-1] for i in indices if 1 <= int(i) <= len(emails)]
        
        return result
    except Exception as e:
        logger.error(f"Error categorizing emails: {str(e)}")
        return {"Other": emails}

