// API client for backend communication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiError {
  detail: string;
}

export interface SessionInfo {
  session_id: string;
  user_email: string;
  expires_at: string;
}

export interface UserProfile {
  email: string;
  name: string;
  picture: string;
}

export interface Email {
  id: string;
  thread_id: string;
  sender: string;
  sender_email: string;
  subject: string;
  date: string;
  body: string;
  summary: string;
  snippet: string;
}

export interface EmailListResponse {
  emails: Email[];
}

export interface Reply {
  email_id: string;
  original_subject: string;
  original_sender: string;
  reply: string;
}

export interface ReplyGenerateResponse {
  replies: Reply[];
}

export interface ChatbotMessage {
  message: string;
  session_id: string;
}

export interface ChatbotResponse {
  response: string;
  action: string;
  data?: {
    emails?: Email[];
    replies?: Reply[];
  };
}

export interface GreetingResponse {
  greeting: string;
  user: UserProfile;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || 'An error occurred');
    }

    return response.json();
  }

  private requestWithSession<T>(
    endpoint: string,
    sessionId: string,
    options: RequestInit = {}
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      headers: {
        'X-Session-Id': sessionId,
        ...options.headers,
      },
    });
  }

  // Auth endpoints
  async initiateGoogleAuth(): Promise<{ authorization_url: string; state: string }> {
    return this.request('/api/auth/google');
  }

  async getSessionInfo(sessionId: string): Promise<SessionInfo> {
    return this.request(`/api/auth/session/${sessionId}`);
  }

  async getUserProfile(sessionId: string): Promise<UserProfile> {
    return this.requestWithSession(`/api/auth/user/${sessionId}`, sessionId);
  }

  // Email endpoints
  async listEmails(sessionId: string, maxResults: number = 5): Promise<EmailListResponse> {
    return this.requestWithSession(
      `/api/email/list?max_results=${maxResults}`,
      sessionId
    );
  }

  async generateReplies(sessionId: string, emailIds: string[]): Promise<ReplyGenerateResponse> {
    return this.requestWithSession('/api/email/reply/generate', sessionId, {
      method: 'POST',
      body: JSON.stringify({ email_ids: emailIds }),
    });
  }

  async sendReply(sessionId: string, emailId: string, replyText: string): Promise<{ success: boolean; message_id: string; message: string }> {
    return this.requestWithSession('/api/email/reply/send', sessionId, {
      method: 'POST',
      body: JSON.stringify({ email_id: emailId, reply_text: replyText }),
    });
  }

  async deleteEmail(sessionId: string, emailId: string): Promise<{ success: boolean; message: string }> {
    return this.requestWithSession(`/api/email/delete/${emailId}`, sessionId, {
      method: 'DELETE',
    });
  }

  async searchEmails(sessionId: string, query: string, maxResults: number = 5): Promise<EmailListResponse> {
    return this.requestWithSession('/api/email/search', sessionId, {
      method: 'POST',
      body: JSON.stringify({ query, max_results: maxResults }),
    });
  }

  // Chatbot endpoints
  async sendChatMessage(sessionId: string, message: string): Promise<ChatbotResponse> {
    return this.request('/api/chatbot/message', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  }

  async getGreeting(sessionId: string): Promise<GreetingResponse> {
    return this.requestWithSession('/api/chatbot/greeting', sessionId);
  }
}

export const apiClient = new ApiClient();

