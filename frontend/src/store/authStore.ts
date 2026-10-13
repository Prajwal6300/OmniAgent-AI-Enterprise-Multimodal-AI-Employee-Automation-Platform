import { create } from 'zustand';
import { apiClient } from '@/services/api/client';

export interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  organization_id?: string;
  role?: string;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: AuthUser, token: string, refreshToken?: string) => void;
  clearAuth: () => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,

  setAuth: (user: AuthUser, token: string, refreshToken?: string) => {
    // Access token stored in memory only (not in localStorage) to prevent XSS theft
    // Store in a global so the API client interceptor can read it
    (window as any).__OMNIAUTH_ACCESS_TOKEN__ = token;
    set({
      user,
      token,
      refreshToken: refreshToken || get().refreshToken,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  clearAuth: () => {
    // Clear the in-memory access token
    (window as any).__OMNIAUTH_ACCESS_TOKEN__ = null;
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access_token, refresh_token, user } = response.data;
      get().setAuth(
        user || { id: 'current', email },
        access_token,
        refresh_token
      );
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    get().clearAuth();
    apiClient.post('/auth/logout').then(() => {
      // Refresh cookie cleared by backend on logout
    }).finally(() => {
      set({ isLoading: false });
    });
    window.location.href = '/login';
  },

  fetchCurrentUser: async () => {
    const token = (window as any).__OMNIAUTH_ACCESS_TOKEN__;
    if (!token) return;
    set({ isLoading: true });
    try {
      const response = await apiClient.get('/users/me');
      set({ user: response.data, isAuthenticated: true });
    } catch {
      get().clearAuth();
    } finally {
      set({ isLoading: false });
    }
  },
}));