/**
 * Unit tests for History page styling
 * Tests design system compliance for Session History page
 * Requirements: 11.1, 11.2, 11.3, 11.4
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LectureHistory from '../LectureHistory';
import LectureCard from '../LectureCard';

// Mock the lecture service
jest.mock('../../../services/lectureService', () => ({
  getLectures: jest.fn(),
  deleteLecture: jest.fn(),
  formatDuration: jest.fn((seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    return `${mins}:00`;
  }),
}));

import * as lectureService from '../../../services/lectureService';

const mockLectures = [
  {
    id: 'lecture-1',
    title: 'Introduction to Machine Learning',
    lecture_type: 'live',
    duration_seconds: 2520, // 42 minutes
    created_at: '2025-12-12T10:00:00Z',
    processing_status: 'completed',
  },
  {
    id: 'lecture-2',
    title: 'Data Structures',
    lecture_type: 'upload',
    duration_seconds: 3600,
    created_at: '2025-01-14T14:30:00Z',
    processing_status: 'completed',
  },
];

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('History Page Styling - Requirement 11', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lectureService.getLectures.mockResolvedValue({ lectures: mockLectures });
  });

  describe('11.1 - Page title displays as H1 "Session History"', () => {
    it('should display "Session History" as the page title', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        expect(screen.getByText('Session History')).toBeInTheDocument();
      });
    });

    it('should apply text-h1 class to page title', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const title = screen.getByText('Session History');
        expect(title).toHaveClass('text-h1');
      });
    });

    it('should render page title as h1 element', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const title = screen.getByRole('heading', { level: 1 });
        expect(title).toHaveTextContent('Session History');
      });
    });
  });

  describe('11.2 - Search input placeholder', () => {
    it('should display search input with placeholder "Search sessions…"', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search sessions…');
        expect(searchInput).toBeInTheDocument();
      });
    });

    it('should have input-field class on search input', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search sessions…');
        expect(searchInput).toHaveClass('input-field');
      });
    });

    it('should have accessible label for search input', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const searchInput = screen.getByLabelText('Search sessions');
        expect(searchInput).toBeInTheDocument();
      });
    });
  });

  describe('11.3 - Session card styling', () => {
    it('should display session name with H3 typography', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const title = screen.getByText('Introduction to Machine Learning');
        expect(title).toHaveClass('text-h3');
      });
    });

    it('should render session title as h3 element', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        const titles = screen.getAllByRole('heading', { level: 3 });
        expect(titles.length).toBeGreaterThan(0);
      });
    });

    it('should display date with small text styling', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        // Date should be formatted and have text-small class
        const dateElement = screen.getByText('12 Dec 2025');
        expect(dateElement).toHaveClass('text-small');
      });
    });

    it('should display duration with small text styling', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        // Duration should be formatted as "X minutes" and have text-small class
        const durationElement = screen.getByText('42 minutes');
        expect(durationElement).toHaveClass('text-small');
      });
    });

    it('should display status with muted color styling', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        // Status should have color-muted class
        const statusElements = screen.getAllByText('Ready');
        const statusElement = statusElements.find((el) =>
          el.classList.contains('color-muted')
        );
        expect(statusElement).toBeInTheDocument();
      });
    });
  });

  describe('11.4 - Session metadata format', () => {
    it('should format date as "12 Dec 2025"', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        expect(screen.getByText('12 Dec 2025')).toBeInTheDocument();
      });
    });

    it('should format duration as "42 minutes"', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        expect(screen.getByText('42 minutes')).toBeInTheDocument();
      });
    });

    it('should display separator between date and duration', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        // The separator should be "·" (middle dot)
        expect(screen.getAllByText('·').length).toBeGreaterThan(0);
      });
    });

    it('should display "Completed" status for completed sessions', async () => {
      renderWithRouter(<LectureHistory />);

      await waitFor(() => {
        // "Ready" is the label for completed status
        expect(screen.getAllByText('Ready').length).toBeGreaterThan(0);
      });
    });
  });
});

describe('LectureCard Styling - Individual Card Tests', () => {
  const mockLecture = {
    id: 'lecture-123',
    title: 'Test Lecture',
    lecture_type: 'live',
    duration_seconds: 2520, // 42 minutes
    created_at: '2025-12-12T10:00:00Z',
    processing_status: 'completed',
  };

  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnDelete.mockResolvedValue();
  });

  it('should apply lecture-card class to card container', () => {
    renderWithRouter(
      <LectureCard lecture={mockLecture} onDelete={mockOnDelete} />
    );

    expect(screen.getByTestId('lecture-card')).toHaveClass('lecture-card');
  });

  it('should apply text-h3 class to card title', () => {
    renderWithRouter(
      <LectureCard lecture={mockLecture} onDelete={mockOnDelete} />
    );

    const title = screen.getByText('Test Lecture');
    expect(title).toHaveClass('text-h3');
  });

  it('should apply text-small class to metadata elements', () => {
    renderWithRouter(
      <LectureCard lecture={mockLecture} onDelete={mockOnDelete} />
    );

    const dateElement = screen.getByText('12 Dec 2025');
    const durationElement = screen.getByText('42 minutes');

    expect(dateElement).toHaveClass('text-small');
    expect(durationElement).toHaveClass('text-small');
  });

  it('should apply color-muted class to status text', () => {
    renderWithRouter(
      <LectureCard lecture={mockLecture} onDelete={mockOnDelete} />
    );

    const statusElement = screen.getByText('Ready', {
      selector: '.lecture-card-status',
    });
    expect(statusElement).toHaveClass('color-muted');
  });
});
