'use client';

import React from 'react';
import { Email, Reply } from '@/lib/api';

interface ChatMessageProps {
    message: string;
    isUser: boolean;
    timestamp?: Date;
    emails?: Email[];
    replies?: Reply[];
    onSendReply?: (emailId: string, replyText: string) => void;
    isSendingReply?: boolean;
}

export default function ChatMessage({
    message,
    isUser,
    timestamp,
    emails,
    replies,
    onSendReply,
    isSendingReply = false,
}: ChatMessageProps) {
    return (
        <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${isUser
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                    }`}
            >
                <div className="whitespace-pre-wrap break-words">{message}</div>

                {emails && emails.length > 0 && (
                    <div className="mt-4 space-y-3 border-t border-gray-300 pt-3 dark:border-gray-600">
                        {emails.map((email, index) => (
                            <div
                                key={email.id}
                                className="rounded-lg bg-white p-3 text-sm text-gray-800 shadow-sm dark:bg-gray-800 dark:text-gray-200"
                            >
                                <div className="mb-2 font-semibold">
                                    Email {index + 1}: {email.subject}
                                </div>
                                <div className="mb-1 text-xs text-gray-600 dark:text-gray-400">
                                    From: {email.sender} ({email.sender_email})
                                </div>
                                <div className="mb-2 text-xs text-gray-600 dark:text-gray-400">
                                    Date: {new Date(email.date).toLocaleString()}
                                </div>
                                {email.summary && (
                                    <div className="mt-2 rounded bg-gray-50 p-2 text-xs dark:bg-gray-900">
                                        <div className="font-medium">Summary:</div>
                                        <div className="mt-1">{email.summary}</div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {replies && replies.length > 0 && (
                    <div className="mt-4 space-y-3 border-t border-gray-300 pt-3 dark:border-gray-600">
                        {replies.map((reply, index) => (
                            <div
                                key={reply.email_id}
                                className="rounded-lg bg-white p-3 text-sm text-gray-800 shadow-sm dark:bg-gray-800 dark:text-gray-200"
                            >
                                <div className="mb-2 font-semibold">
                                    Reply {index + 1} to: {reply.original_subject}
                                </div>
                                <div className="mb-2 text-xs text-gray-600 dark:text-gray-400">
                                    Original from: {reply.original_sender}
                                </div>
                                <div className="mt-2 rounded bg-blue-50 p-2 text-xs dark:bg-blue-900/20">
                                    <div className="font-medium">Suggested Reply:</div>
                                    <div className="mt-1 whitespace-pre-wrap">{reply.reply}</div>
                                </div>
                                {onSendReply && (
                                    <button
                                        onClick={() => onSendReply(reply.email_id, reply.reply)}
                                        disabled={isSendingReply}
                                        className="mt-3 w-full rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        {isSendingReply ? 'Sending...' : 'Send Reply'}
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {timestamp && (
                    <div className={`mt-2 text-xs ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                        {timestamp.toLocaleTimeString()}
                    </div>
                )}
            </div>
        </div>
    );
}

