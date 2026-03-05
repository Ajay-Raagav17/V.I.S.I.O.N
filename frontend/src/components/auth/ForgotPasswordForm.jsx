/**
 * ForgotPasswordForm component for password reset requests.
 */

import { useState } from 'react';
import { validateEmail } from '../../services/authService';

const ForgotPasswordForm = ({ onBack, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        setSubmitted(true);
        if (onSuccess) onSuccess();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to send reset email');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="forgot-password-container">
        <div className="form-header">
          <h2 className="form-title">Check Your Email</h2>
          <p className="form-subtitle">
            If an account exists with {email}, we've sent password reset instructions.
          </p>
        </div>
        <div className="success-message">
          <span className="success-icon">✓</span>
          <p>Please check your inbox and follow the link to reset your password.</p>
        </div>
        <button type="button" onClick={onBack} className="link-button back-link">
          ← Back to Login
        </button>
      </div>
    );
  }

  return (
    <div className="forgot-password-container">
      <div className="form-header">
        <h2 className="form-title">Forgot Password?</h2>
        <p className="form-subtitle">
          Enter your email address and we'll send you instructions to reset your password.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="form-group">
          <label htmlFor="reset-email" className="form-label">Email Address</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </span>
            <input
              id="reset-email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(''); }}
              className={`form-input ${error ? 'input-error' : ''}`}
              placeholder="name@company.com"
              autoComplete="email"
              disabled={isSubmitting}
            />
          </div>
          {error && <span className="error-message">{error}</span>}
        </div>

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          {isSubmitting ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>

      <div className="form-footer">
        <button type="button" onClick={onBack} className="link-button">
          ← Back to Login
        </button>
      </div>
    </div>
  );
};

export default ForgotPasswordForm;
