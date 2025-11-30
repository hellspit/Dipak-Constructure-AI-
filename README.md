# Constructure AI - Email Assistant

A mini-AI powered email assistant built with FastAPI and Next.js, featuring Google OAuth authentication, AI chatbot dashboard, and email automation capabilities.

## Features

- ✅ Google OAuth2 Authentication
- ✅ AI Chatbot Dashboard
- ✅ Read Last 5 Emails with AI Summaries
- ✅ Generate AI-Powered Email Responses
- ✅ Delete Specific Emails
- 🔄 Natural Language Command Understanding (Bonus)
- 🔄 Smart Inbox Grouping (Bonus)
- 🔄 Daily Digest (Bonus)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gmail API** - Email operations
- **OpenAI API** - AI-powered summaries and responses
- **SQLite/PostgreSQL** - Session management

### Frontend
- **Next.js** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling

### Deployment
- **Vercel** - Frontend deployment
- **Backend** - Deployable service (Railway/Render/Fly.io)

## Live URL

🚀 **Live Application**: https://your-app-name.vercel.app

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Cloud Project with Gmail API enabled
- OpenAI API key (or alternative AI provider)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key-for-sessions
DATABASE_URL=sqlite:///./email_assistant.db
FRONTEND_URL=http://localhost:3000
```

5. Run the backend server:
```bash
uvicorn main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

4. Run the development server:
```bash
npm run dev
```

### Google OAuth Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs:
     - `http://localhost:3000/api/auth/callback/google` (development)
     - `https://your-app-name.vercel.app/api/auth/callback/google` (production)
5. Add test user: `test@gmail.com` and `testingcheckuser1234@gmail.com`
6. Copy Client ID and Client Secret to your `.env` files

## Usage

1. Start both backend and frontend servers
2. Navigate to `http://localhost:3000`
3. Click "Sign in with Google"
4. Grant Gmail permissions
5. Use the chatbot to:
   - Read your last 5 emails: "Show me my recent emails"
   - Generate replies: "Generate replies for my emails"
   - Delete emails: "Delete the latest email from [sender]"

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── auth.py           # Google OAuth handling
│   │   ├── email.py          # Gmail API integration
│   │   ├── ai.py             # AI integration
│   │   └── models.py         # Data models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── lib/                  # Utilities
│   └── package.json
└── README.md
```

## Environment Variables

### Backend
- `GOOGLE_CLIENT_ID` - Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth Client Secret
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `SECRET_KEY` - Secret key for session encryption
- `DATABASE_URL` - Database connection string
- `FRONTEND_URL` - Frontend URL for CORS

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID` - Google OAuth Client ID

## Known Limitations

- Email operations require Gmail API permissions
- AI responses depend on OpenAI API availability
- Session management uses in-memory storage (consider Redis for production)

## License

This project is part of the Constructure AI technical assignment.

