'use client';

import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export default function ChatInput({
    onSend,
    disabled = false,
    placeholder = 'Type your message...',
}: ChatInputProps) {
    const [message, setMessage] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [message]);

    const handleSend = () => {
        if (message.trim() && !disabled) {
            onSend(message.trim());
            setMessage('');
            // Reset textarea height
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        }
    };

    const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="border-t border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            <div className="mx-auto max-w-4xl px-4 py-3">
                <div className="flex items-end gap-3">
                    <div className="flex-1 relative">
                        <textarea
                            ref={textareaRef}
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={handleKeyPress}
                            placeholder={placeholder}
                            disabled={disabled}
                            rows={1}
                            className="w-full resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-3 pr-12 text-sm leading-6 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder:text-gray-400 dark:focus:border-blue-400 dark:focus:bg-gray-700"
                            style={{ minHeight: '48px', maxHeight: '120px', overflowY: 'auto' }}
                        />
                        <div className="absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500">
                            Enter to send, Shift+Enter for new line
                        </div>
                    </div>
                    <button
                        onClick={handleSend}
                        disabled={disabled || !message.trim()}
                        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md transition-all hover:bg-blue-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-blue-600 disabled:hover:shadow-md dark:bg-blue-500 dark:hover:bg-blue-600"
                        title="Send message"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-5 w-5"
                        >
                            <path d="m22 2-7 20-4-9-9-4Z" />
                            <path d="M22 2 11 13" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}

