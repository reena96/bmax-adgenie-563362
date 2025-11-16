import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SignupPage from '../SignupPage';
import { useAuthStore } from '../../store/authStore';

// Mock the auth store
vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('SignupPage', () => {
  const mockSignup = vi.fn();
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthStore).mockReturnValue({
      signup: mockSignup,
      isLoading: false,
      error: null,
      clearError: mockClearError,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      setToken: vi.fn(),
      user: null,
      token: null,
    });
  });

  const renderSignupPage = () => {
    return render(
      <BrowserRouter>
        <SignupPage />
      </BrowserRouter>
    );
  };

  it('should render signup form', () => {
    renderSignupPage();

    expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email address')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText('Password (min. 8 characters)')
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Confirm password')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /create account/i })
    ).toBeInTheDocument();
  });

  it('should disable submit button when form is invalid', () => {
    renderSignupPage();

    const submitButton = screen.getByRole('button', { name: /create account/i });
    expect(submitButton).toBeDisabled();
  });

  it('should enable submit button when form is valid', async () => {
    renderSignupPage();

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText(
      'Password (min. 8 characters)'
    );
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm password');
    const submitButton = screen.getByRole('button', { name: /create account/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });

    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('should show password mismatch error', async () => {
    renderSignupPage();

    const passwordInput = screen.getByPlaceholderText(
      'Password (min. 8 characters)'
    );
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm password');

    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, {
      target: { value: 'differentpassword' },
    });

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  it('should call signup on valid form submission', async () => {
    mockSignup.mockResolvedValueOnce(undefined);
    renderSignupPage();

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText(
      'Password (min. 8 characters)'
    );
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm password');
    const submitButton = screen.getByRole('button', { name: /create account/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSignup).toHaveBeenCalledWith(
        'test@example.com',
        'password123',
        'password123'
      );
    });
  });

  it('should display error message for duplicate email', async () => {
    mockSignup.mockRejectedValueOnce(new Error('Email already in use'));

    renderSignupPage();

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText(
      'Password (min. 8 characters)'
    );
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm password');
    const submitButton = screen.getByRole('button', { name: /create account/i });

    fireEvent.change(emailInput, { target: { value: 'existing@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Email already in use')).toBeInTheDocument();
    });
  });

  it('should have link to login page', () => {
    renderSignupPage();

    const loginLink = screen.getByText('Log in');
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('should disable submit button for invalid email', async () => {
    renderSignupPage();

    const emailInput = screen.getByPlaceholderText('Email address');
    const passwordInput = screen.getByPlaceholderText(
      'Password (min. 8 characters)'
    );
    const confirmPasswordInput = screen.getByPlaceholderText('Confirm password');
    const submitButton = screen.getByRole('button', { name: /create account/i });

    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });
});
