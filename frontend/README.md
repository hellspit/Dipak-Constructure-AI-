# Email Assistant Frontend

AI-powered email assistant frontend built with Next.js, React, and TypeScript.

## Features

- **Google OAuth Authentication**: Secure login with Google OAuth2
- **AI Chatbot Dashboard**: Interactive chat interface for email management
- **Email Operations**: 
  - Read and summarize emails
  - Generate AI-powered replies
  - Delete emails based on natural language commands
- **Modern UI**: Clean, responsive design with dark mode support

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Backend API running (see backend README)

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Create a `.env.local` file in the frontend directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, set `NEXT_PUBLIC_API_URL` to your backend URL.

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

### Build

Build for production:

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js app router pages
│   │   ├── login/        # Login page
│   │   ├── dashboard/    # Main chatbot dashboard
│   │   ├── layout.tsx    # Root layout with AuthProvider
│   │   └── page.tsx      # Home page (redirects)
│   ├── components/       # React components
│   │   ├── ChatMessage.tsx
│   │   └── ChatInput.tsx
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   └── lib/              # Utilities
│       └── api.ts        # API client
```

## Usage

1. **Login**: Navigate to the app and click "Sign in with Google"
2. **Grant Permissions**: Authorize Gmail access (read, send, delete)
3. **Chat**: Use natural language to interact:
   - "Show me my last 5 emails"
   - "Generate replies for my emails"
   - "Delete email number 2"
   - "Delete the latest email from john@example.com"

## Deploy on Vercel

1. Push your code to GitHub
2. Import your repository in [Vercel](https://vercel.com)
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL`: Your backend API URL
4. Deploy!

The app will be available at `https://your-app-name.vercel.app`

## Tech Stack

- **Next.js 16**: React framework with App Router
- **React 19**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Geist Font**: Typography
