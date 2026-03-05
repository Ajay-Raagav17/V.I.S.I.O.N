/**
 * Unit tests for PDFExporter component
 * Tests PDF download trigger
 * Requirements: 5.5, 9.4
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PDFExporter from '../PDFExporter';

describe('PDFExporter', () => {
  const mockOnDownload = jest.fn();
  const defaultProps = {
    lectureId: 'lecture-123',
    lectureTitle: 'Introduction to AI',
    onDownload: mockOnDownload,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render download button', () => {
    render(<PDFExporter {...defaultProps} />);
    
    expect(screen.getByTestId('pdf-download-button')).toBeInTheDocument();
    expect(screen.getByText('Download PDF')).toBeInTheDocument();
  });

  it('should have accessible label with lecture title', () => {
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    expect(button).toHaveAttribute('aria-label', 'Download PDF for Introduction to AI');
  });

  it('should call onDownload when button is clicked', async () => {
    mockOnDownload.mockResolvedValue();
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    
    expect(mockOnDownload).toHaveBeenCalledWith('lecture-123');
  });

  it('should show loading state while downloading', async () => {
    mockOnDownload.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    
    expect(screen.getByText('Generating PDF...')).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('should display error message on download failure', async () => {
    mockOnDownload.mockRejectedValue(new Error('Download failed'));
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByTestId('pdf-error')).toBeInTheDocument();
      expect(screen.getByText('Download failed')).toBeInTheDocument();
    });
  });


  it('should be disabled when disabled prop is true', () => {
    render(<PDFExporter {...defaultProps} disabled={true} />);
    
    const button = screen.getByTestId('pdf-download-button');
    expect(button).toBeDisabled();
  });

  it('should not call onDownload when disabled', async () => {
    render(<PDFExporter {...defaultProps} disabled={true} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    
    expect(mockOnDownload).not.toHaveBeenCalled();
  });

  it('should prevent multiple clicks while downloading', async () => {
    mockOnDownload.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    await userEvent.click(button);
    
    expect(mockOnDownload).toHaveBeenCalledTimes(1);
  });

  it('should reset to normal state after successful download', async () => {
    mockOnDownload.mockResolvedValue();
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    await userEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Download PDF')).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });
  });

  it('should use default label when lectureTitle is not provided', () => {
    render(<PDFExporter lectureId="lecture-123" onDownload={mockOnDownload} />);
    
    const button = screen.getByTestId('pdf-download-button');
    expect(button).toHaveAttribute('aria-label', 'Download PDF for lecture');
  });

  it('should handle keyboard activation with Enter key', async () => {
    mockOnDownload.mockResolvedValue();
    render(<PDFExporter {...defaultProps} />);
    
    const button = screen.getByTestId('pdf-download-button');
    button.focus();
    await userEvent.keyboard('{Enter}');
    
    expect(mockOnDownload).toHaveBeenCalled();
  });
});
