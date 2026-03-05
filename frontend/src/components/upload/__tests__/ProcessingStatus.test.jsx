/**
 * Unit tests for ProcessingStatus component
 * Tests status polling display
 * Requirements: 9.3
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ProcessingStatus from '../ProcessingStatus';

describe('ProcessingStatus', () => {
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render processing status container', () => {
    render(<ProcessingStatus />);

    expect(screen.getByTestId('processing-status')).toBeInTheDocument();
    expect(screen.getByText(/processing status/i)).toBeInTheDocument();
  });

  it('should display all processing stages', () => {
    render(<ProcessingStatus status="pending" />);

    expect(screen.getByTestId('stage-uploading')).toBeInTheDocument();
    expect(screen.getByTestId('stage-transcribing')).toBeInTheDocument();
    expect(screen.getByTestId('stage-analyzing')).toBeInTheDocument();
    expect(screen.getByTestId('stage-generating')).toBeInTheDocument();
    expect(screen.getByTestId('stage-completed')).toBeInTheDocument();
  });

  it('should mark uploading stage as active when status is uploading', () => {
    render(<ProcessingStatus status="uploading" />);

    const uploadingStage = screen.getByTestId('stage-uploading');
    expect(uploadingStage).toHaveClass('active');
  });

  it('should mark transcribing stage as active when status is transcribing', () => {
    render(<ProcessingStatus status="transcribing" />);

    const transcribingStage = screen.getByTestId('stage-transcribing');
    expect(transcribingStage).toHaveClass('active');
    
    // Previous stage should be complete
    const uploadingStage = screen.getByTestId('stage-uploading');
    expect(uploadingStage).toHaveClass('complete');
  });

  it('should mark analyzing stage as active when status is analyzing', () => {
    render(<ProcessingStatus status="analyzing" />);

    const analyzingStage = screen.getByTestId('stage-analyzing');
    expect(analyzingStage).toHaveClass('active');
    
    // Previous stages should be complete
    expect(screen.getByTestId('stage-uploading')).toHaveClass('complete');
    expect(screen.getByTestId('stage-transcribing')).toHaveClass('complete');
  });

  it('should mark generating stage as active when status is generating', () => {
    render(<ProcessingStatus status="generating" />);

    const generatingStage = screen.getByTestId('stage-generating');
    expect(generatingStage).toHaveClass('active');
  });

  it('should mark all stages as complete when status is completed', () => {
    render(<ProcessingStatus status="completed" />);

    expect(screen.getByTestId('stage-uploading')).toHaveClass('complete');
    expect(screen.getByTestId('stage-transcribing')).toHaveClass('complete');
    expect(screen.getByTestId('stage-analyzing')).toHaveClass('complete');
    expect(screen.getByTestId('stage-generating')).toHaveClass('complete');
    expect(screen.getByTestId('stage-completed')).toHaveClass('complete');
  });

  it('should display success message when completed', () => {
    render(<ProcessingStatus status="completed" />);

    expect(screen.getByTestId('success-message')).toBeInTheDocument();
    expect(screen.getByText(/processed successfully/i)).toBeInTheDocument();
  });

  it('should display error container when status is failed', () => {
    render(<ProcessingStatus status="failed" error="Network error occurred" />);

    expect(screen.getByTestId('error-container')).toBeInTheDocument();
    expect(screen.getByText(/processing failed/i)).toBeInTheDocument();
    expect(screen.getByText(/network error occurred/i)).toBeInTheDocument();
  });

  it('should display retry button when onRetry is provided and status is failed', () => {
    render(<ProcessingStatus status="failed" error="Error" onRetry={mockOnRetry} />);

    const retryButton = screen.getByTestId('retry-button');
    expect(retryButton).toBeInTheDocument();
    expect(retryButton).toHaveTextContent(/try again/i);
  });

  it('should call onRetry when retry button is clicked', () => {
    render(<ProcessingStatus status="failed" error="Error" onRetry={mockOnRetry} />);

    const retryButton = screen.getByTestId('retry-button');
    fireEvent.click(retryButton);

    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('should not display retry button when onRetry is not provided', () => {
    render(<ProcessingStatus status="failed" error="Error" />);

    expect(screen.queryByTestId('retry-button')).not.toBeInTheDocument();
  });

  it('should have aria-live for accessibility', () => {
    render(<ProcessingStatus status="processing" />);

    expect(document.querySelector('[aria-live="polite"]')).toBeInTheDocument();
  });

  it('should have role alert for error container', () => {
    render(<ProcessingStatus status="failed" error="Error" />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
