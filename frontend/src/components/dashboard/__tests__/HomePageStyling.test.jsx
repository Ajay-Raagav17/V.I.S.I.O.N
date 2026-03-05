/**
 * Unit tests for Home Page Styling
 * Tests design system application on Dashboard/Home page
 * Requirements: 9.1, 9.3
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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

describe('Home Page Styling - Requirements 9.1, 9.3', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lectureService.getLectures.mockResolvedValue({ lectures: [] });
  });

  describe('H1 Title Display - Requirement 9.1', () => {
    it('should display "Welcome to VISION" as the main title', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const welcomeTitle = screen.getByText('Welcome to VISION');
        expect(welcomeTitle).toBeInTheDocument();
      });
    });

    it('should apply text-h1 class to the welcome title', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const welcomeTitle = screen.getByText('Welcome to VISION');
        expect(welcomeTitle).toHaveClass('text-h1');
      });
    });

    it('should display subtext "Turn speech into structured intelligence."', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const subtext = screen.getByText('Turn speech into structured intelligence.');
        expect(subtext).toBeInTheDocument();
      });
    });

    it('should apply text-body class to the subtext', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const subtext = screen.getByText('Turn speech into structured intelligence.');
        expect(subtext).toHaveClass('text-body');
      });
    });
  });

  describe('Feature Cards Content - Requirement 9.3', () => {
    it('should display "Speech to Text" feature card', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Speech to Text')).toBeInTheDocument();
      });
    });

    it('should display "AI Summary" feature card', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('AI Summary')).toBeInTheDocument();
      });
    });

    it('should display "PDF Export" feature card', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('PDF Export')).toBeInTheDocument();
      });
    });

    it('should display "Node Generation" feature card', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Node Generation')).toBeInTheDocument();
      });
    });

    it('should display correct description for Speech to Text', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Convert live audio into accurate real-time text.')).toBeInTheDocument();
      });
    });

    it('should display correct description for AI Summary', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Automatically extract key points and insights.')).toBeInTheDocument();
      });
    });

    it('should display correct description for PDF Export', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Download your sessions as clean, structured PDFs.')).toBeInTheDocument();
      });
    });

    it('should display correct description for Node Generation', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByText('Transform content into connected knowledge nodes.')).toBeInTheDocument();
      });
    });

    it('should apply text-h3 class to feature card titles', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const speechTitle = screen.getByText('Speech to Text');
        expect(speechTitle).toHaveClass('text-h3');
      });
    });

    it('should apply text-body class to feature card descriptions', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        const description = screen.getByText('Convert live audio into accurate real-time text.');
        expect(description).toHaveClass('text-body');
      });
    });
  });

  describe('Feature Cards Structure', () => {
    it('should have four feature cards', async () => {
      renderWithProviders(<DashboardLayout />);
      
      await waitFor(() => {
        expect(screen.getByTestId('feature-card-speech')).toBeInTheDocument();
        expect(screen.getByTestId('feature-card-summary')).toBeInTheDocument();
        expect(screen.getByTestId('feature-card-pdf')).toBeInTheDocument();
        expect(screen.getByTestId('feature-card-nodes')).toBeInTheDocument();
      });
    });
  });
});
