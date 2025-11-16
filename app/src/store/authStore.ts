import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthStore, User, AuthResponse } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            if (response.status === 401) {
              throw new Error('Invalid email or password');
            } else if (response.status === 400) {
              throw new Error('Please check your input and try again');
            } else if (response.status >= 500) {
              throw new Error('Something went wrong. Please try again later.');
            }

            throw new Error(errorData.detail || 'Login failed');
          }

          const data: AuthResponse = await response.json();

          // Store token in localStorage
          localStorage.setItem('auth-token', data.token);

          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Login failed';
          set({ isLoading: false, error: errorMessage });
          throw error;
        }
      },

      signup: async (email: string, password: string, passwordConfirmation: string) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email,
              password,
              password_confirmation: passwordConfirmation,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            if (response.status === 409) {
              throw new Error('Email already in use');
            } else if (response.status === 400) {
              throw new Error('Please check your input and try again');
            } else if (response.status >= 500) {
              throw new Error('Something went wrong. Please try again later.');
            }

            throw new Error(errorData.detail || 'Signup failed');
          }

          const data: AuthResponse = await response.json();

          // Store token in localStorage
          localStorage.setItem('auth-token', data.token);

          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Signup failed';
          set({ isLoading: false, error: errorMessage });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('auth-token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      clearError: () => {
        set({ error: null });
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },

      setToken: (token: string | null) => {
        if (token) {
          localStorage.setItem('auth-token', token);
        } else {
          localStorage.removeItem('auth-token');
        }
        set({ token, isAuthenticated: !!token });
      },
    }),
    {
      name: 'zapcut-auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
