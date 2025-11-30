'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient, UserProfile, SessionInfo } from '@/lib/api';

interface AuthContextType {
    sessionId: string | null;
    user: UserProfile | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: () => Promise<void>;
    logout: () => void;
    checkSession: (sessionId: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [user, setUser] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for session ID in URL (from OAuth callback)
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        // Backend redirects with 'session' parameter
        const sessionIdFromUrl = params.get('session') || params.get('session_id');

        if (sessionIdFromUrl) {
            // Store session ID and clean URL
            localStorage.setItem('session_id', sessionIdFromUrl);
            setSessionId(sessionIdFromUrl);
            window.history.replaceState({}, '', window.location.pathname);
            checkSession(sessionIdFromUrl);
        } else {
            // Check for existing session in localStorage
            const storedSessionId = localStorage.getItem('session_id');
            if (storedSessionId) {
                checkSession(storedSessionId);
            } else {
                setIsLoading(false);
            }
        }
    }, []);

    const checkSession = useCallback(async (sessionIdToCheck: string): Promise<boolean> => {
        try {
            setIsLoading(true);

            // First check session info
            const sessionInfo = await apiClient.getSessionInfo(sessionIdToCheck);

            // Check if session is expired (backend already checks, but we do it here too for client-side validation)
            // Backend returns UTC time without timezone info, so we need to parse it as UTC
            let expiresAt: Date;
            const expiresAtStr = sessionInfo.expires_at;
            if (expiresAtStr.includes('Z') || expiresAtStr.includes('+') || expiresAtStr.includes('-', 10)) {
                // Has timezone info
                expiresAt = new Date(expiresAtStr);
            } else {
                // No timezone info, assume UTC and append 'Z'
                expiresAt = new Date(expiresAtStr + 'Z');
            }

            const now = new Date();
            // Add a small buffer (2 minutes) to account for clock skew
            const buffer = 2 * 60 * 1000; // 2 minutes in milliseconds
            if (expiresAt.getTime() < now.getTime() - buffer) {
                console.warn('Session expired (client-side check)', {
                    expiresAt: expiresAt.toISOString(),
                    now: now.toISOString(),
                    expiresAtStr
                });
                throw new Error('Session expired');
            }

            // Get user profile
            const userProfile = await apiClient.getUserProfile(sessionIdToCheck);

            setSessionId(sessionIdToCheck);
            setUser(userProfile);
            localStorage.setItem('session_id', sessionIdToCheck);
            return true;
        } catch (error: any) {
            console.error('Session check failed:', error);
            // Clear invalid session
            localStorage.removeItem('session_id');
            setSessionId(null);
            setUser(null);
            return false;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const login = useCallback(async () => {
        try {
            const { authorization_url } = await apiClient.initiateGoogleAuth();
            // Redirect to Google OAuth
            window.location.href = authorization_url;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem('session_id');
        setSessionId(null);
        setUser(null);
    }, []);

    const value: AuthContextType = {
        sessionId,
        user,
        isLoading,
        isAuthenticated: !!sessionId && !!user,
        login,
        logout,
        checkSession,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

