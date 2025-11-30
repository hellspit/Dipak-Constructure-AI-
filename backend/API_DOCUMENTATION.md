# API Documentation

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-backend-url.com`

## Authentication

All endpoints (except auth endpoints) require a valid session. Include the session ID in the request header:
```
X-Session-Id: <session_id>
```

---

## API Endpoints

### 1. Authentication Endpoints

#### 1.1 Initiate Google OAuth
**GET** `/api/auth/google`

Initiates the Google OAuth flow.

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random-state-string"
}
```

**Usage:**
- Frontend redirects user to `authorization_url`
- User grants permissions
- Google redirects to callback endpoint

---

#### 1.2 OAuth Callback
**GET** `/api/auth/callback/google?code=<code>&state=<state>`

Handles the OAuth callback from Google.

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: State parameter for security

**Response:**
- Redirects to frontend dashboard with session ID

---

#### 1.3 Get Session Info
**GET** `/api/auth/session/{session_id}`

Get session information.

**Response:**
```json
{
  "session_id": "session-id-string",
  "user_email": "user@example.com",
  "expires_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404`: Session not found
- `401`: Session expired

---

#### 1.4 Get User Profile
**GET** `/api/auth/user/{session_id}`

Get user profile information from Google.

**Response:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/..."
}
```

**Error Responses:**
- `404`: Session not found
- `401`: Session expired or invalid

---

### 2. Email Endpoints

#### 2.1 List Recent Emails
**GET** `/api/email/list?max_results=5`

Get list of recent emails with AI-generated summaries.

**Headers:**
- `X-Session-Id`: Session ID (required)

**Query Parameters:**
- `max_results` (optional): Number of emails to retrieve (default: 5)

**Response:**
```json
{
  "emails": [
    {
      "id": "email-id",
      "thread_id": "thread-id",
      "sender": "John Doe",
      "sender_email": "john@example.com",
      "subject": "Meeting Tomorrow",
      "date": "Mon, 1 Jan 2024 10:00:00 -0800",
      "body": "Email body text...",
      "summary": "AI-generated summary of the email",
      "snippet": "Email snippet..."
    }
  ]
}
```

---

#### 2.2 Generate Email Replies
**POST** `/api/email/reply/generate`

Generate AI-powered replies for specified emails.

**Headers:**
- `X-Session-Id`: Session ID (required)
- `Content-Type`: application/json

**Request Body:**
```json
{
  "email_ids": ["email-id-1", "email-id-2"]
}
```

**Response:**
```json
{
  "replies": [
    {
      "email_id": "email-id-1",
      "original_subject": "Meeting Tomorrow",
      "original_sender": "John Doe <john@example.com>",
      "reply": "Generated reply text..."
    }
  ]
}
```

---

#### 2.3 Send Reply
**POST** `/api/email/reply/send`

Send a generated reply via Gmail.

**Headers:**
- `X-Session-Id`: Session ID (required)
- `Content-Type`: application/json

**Request Body:**
```json
{
  "email_id": "email-id-to-reply-to",
  "reply_text": "Your reply message here"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "sent-message-id",
  "message": "Email sent successfully"
}
```

---

#### 2.4 Delete Email
**DELETE** `/api/email/delete/{email_id}`

Delete a specific email.

**Headers:**
- `X-Session-Id`: Session ID (required)

**Path Parameters:**
- `email_id`: Gmail message ID

**Response:**
```json
{
  "success": true,
  "message": "Email deleted successfully"
}
```

---

#### 2.5 Search Emails
**POST** `/api/email/search`

Search emails by query (sender, subject, etc.).

**Headers:**
- `X-Session-Id`: Session ID (required)
- `Content-Type`: application/json

**Request Body:**
```json
{
  "query": "from:john@example.com subject:meeting",
  "max_results": 5
}
```

**Query Examples:**
- `from:john@example.com` - Emails from specific sender
- `subject:meeting` - Emails with subject containing "meeting"
- `is:unread` - Unread emails

**Response:**
```json
{
  "emails": [
    {
      "id": "email-id",
      "sender": "John Doe",
      "sender_email": "john@example.com",
      "subject": "Meeting",
      "date": "Mon, 1 Jan 2024 10:00:00 -0800",
      "snippet": "Email snippet..."
    }
  ]
}
```

---

### 3. Chatbot Endpoints

#### 3.1 Process Chat Message
**POST** `/api/chatbot/message`

Process natural language chat messages and execute email operations.

**Headers:**
- `Content-Type`: application/json

**Request Body:**
```json
{
  "message": "Show me my last 5 emails",
  "session_id": "session-id"
}
```

**Response:**
```json
{
  "response": "Here are your last 5 emails:\n\n**Email 1:**\nFrom: John Doe (john@example.com)\nSubject: Meeting Tomorrow\nSummary: AI-generated summary...",
  "action": "read",
  "data": {
    "emails": [...]
  }
}
```

**Supported Commands:**
- **Read emails**: "Show me my emails", "Read my last 5 emails", "List my emails"
- **Generate replies**: "Generate replies", "Create replies for my emails", "Reply to email 1"
- **Delete emails**: "Delete email 2", "Delete the latest email from john@example.com", "Delete email with subject meeting"
- **Greetings**: "Hello", "Hi", "Hey"
- **Help**: "Help", "What can you do", "Capabilities"

---

#### 3.2 Get Greeting
**GET** `/api/chatbot/greeting`

Get initial greeting message with user information.

**Headers:**
- `X-Session-Id`: Session ID (required)

**Response:**
```json
{
  "greeting": "Hello John Doe! 👋\n\nI'm your AI email assistant...",
  "user": {
    "email": "user@example.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/..."
  }
}
```

---

### 4. Health & Status Endpoints

#### 4.1 Root Endpoint
**GET** `/`

Get API information.

**Response:**
```json
{
  "message": "Email Assistant API",
  "version": "1.0.0",
  "status": "running"
}
```

---

#### 4.2 Health Check
**GET** `/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired session"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, there are no rate limits implemented. For production, consider implementing rate limiting based on:
- API key
- Session ID
- IP address

---

## Gmail API Scopes

The application requires the following Gmail API scopes:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Delete emails
- `https://www.googleapis.com/auth/userinfo.email` - User email
- `https://www.googleapis.com/auth/userinfo.profile` - User profile

---

## Notes

1. **Session Management**: Sessions are stored in the database and expire based on OAuth token expiration. Sessions are automatically refreshed when possible.

2. **AI Integration**: The API uses Groq's fast LLM models (llama-3.1-70b-versatile) for:
   - Email summarization
   - Reply generation
   - Natural language command parsing

3. **Email Body Decoding**: The API automatically handles base64-encoded email bodies and converts HTML emails to plain text when needed.

4. **Error Handling**: All endpoints include comprehensive error handling and logging.

5. **CORS**: The API is configured to accept requests from the frontend URL specified in `FRONTEND_URL` environment variable.


