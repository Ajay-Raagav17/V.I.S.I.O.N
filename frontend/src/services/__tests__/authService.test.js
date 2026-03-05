/**
 * Unit tests for authService
 */

import {
  validatePassword,
  validateEmail,
  storeAuthData,
  getStoredToken,
  getStoredUser,
  clearAuthData,
  isAuthenticated
} from '../authService';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('authService', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('validatePassword', () => {
    it('should reject passwords shorter than 8 characters', () => {
      const result = validatePassword('Short1');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must be at least 8 characters long');
    });

    it('should reject passwords without uppercase letters', () => {
      const result = validatePassword('lowercase123');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one uppercase letter');
    });

    it('should reject passwords without lowercase letters', () => {
      const result = validatePassword('UPPERCASE123');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one lowercase letter');
    });

    it('should reject passwords without numbers', () => {
      const result = validatePassword('NoNumbers');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Password must contain at least one number');
    });

    it('should accept valid passwords', () => {
      const result = validatePassword('ValidPass123');
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });

  describe('validateEmail', () => {
    it('should accept valid email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@domain.org')).toBe(true);
      expect(validateEmail('user+tag@example.co.uk')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('invalid@')).toBe(false);
      expect(validateEmail('@domain.com')).toBe(false);
      expect(validateEmail('user@.com')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('token storage', () => {
    it('should store and retrieve auth data', () => {
      const token = 'test-token';
      const user = { user_id: '123', email: 'test@example.com' };

      storeAuthData(token, user);

      expect(localStorageMock.setItem).toHaveBeenCalledWith('vision_access_token', token);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('vision_user', JSON.stringify(user));
    });

    it('should clear auth data', () => {
      clearAuthData();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('vision_access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('vision_user');
    });

    it('should return null for missing token', () => {
      const token = getStoredToken();
      expect(token).toBeNull();
    });

    it('should return null for missing user', () => {
      const user = getStoredUser();
      expect(user).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('should return false when no token is stored', () => {
      expect(isAuthenticated()).toBe(false);
    });

    it('should return true when token is stored', () => {
      localStorageMock.getItem.mockReturnValueOnce('test-token');
      expect(isAuthenticated()).toBe(true);
    });
  });
});
