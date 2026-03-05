/**
 * Unit tests for LectureHistory component
 * Tests lecture list rendering, filtering, and sorting
 * Requirements: 6.4, 6.5
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import LectureHistory from '../LectureHistory';

// Mock the lecture service
jest.mock('../../../services/lectureService', () => ({
  getLectures: jest.fn(),
  deleteLecture: jest.fn(),
  formatLectureDate: jest.fn((date) => new Date(date).toLocaleDateString()),
  formatDuration: jest.fn((seconds) => {
    const mins = Math.floor(seconds / 60);
    return `${mins}:00`;
  }),
}));

// Import after mock
import * as lectureService from '../../../services/lectureService';

const mockLectures = [
  {
    id: 'lecture-1',
    title: 'Introduction to Machine Learning',
    lecture_type: 'live',
    duration_seconds: 3600,
    created_at: '2025-01-15T10:00:00Z',
    processing_status: 'completed',
  },
  {
    id: 'lecture-2',
    title: 'Data Structures',
    lecture_type: 'upload',
    duration_seconds: 2400,
    created_at: '2025-01-14T14:30:00Z',
    processing_status: 'completed',
  },
  {
    id: 'lecture-3',
    title: 'Algorithms',
    lecture_type: 'live',
    duration_seconds: 1800,
    created_at: '2025-01-13T09:00:00Z',
    processing_status: 'processing',
  },
];

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('LectureHistory', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lectureService.getLectures.mockResolvedValue({ lectures: mockLectures });
    lectureService.deleteLecture.mockResolvedValue({ success: true });
    lectureService.formatLectureDate.mockImplementation((date) => new Date(date).toLocaleDateString());
    lectureService.formatDuration.mockImplementation((seconds) => {
      const mins = Math.floor(seconds / 60);
      return `${mins}:00`;
    });
  });

  it('should render lecture history container', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByTestId('lecture-history')).toBeInTheDocument();
    });
  });

  it('should display loading state initially', () => {
    lectureService.getLectures.mockImplementation(() => new Promise(() => {}));
    renderWithRouter(<LectureHistory />);
    
    expect(screen.getByText('Loading lectures...')).toBeInTheDocument();
  });

  it('should render lecture list after loading', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByTestId('lecture-grid')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Introduction to Machine Learning')).toBeInTheDocument();
    expect(screen.getByText('Data Structures')).toBeInTheDocument();
    expect(screen.getByText('Algorithms')).toBeInTheDocument();
  });

  it('should render correct number of lecture cards', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      const lectureCards = screen.getAllByTestId('lecture-card');
      expect(lectureCards).toHaveLength(3);
    });
  });

  it('should show empty state when no lectures', async () => {
    lectureService.getLectures.mockResolvedValue({ lectures: [] });
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
    expect(screen.getByText('No lectures yet')).toBeInTheDocument();
  });

  it('should show error state on fetch failure', async () => {
    lectureService.getLectures.mockRejectedValue(new Error('Network error'));
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('should have retry button on error', async () => {
    lectureService.getLectures.mockRejectedValue(new Error('Network error'));
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('should retry fetch when retry button is clicked', async () => {
    lectureService.getLectures
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ lectures: mockLectures });
    
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByText('Retry'));
    
    await waitFor(() => {
      expect(lectureService.getLectures).toHaveBeenCalledTimes(2);
    });
  });

  it('should have filter dropdown', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Filter lectures by type')).toBeInTheDocument();
    });
  });

  it('should have sort dropdown', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Sort lectures')).toBeInTheDocument();
    });
  });

  it('should call getLectures with filter when filter changes', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Filter lectures by type')).toBeInTheDocument();
    });
    
    const filterSelect = screen.getByLabelText('Filter lectures by type');
    await userEvent.selectOptions(filterSelect, 'live');
    
    await waitFor(() => {
      expect(lectureService.getLectures).toHaveBeenCalledWith(
        expect.objectContaining({ filterType: 'live' })
      );
    });
  });

  it('should call getLectures with sort when sort changes', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getByLabelText('Sort lectures')).toBeInTheDocument();
    });
    
    const sortSelect = screen.getByLabelText('Sort lectures');
    await userEvent.selectOptions(sortSelect, 'title-asc');
    
    await waitFor(() => {
      expect(lectureService.getLectures).toHaveBeenCalledWith(
        expect.objectContaining({ sortBy: 'title', sortOrder: 'asc' })
      );
    });
  });

  it('should remove lecture from list after successful deletion', async () => {
    renderWithRouter(<LectureHistory />);
    
    await waitFor(() => {
      expect(screen.getAllByTestId('lecture-card')).toHaveLength(3);
    });
    
    // Click delete button on first lecture
    const deleteButtons = screen.getAllByTestId('delete-button');
    await userEvent.click(deleteButtons[0]);
    
    // Confirm deletion
    await waitFor(() => {
      expect(screen.getByTestId('delete-confirm')).toBeInTheDocument();
    });
    
    await userEvent.click(screen.getByLabelText('Confirm deletion'));
    
    await waitFor(() => {
      expect(screen.getAllByTestId('lecture-card')).toHaveLength(2);
    });
  });
});
