import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../authStore';

// Mock fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch as typeof fetch;

describe('authStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });

    // Clear localStorage
    localStorage.clear();

    // Reset mocks
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should successfully log in a user', async () => {
      const mockResponse = {
        token: 'test-token-123',
        user: {
          id: '1',
          email: 'test@example.com',
          subscription_tier: 'free',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { login } = useAuthStore.getState();
      await login('test@example.com', 'password123');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockResponse.user);
      expect(state.token).toBe(mockResponse.token);
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(localStorage.getItem('auth-token')).toBe(mockResponse.token);
    });

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      });

      const { login } = useAuthStore.getState();

      await expect(login('test@example.com', 'wrongpassword')).rejects.toThrow(
        'Invalid email or password'
      );

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
    });
  });

  describe('signup', () => {
    it('should successfully sign up a user', async () => {
      const mockResponse = {
        token: 'test-token-456',
        user: {
          id: '2',
          email: 'newuser@example.com',
          subscription_tier: 'free',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { signup } = useAuthStore.getState();
      await signup('newuser@example.com', 'password123', 'password123');

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockResponse.user);
      expect(state.token).toBe(mockResponse.token);
      expect(state.isAuthenticated).toBe(true);
      expect(localStorage.getItem('auth-token')).toBe(mockResponse.token);
    });

    it('should handle 409 duplicate email error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ detail: 'Email exists' }),
      });

      const { signup } = useAuthStore.getState();

      await expect(
        signup('existing@example.com', 'password123', 'password123')
      ).rejects.toThrow('Email already in use');
    });
  });

  describe('logout', () => {
    it('should clear user data and token', () => {
      // Set initial state
      useAuthStore.setState({
        user: { id: '1', email: 'test@example.com', subscription_tier: 'free' },
        token: 'test-token',
        isAuthenticated: true,
      });
      localStorage.setItem('auth-token', 'test-token');

      const { logout } = useAuthStore.getState();
      logout();

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(localStorage.getItem('auth-token')).toBeNull();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useAuthStore.setState({ error: 'Some error' });

      const { clearError } = useAuthStore.getState();
      clearError();

      const state = useAuthStore.getState();
      expect(state.error).toBeNull();
    });
  });
});
