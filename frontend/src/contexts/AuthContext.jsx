/**
 * Authentication context provider for managing authentication state.
 * Provides user authentication state and methods throughout the app.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

// Create the auth context
const AuthContext = createContext(null);

// Token refresh interval (refresh 5 minutes before expiry, assuming 1 hour tokens)
const TOKEN_REFRESH_INTERVAL = 55 * 60 * 1000; // 55 minutes

/**
 * AuthProvider component that wraps the app and provides authentication state.
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Initialize auth state from stored data
   */
  const initializeAuth = useCallback(async () => {
    try {
      const storedToken = authService.getStoredToken();
      const storedUser = authService.getStoredUser();

      if (storedToken && storedUser) {
        // Verify token is still valid by fetching current user
        try {
          const currentUser = await authService.getCurrentUser();
          setUser({
            user_id: currentUser.user_id,
            email: currentUser.email
          });
          setToken(storedToken);
        } catch (err) {
          // Token is invalid, clear stored data
          authService.clearAuthData();
          setUser(null);
          setToken(null);
        }
      }
    } catch (err) {
      console.error('Error initializing auth:', err);
      setError('Failed to initialize authentication');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Register a new user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Registration result
   */
  const register = async (email, password) => {
    setError(null);
    try {
      const result = await authService.register(email, password);
      setUser(result.user);
      setToken(result.token);
      return { success: true, user: result.user };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Registration failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  /**
   * Login with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Login result
   */
  const login = async (email, password) => {
    setError(null);
    try {
      const result = await authService.login(email, password);
      setUser(result.user);
      setToken(result.token);
      return { success: true, user: result.user };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  /**
   * Logout current user
   */
  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setToken(null);
      setError(null);
    }
  };

  /**
   * Refresh the access token
   * @returns {Promise<boolean>} True if refresh succeeded
   */
  const refreshAuthToken = async () => {
    try {
      const result = await authService.refreshToken();
      setToken(result.token);
      setUser(result.user);
      return true;
    } catch (err) {
      console.error('Token refresh failed:', err);
      // If refresh fails, log out the user
      await logout();
      return false;
    }
  };

  /**
   * Clear any authentication errors
   */
  const clearError = () => {
    setError(null);
  };

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  // Set up automatic token refresh
  useEffect(() => {
    if (!token) return;

    const refreshInterval = setInterval(() => {
      refreshAuthToken();
    }, TOKEN_REFRESH_INTERVAL);

    return () => clearInterval(refreshInterval);
  }, [token]);

  // Context value
  const value = {
    user,
    token,
    loading,
    error,
    isAuthenticated: !!user && !!token,
    register,
    login,
    logout,
    refreshAuthToken,
    clearError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use the auth context
 * @returns {Object} Auth context value
 * @throws {Error} If used outside of AuthProvider
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
