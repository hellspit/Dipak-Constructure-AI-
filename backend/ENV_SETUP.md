# Environment Variables Setup Guide

## Required Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here

# Groq API Configuration
GROQ_API_KEY=your-groq-api-key-here

# Secret Key for Session Management
SECRET_KEY=your-secret-key-here-generate-a-random-string

# Database Configuration
DATABASE_URL=sqlite:///./email_assistant.db

# Frontend URL (for CORS and redirects)
FRONTEND_URL=http://localhost:3000

# Backend URL (for deployment)
BACKEND_URL=http://localhost:8000
```

---

## Detailed Configuration

### 1. Google OAuth Configuration

**What you need:** `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

These credentials allow your app to authenticate users with Google and access their Gmail. Follow these steps:

#### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create or Select a Project**
   - Click the project dropdown at the top (next to "Google Cloud")
   - Click **"New Project"**
   - Enter a project name (e.g., "Email Assistant")
   - Click **"Create"**
   - Wait for the project to be created, then select it from the dropdown

#### Step 2: Enable Gmail API

1. **Navigate to API Library**
   - In the left sidebar, click **"APIs & Services"** > **"Library"**
   - Or go directly to: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)

2. **Search and Enable Gmail API**
   - In the search bar, type **"Gmail API"**
   - Click on **"Gmail API"** from the results
   - Click the **"Enable"** button
   - Wait for it to enable (you'll see a green checkmark)

#### Step 3: Configure OAuth Consent Screen

**Important:** You must configure the consent screen before creating credentials.

1. **Go to OAuth Consent Screen**
   - In the left sidebar, click **"APIs & Services"** > **"OAuth consent screen"**
   - Or go to: [https://console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)

2. **Configure Consent Screen**
   - **User Type:** Select **"External"** (for testing/development)
   - Click **"Create"**

3. **Fill in App Information**
   - **App name:** Enter your app name (e.g., "Email Assistant")
   - **User support email:** Select your email from dropdown
   - **Developer contact information:** Enter your email
   - Click **"Save and Continue"**

4. **Add Scopes**
   - Click **"Add or Remove Scopes"**
   - In the filter box, search for and select these scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Click **"Update"**
   - Click **"Save and Continue"**

5. **Add Test Users** (Required for testing)
   - Click **"Add Users"**
   - Add these test users:
     - `test@gmail.com` (required by assignment)
     - Your own email address (for testing)
   - Click **"Add"**
   - Click **"Save and Continue"**

6. **Review and Finish**
   - Review your settings
   - Click **"Back to Dashboard"**

#### Step 4: Create OAuth 2.0 Credentials

1. **Go to Credentials Page**
   - In the left sidebar, click **"APIs & Services"** > **"Credentials"**
   - Or go to: [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)

2. **Create OAuth Client ID**
   - Click **"+ CREATE CREDENTIALS"** at the top
   - Select **"OAuth client ID"**

3. **Configure OAuth Client**
   - **Application type:** Select **"Web application"**
   - **Name:** Enter a name (e.g., "Email Assistant Web Client")

4. **Add Authorized JavaScript Origins**
   - Click **"+ ADD URI"** for each:
     - `http://localhost:3000` (for local development)
     - `https://your-app-name.vercel.app` (for production - update with your actual Vercel URL)

5. **Add Authorized Redirect URIs**
   - Click **"+ ADD URI"** for each:
     - `http://localhost:8000/api/auth/callback/google` (backend callback - development)
     - `https://your-backend-url.com/api/auth/callback/google` (backend callback - production)
   
   **Important:** The redirect URI must point to your **backend** URL, not the frontend!

6. **Create and Copy Credentials**
   - Click **"Create"**
   - A popup will appear with your credentials:
     - **Your Client ID:** `123456789-abcdefghijklmnop.apps.googleusercontent.com`
     - **Your Client Secret:** `GOCSPX-abcdefghijklmnopqrstuvwxyz`
   - **Copy both values immediately** (you won't be able to see the secret again!)
   - Click **"OK"**

#### Step 5: Add Credentials to .env File

1. **Open your `.env` file** in the `backend/` directory

2. **Add the credentials:**
   ```env
   GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
   ```
   
   Replace the example values with your actual Client ID and Client Secret.

3. **Save the file**

#### Quick Reference: Where to Find Your Credentials Later

If you need to view your credentials again:
- Go to: [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
- Find your OAuth 2.0 Client ID in the list
- Click the edit icon (pencil) to view the Client ID
- **Note:** The Client Secret is only shown once when created. If you lose it, you'll need to create new credentials.

#### Troubleshooting

**"Redirect URI mismatch" error:**
- Make sure the redirect URI in Google Console exactly matches your backend URL
- For development: `http://localhost:8000/api/auth/callback/google`
- For production: `https://your-backend-url.com/api/auth/callback/google`

**"Access blocked" error:**
- Make sure you added yourself as a test user in OAuth consent screen
- Make sure the app is in "Testing" mode (not "In production")

---

### 2. Groq API Configuration

#### Step 1: Get API Key
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in with your account
3. Navigate to **API Keys** section
4. Click **Create API Key** or **Generate New Key**
5. Copy the key (you won't be able to see it again - save it securely)

#### Step 2: Add to .env
```env
GROQ_API_KEY=gsk_abcdefghijklmnopqrstuvwxyz1234567890
```

**Note**: The API uses Groq's fast LLM models (like llama-3.1-70b-versatile). Groq offers free tier with generous rate limits. Make sure you have sufficient quota.

---

### 3. Secret Key Generation

Generate a secure random string for session management:

**Using OpenSSL:**
```bash
openssl rand -hex 32
```

**Using Python:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**Using Node.js:**
```javascript
require('crypto').randomBytes(32).toString('hex')
```

Add to `.env`:
```env
SECRET_KEY=your-generated-secret-key-here
```

---

### 4. Database Configuration

#### SQLite (Default - Development)
```env
DATABASE_URL=sqlite:///./email_assistant.db
```

The database file will be created automatically in the `backend/` directory.

#### PostgreSQL (Production)
```env
DATABASE_URL=postgresql://username:password@localhost:5432/email_assistant
```

**Setup PostgreSQL:**
1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE email_assistant;
   ```
3. Update the connection string with your credentials

---

### 5. Frontend URL Configuration

#### Development
```env
FRONTEND_URL=http://localhost:3000
```

#### Production
```env
FRONTEND_URL=https://your-app-name.vercel.app
```

**Important**: This URL is used for:
- CORS configuration
- OAuth redirect URIs
- Session redirects

---

### 6. Backend URL Configuration

#### Development
```env
BACKEND_URL=http://localhost:8000
```

#### Production
```env
BACKEND_URL=https://your-backend-url.com
```

**Note**: Update this when deploying your backend to a service like:
- Railway
- Render
- Fly.io
- Heroku
- AWS/GCP/Azure

---

## Environment File Structure

Your `backend/.env` file should look like this:

```env
# ============================================
# Google OAuth Configuration
# ============================================
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz

# ============================================
# Groq API Configuration
# ============================================
GROQ_API_KEY=gsk_abcdefghijklmnopqrstuvwxyz1234567890

# ============================================
# Security
# ============================================
SECRET_KEY=your-generated-secret-key-minimum-32-characters

# ============================================
# Database
# ============================================
DATABASE_URL=sqlite:///./email_assistant.db

# ============================================
# URLs
# ============================================
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

---

## Production Environment Variables

For production deployment, set these environment variables in your hosting platform:

### Railway
1. Go to your project settings
2. Navigate to **Variables** tab
3. Add each variable

### Render
1. Go to your service settings
2. Navigate to **Environment** section
3. Add each variable

### Fly.io
```bash
fly secrets set GOOGLE_CLIENT_ID=your-value
fly secrets set GOOGLE_CLIENT_SECRET=your-value
fly secrets set GROQ_API_KEY=your-value
fly secrets set SECRET_KEY=your-value
fly secrets set DATABASE_URL=your-value
fly secrets set FRONTEND_URL=your-value
fly secrets set BACKEND_URL=your-value
```

---

## Verification

After setting up your `.env` file, verify the configuration:

1. **Check file exists:**
   ```bash
   ls backend/.env
   ```

2. **Test backend startup:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Check for errors:**
   - If you see "Settings validation error", check your `.env` file
   - Make sure all required variables are set
   - Verify no extra spaces or quotes around values

---

## Security Best Practices

1. **Never commit `.env` to version control**
   - Add `.env` to `.gitignore`
   - Use `.env.example` for documentation

2. **Use strong secret keys**
   - Minimum 32 characters
   - Random and unpredictable

3. **Rotate keys regularly**
   - Especially if exposed or compromised

4. **Use different keys for development and production**
   - Never use production keys in development

5. **Limit API key permissions**
   - Use least privilege principle
   - Monitor API usage

---

## Troubleshooting

### Issue: "Settings validation error"
**Solution**: Check that all required environment variables are set in `.env`

### Issue: "Invalid client ID"
**Solution**: Verify `GOOGLE_CLIENT_ID` matches your Google Cloud Console credentials

### Issue: "Groq API error"
**Solution**: 
- Verify `GROQ_API_KEY` is correct
- Check your Groq account has sufficient quota
- Verify API key hasn't been revoked
- Check Groq API status at https://status.groq.com/

### Issue: "Database connection error"
**Solution**: 
- For SQLite: Check file permissions
- For PostgreSQL: Verify connection string and database exists

### Issue: "CORS error"
**Solution**: Verify `FRONTEND_URL` matches your actual frontend URL

---

## Next Steps

After setting up your environment variables:

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Run database migrations (automatic on first run)
3. ✅ Start the backend server
4. ✅ Test the API endpoints
5. ✅ Configure frontend to connect to backend

For more information, see:
- [API Documentation](./API_DOCUMENTATION.md)
- [README.md](../README.md)


