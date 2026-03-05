/**
 * Authentication service for API calls to the backend auth endpoints.
 * Handles user registration, login, logout, and token management.
 */

import axios from 'axios';

const API_BASE_URL = '/api/auth';

// Token storage keys
const TOKEN_KEY = 'vision_access_token';
const USER_KEY = 'vision_user';

/**
 * Store authentication data in localStorage
 * @param {string} token - JWT access token
 * @param {Object} user - User data object
 */
export const storeAuthData = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * Clear authentication data from localStorage
 */
export const clearAuthData = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * Get stored access token
 * @returns {string|null} The stored token or null
 */
export const getStoredToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Get stored user data
 * @returns {Object|null} The stored user object or null
 */
export const getStoredUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
  return null;
};

/**
 * Create axios instance with auth header
 * @returns {AxiosInstance} Configured axios instance
 */
export const createAuthenticatedClient = () => {
  const token = getStoredToken();
  return axios.create({
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
};

/**
 * Register a new user account
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Auth response with token and user info
 */
export const register = async (email, password) => {
  const response = await axios.post(`${API_BASE_URL}/register`, {
    email,
    password
  });
  
  const { access_token, user_id, email: userEmail } = response.data;
  const user = { user_id, email: userEmail };
  
  storeAuthData(access_token, user);
  
  return { token: access_token, user };
};

/**
 * Login with email and password
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Auth response with token and user info
 */
export const login = async (email, password) => {
  const response = await axios.post(`${API_BASE_URL}/login`, {
    email,
    password
  });
  
  const { access_token, user_id, email: userEmail } = response.data;
  const user = { user_id, email: userEmail };
  
  storeAuthData(access_token, user);
  
  return { token: access_token, user };
};

/**
 * Logout current user
 * @returns {Promise<void>}
 */
export const logout = async () => {
  try {
    const client = createAuthenticatedClient();
    await client.post(`${API_BASE_URL}/logout`);
  } catch (error) {
    // Even if the API call fails, clear local data
    console.warn('Logout API call failed:', error.message);
  } finally {
    clearAuthData();
  }
};

/**
 * Get current user information
 * @returns {Promise<Object>} User information
 */
export const getCurrentUser = async () => {
  const client = createAuthenticatedClient();
  const response = await client.get(`${API_BASE_URL}/me`);
  return response.data;
};

/**
 * Refresh the access token
 * @returns {Promise<Object>} New auth response with refreshed token
 */
export const refreshToken = async () => {
  const client = createAuthenticatedClient();
  const response = await client.post(`${API_BASE_URL}/refresh`);
  
  const { access_token, user_id, email } = response.data;
  const user = { user_id, email };
  
  storeAuthData(access_token, user);
  
  return { token: access_token, user };
};

/**
 * Check if user is authenticated (has valid token stored)
 * @returns {boolean} True if token exists
 */
export const isAuthenticated = () => {
  return !!getStoredToken();
};

/**
 * Validate password meets requirements
 * @param {string} password - Password to validate
 * @returns {Object} Validation result with isValid and errors array
 */
export const validatePassword = (password) => {
  const errors = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if email format is valid
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export default {
  register,
  login,
  logout,
  getCurrentUser,
  refreshToken,
  isAuthenticated,
  getStoredToken,
  getStoredUser,
  clearAuthData,
  storeAuthData,
  validatePassword,
  validateEmail,
  createAuthenticatedClient
};
