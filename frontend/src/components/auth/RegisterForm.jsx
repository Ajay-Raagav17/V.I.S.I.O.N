/**
 * RegisterForm component with premium visual design.
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { validateEmail, validatePassword } from '../../services/authService';

const RegisterForm = ({ onSuccess, onSwitchToLogin }) => {
  const { register, error: authError, clearError } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors = {};
    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    if (!password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordValidation = validatePassword(password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.errors[0];
      }
    }
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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
      const result = await register(email, password);
      if (result.success && onSuccess) {
        onSuccess(result.user);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="register-form-container">
      <div className="form-header">
        <h2 className="form-title">Create your account</h2>
        <p className="form-subtitle">Start your journey with VISION today</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form" noValidate>
        <div className="form-group">
          <label htmlFor="register-email" className="form-label">Email Address</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </span>
            <input
              id="register-email"
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
          <label htmlFor="register-password" className="form-label">Password</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </span>
            <input
              id="register-password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors(p => ({...p, password: null})); }}
              className={`form-input ${errors.password ? 'input-error' : ''}`}
              placeholder="Create a strong password"
              autoComplete="new-password"
              disabled={isSubmitting}
            />
          </div>
          
          <div className="password-requirements">
            <p className="requirements-title">Password must contain:</p>
            <ul className="requirements-list">
              <li className={password.length >= 8 ? 'requirement-met' : ''}>8+ characters</li>
              <li className={/[A-Z]/.test(password) ? 'requirement-met' : ''}>Uppercase</li>
              <li className={/[a-z]/.test(password) ? 'requirement-met' : ''}>Lowercase</li>
              <li className={/[0-9]/.test(password) ? 'requirement-met' : ''}>Number</li>
            </ul>
          </div>
          {errors.password && <span className="error-message">{errors.password}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="register-confirm-password" className="form-label">Confirm Password</label>
          <div className="input-wrapper">
            <span className="input-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </span>
            <input
              id="register-confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => { setConfirmPassword(e.target.value); setErrors(p => ({...p, confirmPassword: null})); }}
              className={`form-input ${errors.confirmPassword ? 'input-error' : ''}`}
              placeholder="Confirm your password"
              autoComplete="new-password"
              disabled={isSubmitting}
            />
          </div>
          {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
        </div>

        {authError && <div className="auth-error" role="alert">{authError}</div>}

        <button type="submit" className="submit-button" disabled={isSubmitting}>
          <span>{isSubmitting ? 'Creating Account...' : 'Create Account'}</span>
        </button>
      </form>

      <div className="form-footer">
        <p>
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="link-button" disabled={isSubmitting}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};

export default RegisterForm;
