/**
 * Unit tests for ProtectedRoute component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../ProtectedRoute';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth service
jest.mock('../../../services/authService', () => ({
  getStoredToken: jest.fn(),
  getStoredUser: jest.fn(),
  getCurrentUser: jest.fn(),
  clearAuthData: jest.fn()
}));

import * as authService from '../../../services/authService';

// Helper to render with router and auth
const renderWithProviders = (ui, { initialEntries = ['/protected'] } = {}) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        {ui}
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should show loading state while checking authentication', () => {
    authService.getStoredToken.mockReturnValue('test-token');
    authService.getStoredUser.mockReturnValue({ user_id: '123', email: 'test@example.com' });
    authService.getCurrentUser.mockReturnValue(new Promise(() => {})); // Never resolves

    renderWithProviders(
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should redirect to login when not authenticated', async () => {
    authService.getStoredToken.mockReturnValue(null);
    authService.getStoredUser.mockReturnValue(null);

    renderWithProviders(
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    );

    // Wait for the redirect
    await screen.findByText('Login Page');
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('should render children when authenticated', async () => {
    authService.getStoredToken.mockReturnValue('test-token');
    authService.getStoredUser.mockReturnValue({ user_id: '123', email: 'test@example.com' });
    authService.getCurrentUser.mockResolvedValue({ user_id: '123', email: 'test@example.com' });

    renderWithProviders(
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    );

    await screen.findByText('Protected Content');
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should redirect to custom path when specified', async () => {
    authService.getStoredToken.mockReturnValue(null);
    authService.getStoredUser.mockReturnValue(null);

    renderWithProviders(
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute redirectTo="/custom-login">
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/custom-login" element={<div>Custom Login Page</div>} />
      </Routes>
    );

    await screen.findByText('Custom Login Page');
    expect(screen.getByText('Custom Login Page')).toBeInTheDocument();
  });

  it('should have accessible loading state', () => {
    authService.getStoredToken.mockReturnValue('test-token');
    authService.getStoredUser.mockReturnValue({ user_id: '123', email: 'test@example.com' });
    authService.getCurrentUser.mockReturnValue(new Promise(() => {}));

    renderWithProviders(
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    );

    const loadingContainer = screen.getByRole('status');
    expect(loadingContainer).toHaveAttribute('aria-live', 'polite');
  });
});
