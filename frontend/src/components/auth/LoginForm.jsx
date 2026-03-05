/**
 * LoginForm component with VISION Design System styling.
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { validateEmail } from '../../services/authService';
import ForgotPasswordForm from './ForgotPasswordForm';

const LoginForm = ({ onSuccess, onSwitchToRegister }) => {
  const { login, error: authError, clearError } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    if (!password) {
      newErrors.password = 'Password is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const result = await login(email, password);
      if (result.success && onSuccess) {
        onSuccess(result.user);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show forgot password form if requested
  if (showForgotPassword) {
    return (
      <ForgotPasswordForm 
        onBack={() => setShowForgotPassword(false)}
        onSuccess={() => {}}
      />
    );
  }

  return (
    <div className="login-form-container">
      <div className="form-header">
        {/* Requirement 8.1: VISION logo at 28px SemiBold in brand color */}
        <h1 className="vision-logo" data-testid="vision-logo">VISION</h1>
        <p className="text-body form-subtitle">Sign in to continue to your dashboard</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="form-group">
          {/* Requirement 8.2: Labels at 12px Medium grey */}
          <label htmlFor="login-email" className="text-label form-label">Username</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </span>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setErrors(p => ({...p, email: null})); }}
              className={`form-input ${errors.email ? 'input-error' : ''}`}
              placeholder="name@company.com"
              autoComplete="email"
              disabled={isSubmitting}
            />
          </div>
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <div className="form-group">
          {/* Requirement 8.2: Labels at 12px Medium grey */}
          <label htmlFor="login-password" className="text-label form-label">Password</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors(p => ({...p, password: null})); }}
              className={`form-input ${errors.password ? 'input-error' : ''}`}
              placeholder="Enter your password"
              autoComplete="current-password"
              disabled={isSubmitting}
            />
          </div>
          {errors.password && <span className="error-message">{errors.password}</span>}
        </div>

        {authError && <div className="auth-error" role="alert">{authError}</div>}

        {/* Requirement 8.3: Log In button at 14px Medium with white text on brand color */}
        <button 
          type="submit" 
          className="login-submit-button btn-primary" 
          data-testid="login-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Signing in...' : 'Log In'}
        </button>
      </form>

      {/* Requirement 8.4: Secondary actions at 12px Regular */}
      <div className="form-footer">
        <p className="text-small secondary-action" data-testid="signup-link">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToRegister} className="link-button" disabled={isSubmitting}>
            Sign up
          </button>
        </p>
        <p className="text-small secondary-action" data-testid="forgot-password-link">
          <button 
            type="button" 
            className="link-button" 
            disabled={isSubmitting}
            onClick={() => setShowForgotPassword(true)}
          >
            Forgot password?
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginForm;
