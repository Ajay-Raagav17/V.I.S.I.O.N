/**
 * Unit tests for DashboardLayout component
 * Tests dashboard navigation and layout
 * Requirements: 6.4, 9.1
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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

describe('DashboardLayout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lectureService.getLectures.mockResolvedValue({ lectures: [] });
    lectureService.formatLectureDate.mockImplementation((date) => new Date(date).toLocaleDateString());
    lectureService.formatDuration.mockImplementation((seconds) => `${Math.floor(seconds / 60)}:00`);
  });

  it('should render dashboard container', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByText('VISION')).toBeInTheDocument();
    });
  });

  it('should display welcome message on home tab', async () => {
    renderWithProviders(<DashboardLayout />);
    
    // Design system update: Welcome message is now "Welcome to VISION" per Requirement 9.1
    await waitFor(() => {
      expect(screen.getByText('Welcome to VISION')).toBeInTheDocument();
    });
  });

  it('should display feature cards on home tab', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByText('VISION')).toBeInTheDocument();
    });
    
    // Design system update: Feature cards now use new text per Requirement 9.3
    expect(screen.getByRole('heading', { name: 'Speech to Text' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'AI Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'PDF Export' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Node Generation' })).toBeInTheDocument();
  });

  it('should have navigation buttons', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Home' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
    });
  });

  it('should switch to history tab when My Lectures is clicked', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
    
    await waitFor(() => {
      expect(screen.getByTestId('lecture-history')).toBeInTheDocument();
    });
  });

  it('should switch to history tab when PDF Export card is clicked', async () => {
    renderWithProviders(<DashboardLayout />);
    
    // Design system update: "Lecture History" is now "PDF Export" per Requirement 9.3
    await waitFor(() => {
      expect(screen.getByText('PDF Export')).toBeInTheDocument();
    });
    
    // Find the PDF Export button (which navigates to history)
    const historyButton = screen.getByTestId('feature-card-pdf');
    await userEvent.click(historyButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('lecture-history')).toBeInTheDocument();
    });
  });

  it('should show back to home button when not on home tab', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
    
    await waitFor(() => {
      expect(screen.getByLabelText('Back to home')).toBeInTheDocument();
    });
  });

  it('should return to home when back button is clicked', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'My Lectures' })).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByRole('button', { name: 'My Lectures' }));
    
    await waitFor(() => {
      expect(screen.getByLabelText('Back to home')).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByLabelText('Back to home'));
    
    // Design system update: Welcome message is now "Welcome to VISION" per Requirement 9.1
    await waitFor(() => {
      expect(screen.getByText('Welcome to VISION')).toBeInTheDocument();
    });
  });

  it('should have logout button', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Log out')).toBeInTheDocument();
    });
  });

  it('should have mobile menu toggle button', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
    });
  });

  it('should toggle mobile menu when button is clicked', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Toggle navigation menu')).toBeInTheDocument();
    });
    
    const menuButton = screen.getByLabelText('Toggle navigation menu');
    
    // Initially not expanded
    expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    
    await userEvent.click(menuButton);
    
    // Now expanded
    expect(menuButton).toHaveAttribute('aria-expanded', 'true');
  });

  it('should have links to live captioning and upload pages', async () => {
    renderWithProviders(<DashboardLayout />);
    
    // Design system update: Feature cards now use new text per Requirement 9.3
    await waitFor(() => {
      // These are Link components, check for the text content
      expect(screen.getByText('Speech to Text')).toBeInTheDocument();
      expect(screen.getByText('AI Summary')).toBeInTheDocument();
    });
  });

  it('should mark active tab with aria-current', async () => {
    renderWithProviders(<DashboardLayout />);
    
    await waitFor(() => {
      const homeButton = screen.getByRole('button', { name: 'Home' });
      expect(homeButton).toHaveAttribute('aria-current', 'page');
    });
  });
});
