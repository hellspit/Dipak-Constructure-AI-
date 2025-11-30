# Email Assistant - AI-Powered Gmail Automation

A full-stack AI-powered email assistant application built with FastAPI (backend) and React/Next.js (frontend). This application allows users to manage their Gmail inbox through natural language commands, with AI-powered email summarization and reply generation.

## Features

- 🔐 **Google OAuth Authentication** - Secure login with Gmail permissions
- 🤖 **AI Chatbot Interface** - Natural language email management
- 📧 **Email Reading** - Fetch and summarize recent emails with AI
- ✍️ **AI Reply Generation** - Context-aware email reply suggestions
- 🗑️ **Email Deletion** - Delete emails by sender, subject, or reference number
- 📊 **Clean Dashboard** - User-friendly chatbot interface

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Google Gmail API** - Email operations
- **Groq API** - AI-powered features (summaries, replies, command parsing)
- **SQLite/PostgreSQL** - Database

### Frontend
- **React** or **Next.js** - Frontend framework
- **Vercel** - Deployment platform

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── auth.py          # Google OAuth authentication
│   ├── email.py         # Gmail API operations
│   ├── chatbot.py       # Chatbot endpoint and natural language processing
│   ├── ai.py            # Groq AI integration
│   ├── models.py        # Database models
│   └── config.py        # Configuration and settings
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment variables
├── API_DOCUMENTATION.md # Detailed API documentation
├── ENV_SETUP.md         # Environment setup guide
└── README.md            # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Google Cloud Project with Gmail API enabled
- Groq API key

### Backend Setup

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
   
   See [ENV_SETUP.md](./ENV_SETUP.md) for detailed configuration instructions.

4. **Run the backend server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`
   
   API documentation: `http://localhost:8000/docs`

### Frontend Setup

The frontend should be set up in a separate directory. See the frontend repository for setup instructions.

## Environment Variables

Required environment variables (see `.env.example`):

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GROQ_API_KEY=your-groq-api-key
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./email_assistant.db
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

For detailed setup instructions, see [ENV_SETUP.md](./ENV_SETUP.md).

## API Endpoints

### Authentication
- `GET /api/auth/google` - Initiate Google OAuth
- `GET /api/auth/callback/google` - OAuth callback handler
- `GET /api/auth/session/{session_id}` - Get session info
- `GET /api/auth/user/{session_id}` - Get user profile

### Email Operations
- `GET /api/email/list` - List recent emails with AI summaries
- `POST /api/email/reply/generate` - Generate AI replies
- `POST /api/email/reply/send` - Send a reply email
- `DELETE /api/email/delete/{email_id}` - Delete an email
- `POST /api/email/search` - Search emails

### Chatbot
- `POST /api/chatbot/message` - Process natural language commands
- `GET /api/chatbot/greeting` - Get initial greeting with user info

For detailed API documentation, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md).

## Deployment

### Backend Deployment

The backend can be deployed to various platforms:

#### Railway
1. Connect your GitHub repository
2. Add environment variables in Railway dashboard
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### Render
1. Create a new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

#### Fly.io
```bash
fly launch
fly secrets set GOOGLE_CLIENT_ID=your-value
fly secrets set GOOGLE_CLIENT_SECRET=your-value
fly secrets set GROQ_API_KEY=your-value
fly secrets set SECRET_KEY=your-value
fly secrets set DATABASE_URL=your-value
fly secrets set FRONTEND_URL=your-value
fly secrets set BACKEND_URL=your-value
fly deploy
```

### Frontend Deployment (Vercel)

1. Connect your frontend repository to Vercel
2. Configure environment variables:
   - `NEXT_PUBLIC_BACKEND_URL` - Your backend URL
3. Deploy

**Important**: Update your Google OAuth redirect URIs to include:
- Backend callback: `https://your-backend-url.com/api/auth/callback/google`
- Frontend URL: `https://your-app-name.vercel.app`

### Google OAuth Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** > **Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add authorized redirect URIs:
   - Development: `http://localhost:8000/api/auth/callback/google`
   - Production: `https://your-backend-url.com/api/auth/callback/google`
5. Add test users: `test@gmail.com` (as required by assignment)

## Usage

1. **Login**: Click "Sign in with Google" and grant Gmail permissions
2. **Dashboard**: You'll see the chatbot interface with a greeting
3. **Read Emails**: Type "Show me my last 5 emails" or "Read my emails"
4. **Generate Replies**: Type "Generate replies for my emails" or "Create a reply for email 1"
5. **Delete Emails**: Type "Delete email number 2" or "Delete the latest email from sender@example.com"

## Testing

### Manual Testing

1. Start the backend server
2. Use the API documentation at `http://localhost:8000/docs` to test endpoints
3. Test the OAuth flow by initiating authentication
4. Test email operations with a valid session

### Test User

As per assignment requirements, add `test@gmail.com` as a test user in Google Cloud Console OAuth settings.

## Troubleshooting

### Common Issues

**"Settings validation error"**
- Check that all required environment variables are set in `.env`

**"Invalid client ID"**
- Verify `GOOGLE_CLIENT_ID` matches your Google Cloud Console credentials
- Check redirect URIs are correctly configured

**"Groq API error"**
- Verify `GROQ_API_KEY` is correct
- Check your Groq account has sufficient quota
- Visit https://console.groq.com/ to check your usage

**"CORS error"**
- Verify `FRONTEND_URL` matches your actual frontend URL
- Check CORS middleware configuration in `main.py`

**"Database connection error"**
- For SQLite: Check file permissions
- For PostgreSQL: Verify connection string and database exists

## Security Notes

- Never commit `.env` file to version control
- Use strong, random secret keys
- Use different keys for development and production
- Regularly rotate API keys
- Monitor API usage

## Assignment Requirements Checklist

- ✅ **Part 0 - Deployment**: Backend reachable, frontend on Vercel
- ✅ **Part 1 - Google Authentication**: OAuth2 with Gmail permissions, session management
- ✅ **Part 2 - Chatbot Dashboard**: AI interface with greeting and capabilities
- ✅ **Part 3.1 - Read Emails**: Fetch last 5 emails with AI summaries
- ✅ **Part 3.2 - Generate Replies**: AI-powered reply generation with send capability
- ✅ **Part 3.3 - Delete Emails**: Delete by sender, subject, or reference number

## License

This project is part of a technical assignment.

## Support

For issues or questions, refer to:
- [API Documentation](./API_DOCUMENTATION.md)
- [Environment Setup Guide](./ENV_SETUP.md)

