import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Zap, Mail } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import GlassInput from '../components/glass/GlassInput';
import PrimaryButton from '../components/glass/PrimaryButton';
import SecondaryButton from '../components/glass/SecondaryButton';

const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { signup, isLoading, error, clearError, isAuthenticated } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [apiError, setApiError] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/brands');
    }
  }, [isAuthenticated, navigate]);

  // Email validation
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setEmailError('Email is required');
      return false;
    }
    if (!emailRegex.test(email)) {
      setEmailError('Please enter a valid email');
      return false;
    }
    setEmailError('');
    return true;
  };

  // Password validation
  const validatePassword = (password: string): boolean => {
    if (!password) {
      setPasswordError('Password is required');
      return false;
    }
    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  // Confirm password validation
  const validateConfirmPassword = (confirmPwd: string): boolean => {
    if (!confirmPwd) {
      setConfirmPasswordError('Please confirm your password');
      return false;
    }
    if (confirmPwd !== password) {
      setConfirmPasswordError('Passwords do not match');
      return false;
    }
    setConfirmPasswordError('');
    return true;
  };

  // Form validation
  const isFormValid = (): boolean => {
    return (
      email.trim() !== '' &&
      password.length >= 8 &&
      confirmPassword === password &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    );
  };

  // Handle input changes
  const handleEmailChange = (value: string) => {
    setEmail(value);
    setEmailError('');
    setApiError('');
    clearError();
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    setPasswordError('');
    // Re-validate confirm password if it's already filled
    if (confirmPassword) {
      if (value !== confirmPassword) {
        setConfirmPasswordError('Passwords do not match');
      } else {
        setConfirmPasswordError('');
      }
    }
    setApiError('');
    clearError();
  };

  const handleConfirmPasswordChange = (value: string) => {
    setConfirmPassword(value);
    if (value !== password) {
      setConfirmPasswordError('Passwords do not match');
    } else {
      setConfirmPasswordError('');
    }
    setApiError('');
    clearError();
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous errors
    setApiError('');
    clearError();

    // Validate inputs
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);
    const isConfirmPasswordValid = validateConfirmPassword(confirmPassword);

    if (!isEmailValid || !isPasswordValid || !isConfirmPasswordValid) {
      return;
    }

    try {
      await signup(email, password, confirmPassword);
      // Navigation handled by useEffect watching isAuthenticated
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Signup failed';
      setApiError(errorMessage);
    }
  };

  return (
    <div className="min-h-screen cosmic-gradient flex items-center justify-center px-6">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 text-white mb-6">
            <Zap className="w-8 h-8 text-lightning-yellow" />
            <span className="text-2xl font-bold">AdGenie</span>
          </Link>
          <h1 className="text-3xl font-bold text-white mt-4">Create Account</h1>
          <p className="text-white/60 mt-2">Start creating amazing video ads today</p>
        </div>

        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} noValidate>
            <div className="space-y-4">
              {/* API Error Message */}
              {(apiError || error) && (
                <div
                  className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm"
                  role="alert"
                >
                  {apiError || error}
                </div>
              )}

              {/* Email Input */}
              <GlassInput
                id="email"
                name="email"
                type="email"
                placeholder="Email address"
                value={email}
                onChange={handleEmailChange}
                error={emailError}
                icon={<Mail className="w-5 h-5" />}
                disabled={isLoading}
                autoComplete="email"
                required
                ariaLabel="Email address"
              />

              {/* Password Input */}
              <GlassInput
                id="password"
                name="password"
                type="password"
                placeholder="Password (min. 8 characters)"
                value={password}
                onChange={handlePasswordChange}
                error={passwordError}
                disabled={isLoading}
                autoComplete="new-password"
                required
                ariaLabel="Password"
              />

              {/* Confirm Password Input */}
              <GlassInput
                id="confirm-password"
                name="confirm-password"
                type="password"
                placeholder="Confirm password"
                value={confirmPassword}
                onChange={handleConfirmPasswordChange}
                error={confirmPasswordError}
                disabled={isLoading}
                autoComplete="new-password"
                required
                ariaLabel="Confirm password"
              />

              {/* Signup Button */}
              <PrimaryButton
                type="submit"
                disabled={!isFormValid()}
                isLoading={isLoading}
                className="w-full"
              >
                {isLoading ? 'Creating account...' : 'Create Account'}
              </PrimaryButton>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-white/50">OR</span>
                </div>
              </div>

              {/* Google OAuth Button */}
              <SecondaryButton
                type="button"
                onClick={() => {
                  // Placeholder for Google OAuth
                  console.log('Google OAuth not yet implemented');
                }}
                disabled={isLoading}
                className="w-full"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </SecondaryButton>
            </div>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-white/60">
              Already have an account?{' '}
              <Link to="/login" className="text-lightning-yellow hover:underline">
                Log in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
