/**
 * Unit tests for responsive layout and mobile navigation
 * Tests component rendering at different viewport sizes
 * Requirements: 9.5
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import DashboardLayout from '../DashboardLayout';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the lecture service
jest.mock('../../../services/lectureService', () => ({
  getLectures: jest.fn(),
  deleteLecture: jest.fn(),
  formatLectureDate: jest.fn((date) => new Date(date).toLocaleDateString()),
  formatDuration: jest.fn((seconds) => `${Math.floor(seconds / 60)}:00`),
}));

// Mock the auth service
jest.mock('../../../services/authService', () => ({
  getStoredToken: jest.fn(() => 'mock-token'),
  getStoredUser: jest.fn(() => ({ email: 'test@example.com', user_id: '123' })),
  getCurrentUser: jest.fn().mockResolvedValue({ email: 'test@example.com', user_id: '123' }),
  logout: jest.fn().mockResolvedValue(),
  clearAuthData: jest.fn(),
}));

// Import after mock
import * as lectureService from '../../../services/lectureService';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderWithProviders = (component) => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('Responsive Layout Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lectureService.getLectures.mockResolvedValue({ lectures: [] });
  });

  describe('Mobile Navigation Functionality', () => {
    it('should render mobile menu toggle button', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
    });

    it('should have aria-expanded attribute on mobile menu button', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const menuButton = screen.getByLabelText('Toggle navigation menu');
        expect(menuButton).toHaveAttribute('aria-expanded');
      });
    });

    it('should toggle aria-expanded when mobile menu button is clicked', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
      
      const menuButton = screen.getByLabelText('Toggle navigation menu');
      
      // Initially not expanded
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      
      // Click to open
      await userEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      
      // Click to close
      await userEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should add mobile-open class to nav when menu is opened', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
      
      const menuButton = screen.getByLabelText('Toggle navigation menu');
      const nav = document.querySelector('.dashboard-nav');
      
      // Initially no mobile-open class
      expect(nav).not.toHaveClass('mobile-open');
      
      // Click to open
      await userEvent.click(menuButton);
      expect(nav).toHaveClass('mobile-open');
    });

    it('should close mobile menu when navigation item is clicked', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
      
      const menuButton = screen.getByLabelText('Toggle navigation menu');
      
      // Open menu
      await userEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      
      // Click on Home button
      await userEvent.click(screen.getByRole('button', { name: 'Home' }));
      
      // Menu should close
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should close mobile menu when My Lectures is clicked', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
      });
      
      const menuButton = screen.getByLabelText('Toggle navigation menu');
      
      // Open menu
      await userEvent.click(menuButton);
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      
      // Click on My Lectures button
      await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
      
      // Menu should close
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });
  });

  describe('Component Structure for Responsive Design', () => {
    it('should render dashboard container with proper structure', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(document.querySelector('.dashboard-container')).toBeInTheDocument();
      });
    });

    it('should render header with proper structure', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(document.querySelector('.dashboard-header')).toBeInTheDocument();
        expect(document.querySelector('.header-left')).toBeInTheDocument();
        expect(document.querySelector('.dashboard-nav')).toBeInTheDocument();
        expect(document.querySelector('.user-info')).toBeInTheDocument();
      });
    });

    it('should render feature cards grid', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(document.querySelector('.feature-cards')).toBeInTheDocument();
      });
      
      const featureCards = document.querySelectorAll('.feature-card');
      // Design system update: 4 feature cards (Speech to Text, AI Summary, PDF Export, Node Generation)
      expect(featureCards.length).toBe(4);
    });

    it('should render main content area', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(document.querySelector('.dashboard-main')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility for Responsive Design', () => {
    it('should have proper aria-label on mobile menu button', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const menuButton = screen.getByLabelText('Toggle navigation menu');
        expect(menuButton).toBeInTheDocument();
      });
    });

    it('should have aria-current on active navigation item', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const homeButton = screen.getByRole('button', { name: 'Home' });
        expect(homeButton).toHaveAttribute('aria-current', 'page');
      });
    });

    it('should update aria-current when switching tabs', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
      });
      
      // Click My Lectures
      await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
      
      await waitFor(() => {
        const myLecturesButton = screen.getByRole('button', { name: 'My Lectures' });
        expect(myLecturesButton).toHaveAttribute('aria-current', 'page');
        
        const homeButton = screen.getByRole('button', { name: 'Home' });
        expect(homeButton).not.toHaveAttribute('aria-current');
      });
    });

    it('should have aria-hidden on decorative icons', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const icons = document.querySelectorAll('.feature-icon');
        icons.forEach(icon => {
          expect(icon).toHaveAttribute('aria-hidden', 'true');
        });
      });
    });

    it('should have proper aria-label on logout button', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Log out')).toBeInTheDocument();
      });
    });

    it('should have proper aria-label on back button', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
      });
      
      // Switch to history tab to show back button
      await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
      
      await waitFor(() => {
        expect(screen.getByLabelText('Back to home')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation Links', () => {
    // Design system update: Feature cards now use new text per Requirements 9.3
    it('should have Speech to Text feature card link', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        // Speech to Text is a feature card link (was Live Captioning)
        expect(screen.getByText('Speech to Text')).toBeInTheDocument();
      });
    });

    it('should have AI Summary feature card', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        // AI Summary is a feature card link (was Upload Recording)
        expect(screen.getByText('AI Summary')).toBeInTheDocument();
      });
    });

    it('should have Speech to Text feature card with correct href', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        // Speech to Text links to /live
        const featureCard = screen.getByTestId('feature-card-speech');
        expect(featureCard).toHaveAttribute('href', '/live');
      });
    });

    it('should have AI Summary feature card link with correct href', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const featureCard = screen.getByTestId('feature-card-summary');
        expect(featureCard).toHaveAttribute('href', '/upload');
      });
    });
  });
});
