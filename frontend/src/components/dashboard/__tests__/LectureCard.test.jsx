/**
 * Unit tests for LectureCard component
 * Tests lecture card interactions and deletion confirmation flow
 * Requirements: 6.4, 6.5
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import LectureCard from '../LectureCard';

// Mock the lecture service - only formatDuration is still imported by LectureCard
jest.mock('../../../services/lectureService', () => ({
  formatDuration: jest.fn((seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }),
}));

const mockLecture = {
  id: 'lecture-123',
  title: 'Introduction to Machine Learning',
  lecture_type: 'live',
  duration_seconds: 3600,
  created_at: '2025-01-15T10:00:00Z',
  processing_status: 'completed',
};

const mockOnDelete = jest.fn();

const renderWithRouter = (component) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('LectureCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockOnDelete.mockResolvedValue();
  });

  it('should render lecture card', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByTestId('lecture-card')).toBeInTheDocument();
  });

  it('should display lecture title', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('Introduction to Machine Learning')).toBeInTheDocument();
  });

  it('should display default title when title is missing', () => {
    const lectureWithoutTitle = { ...mockLecture, title: null };
    renderWithRouter(<LectureCard lecture={lectureWithoutTitle} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('Untitled Lecture')).toBeInTheDocument();
  });

  it('should display live session icon for live lectures', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('🎤')).toBeInTheDocument();
  });

  it('should display upload icon for uploaded lectures', () => {
    const uploadedLecture = { ...mockLecture, lecture_type: 'upload' };
    renderWithRouter(<LectureCard lecture={uploadedLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('📁')).toBeInTheDocument();
  });

  it('should display formatted duration in minutes format per Requirement 11.4', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    // Duration should be formatted as "X minutes" per Requirement 11.4
    expect(screen.getByText('60 minutes')).toBeInTheDocument();
  });

  it('should display formatted date per Requirement 11.4', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    // Date should be formatted as "15 Jan 2025" per Requirement 11.4
    expect(screen.getByText('15 Jan 2025')).toBeInTheDocument();
  });

  it('should display metadata with separator per Requirement 11.4', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    // Metadata should be formatted as "date · duration" per Requirement 11.4
    expect(screen.getByText('·')).toBeInTheDocument();
  });

  it('should display completed status badge', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    // Status badge appears in header
    expect(screen.getByText('Ready', { selector: '.lecture-status-badge' })).toBeInTheDocument();
  });

  it('should display processing status badge', () => {
    const processingLecture = { ...mockLecture, processing_status: 'processing' };
    renderWithRouter(<LectureCard lecture={processingLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('Processing', { selector: '.lecture-status-badge' })).toBeInTheDocument();
  });

  it('should display pending status badge', () => {
    const pendingLecture = { ...mockLecture, processing_status: 'pending' };
    renderWithRouter(<LectureCard lecture={pendingLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('Pending', { selector: '.lecture-status-badge' })).toBeInTheDocument();
  });

  it('should display failed status badge', () => {
    const failedLecture = { ...mockLecture, processing_status: 'failed' };
    renderWithRouter(<LectureCard lecture={failedLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByText('Failed', { selector: '.lecture-status-badge' })).toBeInTheDocument();
  });

  it('should have delete button', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByTestId('delete-button')).toBeInTheDocument();
  });

  it('should have accessible delete button label', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    expect(screen.getByLabelText('Delete Introduction to Machine Learning')).toBeInTheDocument();
  });

  it('should link to notes page for completed lectures', () => {
    renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
    
    const link = screen.getByLabelText('View Introduction to Machine Learning');
    expect(link).toHaveAttribute('href', '/notes/lecture-123');
  });

  it('should not link to notes page for non-completed lectures', () => {
    const processingLecture = { ...mockLecture, processing_status: 'processing' };
    renderWithRouter(<LectureCard lecture={processingLecture} onDelete={mockOnDelete} />);
    
    const link = screen.getByLabelText('View Introduction to Machine Learning');
    // Non-completed lectures have disabled class and don't link to notes
    expect(link).toHaveClass('disabled');
  });

  // Deletion confirmation flow tests
  describe('Deletion confirmation flow', () => {
    it('should show delete confirmation when delete button is clicked', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      const deleteButton = screen.getByTestId('delete-button');
      await userEvent.click(deleteButton);
      
      expect(screen.getByTestId('delete-confirm')).toBeInTheDocument();
      expect(screen.getByText('Delete this lecture?')).toBeInTheDocument();
    });

    it('should show warning message in confirmation dialog', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      
      expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
    });

    it('should have cancel and confirm buttons in confirmation dialog', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      
      expect(screen.getByLabelText('Cancel deletion')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm deletion')).toBeInTheDocument();
    });

    it('should hide confirmation dialog when cancel is clicked', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      expect(screen.getByTestId('delete-confirm')).toBeInTheDocument();
      
      await userEvent.click(screen.getByLabelText('Cancel deletion'));
      
      expect(screen.queryByTestId('delete-confirm')).not.toBeInTheDocument();
    });

    it('should call onDelete when confirm is clicked', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      await userEvent.click(screen.getByLabelText('Confirm deletion'));
      
      expect(mockOnDelete).toHaveBeenCalledWith('lecture-123');
    });

    it('should show deleting state during deletion', async () => {
      mockOnDelete.mockImplementation(() => new Promise(() => {})); // Never resolves
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      await userEvent.click(screen.getByLabelText('Confirm deletion'));
      
      expect(screen.getByText('Deleting...')).toBeInTheDocument();
    });

    it('should disable buttons during deletion', async () => {
      mockOnDelete.mockImplementation(() => new Promise(() => {})); // Never resolves
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      await userEvent.click(screen.getByLabelText('Confirm deletion'));
      
      expect(screen.getByLabelText('Cancel deletion')).toBeDisabled();
      expect(screen.getByLabelText('Confirm deletion')).toBeDisabled();
    });

    it('should hide confirmation and show card on delete error', async () => {
      mockOnDelete.mockRejectedValue(new Error('Delete failed'));
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      await userEvent.click(screen.getByTestId('delete-button'));
      await userEvent.click(screen.getByLabelText('Confirm deletion'));
      
      await waitFor(() => {
        expect(screen.queryByTestId('delete-confirm')).not.toBeInTheDocument();
      });
      expect(screen.getByText('Introduction to Machine Learning')).toBeInTheDocument();
    });

    it('should not navigate when delete button is clicked', async () => {
      renderWithRouter(<LectureCard lecture={mockLecture} onDelete={mockOnDelete} />);
      
      const deleteButton = screen.getByTestId('delete-button');
      await userEvent.click(deleteButton);
      
      // Should show confirmation, not navigate
      expect(screen.getByTestId('delete-confirm')).toBeInTheDocument();
    });
  });
});
