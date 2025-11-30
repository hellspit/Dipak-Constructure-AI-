'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, ChatbotResponse, Email, Reply } from '@/lib/api';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';

interface Message {
    text: string;
    isUser: boolean;
    timestamp: Date;
    emails?: Email[];
    replies?: Reply[];
}

export default function DashboardPage() {
    const { isAuthenticated, isLoading, sessionId, user, logout } = useAuth();
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoadingGreeting, setIsLoadingGreeting] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [isSendingReply, setIsSendingReply] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isLoading, isAuthenticated, router]);

    useEffect(() => {
        if (isAuthenticated && sessionId && messages.length === 0) {
            loadGreeting();
        }
    }, [isAuthenticated, sessionId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const loadGreeting = async () => {
        if (!sessionId) return;

        try {
            setIsLoadingGreeting(true);
            const greeting = await apiClient.getGreeting(sessionId);
            setMessages([
                {
                    text: greeting.greeting,
                    isUser: false,
                    timestamp: new Date(),
                },
            ]);
        } catch (error) {
            console.error('Failed to load greeting:', error);
            setMessages([
                {
                    text: 'Hello! I\'m your AI email assistant. How can I help you today?',
                    isUser: false,
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoadingGreeting(false);
        }
    };

    const handleSendMessage = async (messageText: string) => {
        if (!sessionId || isSending) return;

        // Add user message
        const userMessage: Message = {
            text: messageText,
            isUser: true,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setIsSending(true);

        try {
            const response: ChatbotResponse = await apiClient.sendChatMessage(
                sessionId,
                messageText
            );

            // Add AI response
            const aiMessage: Message = {
                text: response.response,
                isUser: false,
                timestamp: new Date(),
                emails: response.data?.emails,
                replies: response.data?.replies,
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            console.error('Failed to send message:', error);
            const errorMessage: Message = {
                text: 'Sorry, I encountered an error processing your request. Please try again.',
                isUser: false,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsSending(false);
        }
    };

    const handleSendReply = async (emailId: string, replyText: string) => {
        if (!sessionId || isSendingReply) return;

        setIsSendingReply(true);
        try {
            const result = await apiClient.sendReply(sessionId, emailId, replyText);

            // Add success message
            const successMessage: Message = {
                text: `✅ ${result.message}`,
                isUser: false,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, successMessage]);
        } catch (error) {
            console.error('Failed to send reply:', error);
            const errorMessage: Message = {
                text: '❌ Failed to send reply. Please try again.',
                isUser: false,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsSendingReply(false);
        }
    };

    if (isLoading || isLoadingGreeting) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-lg">Loading...</div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    return (
        <div className="flex h-screen flex-col bg-gray-50 dark:bg-gray-900">
            {/* Header */}
            <header className="border-b border-gray-200 bg-white px-6 py-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        {user?.picture && (
                            <img
                                src={user.picture}
                                alt={user.name}
                                className="h-10 w-10 rounded-full"
                            />
                        )}
                        <div>
                            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                                Email Assistant
                            </h1>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                {user?.name || user?.email}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={logout}
                        className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                    >
                        Logout
                    </button>
                </div>
            </header>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="mx-auto max-w-4xl space-y-4">
                    {messages.map((message, index) => (
                        <ChatMessage
                            key={index}
                            message={message.text}
                            isUser={message.isUser}
                            timestamp={message.timestamp}
                            emails={message.emails}
                            replies={message.replies}
                            onSendReply={handleSendReply}
                            isSendingReply={isSendingReply}
                        />
                    ))}
                    {isSending && (
                        <div className="flex justify-start">
                            <div className="rounded-lg bg-gray-100 px-4 py-3 dark:bg-gray-700">
                                <div className="flex gap-1">
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Chat Input */}
            <ChatInput
                onSend={handleSendMessage}
                disabled={isSending}
                placeholder="Ask me to read emails, generate replies, or delete messages..."
            />
        </div>
    );
}

