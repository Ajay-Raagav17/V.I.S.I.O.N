/**
 * Unit tests for LoginForm styling according to VISION Design System
 * Requirements: 8.1, 8.2, 8.3, 8.4
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import LoginForm from '../LoginForm';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth service
jest.mock('../../../services/authService', () => ({
  login: jest.fn(),
  validateEmail: jest.fn((email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)),
  getStoredToken: jest.fn(() => null),
  getStoredUser: jest.fn(() => null),
  clearAuthData: jest.fn()
}));

// Wrapper component with AuthProvider
const renderWithAuth = (component) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('LoginForm Styling - Design System Compliance', () => {
  const mockOnSuccess = jest.fn();
  const mockOnSwitchToRegister = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Requirement 8.1: VISION logo styling', () => {
    it('should display VISION logo with brand color class', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const logo = screen.getByTestId('vision-logo');
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveTextContent('VISION');
      expect(logo).toHaveClass('vision-logo');
    });

    it('should render VISION logo as h1 element', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const logo = screen.getByTestId('vision-logo');
      expect(logo.tagName).toBe('H1');
    });
  });

  describe('Requirement 8.2: Form label styling', () => {
    it('should display Username label with text-label class', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const usernameLabel = screen.getByText('Username');
      expect(usernameLabel).toBeInTheDocument();
      expect(usernameLabel).toHaveClass('text-label');
      expect(usernameLabel).toHaveClass('form-label');
    });

    it('should display Password label with text-label class', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const passwordLabel = screen.getByText('Password');
      expect(passwordLabel).toBeInTheDocument();
      expect(passwordLabel).toHaveClass('text-label');
      expect(passwordLabel).toHaveClass('form-label');
    });
  });

  describe('Requirement 8.3: Login button styling', () => {
    it('should display Log In button with correct styling classes', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const loginButton = screen.getByTestId('login-button');
      expect(loginButton).toBeInTheDocument();
      expect(loginButton).toHaveTextContent('Log In');
      expect(loginButton).toHaveClass('btn-primary');
      expect(loginButton).toHaveClass('login-submit-button');
    });

    it('should have submit type on login button', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const loginButton = screen.getByTestId('login-button');
      expect(loginButton).toHaveAttribute('type', 'submit');
    });
  });

  describe('Requirement 8.4: Secondary action links styling', () => {
    it('should display signup link with text-small and secondary-action classes', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const signupLink = screen.getByTestId('signup-link');
      expect(signupLink).toBeInTheDocument();
      expect(signupLink).toHaveClass('text-small');
      expect(signupLink).toHaveClass('secondary-action');
      expect(signupLink).toHaveTextContent("Don't have an account?");
      expect(signupLink).toHaveTextContent('Sign up');
    });

    it('should display forgot password link with text-small and secondary-action classes', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const forgotPasswordLink = screen.getByTestId('forgot-password-link');
      expect(forgotPasswordLink).toBeInTheDocument();
      expect(forgotPasswordLink).toHaveClass('text-small');
      expect(forgotPasswordLink).toHaveClass('secondary-action');
      expect(forgotPasswordLink).toHaveTextContent('Forgot password?');
    });

    it('should have link-button class on Sign up button', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const signupButton = screen.getByRole('button', { name: /sign up/i });
      expect(signupButton).toHaveClass('link-button');
    });

    it('should have link-button class on Forgot password button', () => {
      renderWithAuth(
        <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
      );

      const forgotPasswordButton = screen.getByRole('button', { name: /forgot password/i });
      expect(forgotPasswordButton).toHaveClass('link-button');
    });
  });
});
