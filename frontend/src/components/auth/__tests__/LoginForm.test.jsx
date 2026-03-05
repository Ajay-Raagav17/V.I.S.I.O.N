/**
 * Unit tests for LoginForm component
 * Updated to match VISION Design System UI copy (Requirements 8.1-8.4)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

describe('LoginForm', () => {
  const mockOnSuccess = jest.fn();
  const mockOnSwitchToRegister = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render login form with all fields', () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Username" label instead of "Email Address"
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    // Updated to match design system: "Log In" button instead of "Sign In"
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('should show validation error for empty email', async () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Log In" button
    const submitButton = screen.getByRole('button', { name: /log in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
  });

  it('should show validation error for invalid email format', async () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Username" label
    const emailInput = screen.getByLabelText(/username/i);
    await userEvent.type(emailInput, 'invalid-email');

    // Updated to match design system: "Log In" button
    const submitButton = screen.getByRole('button', { name: /log in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
    });
  });

  it('should show validation error for empty password', async () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Username" label
    const emailInput = screen.getByLabelText(/username/i);
    await userEvent.type(emailInput, 'test@example.com');

    // Updated to match design system: "Log In" button
    const submitButton = screen.getByRole('button', { name: /log in/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('should call onSwitchToRegister when clicking Sign up link', async () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Sign up" link instead of "create one"
    const switchButton = screen.getByRole('button', { name: /sign up/i });
    fireEvent.click(switchButton);

    expect(mockOnSwitchToRegister).toHaveBeenCalled();
  });

  it('should have accessible form elements', () => {
    renderWithAuth(
      <LoginForm onSuccess={mockOnSuccess} onSwitchToRegister={mockOnSwitchToRegister} />
    );

    // Updated to match design system: "Username" label
    const emailInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);

    expect(emailInput).toHaveAttribute('type', 'email');
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(emailInput).toHaveAttribute('autocomplete', 'email');
    expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
  });
});
