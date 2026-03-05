/**
 * Unit tests for AudioUploader component
 * Tests file selection and validation
 * Requirements: 2.1, 2.2, 9.3
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AudioUploader from '../AudioUploader';

// Mock the uploadService module - avoid requireActual due to import.meta issues
jest.mock('../../../services/uploadService', () => ({
  validateFile: jest.fn((file) => {
    if (!file) return { valid: false, error: 'No file selected' };
    const fileName = file.name.toLowerCase();
    if (fileName.endsWith('.mp3') || fileName.endsWith('.wav') || 
        fileName.endsWith('.m4a') || fileName.endsWith('.ogg')) {
      return { valid: true };
    }
    return { valid: false, error: 'Invalid file format. Supported formats: MP3, WAV, M4A, OGG' };
  }),
  uploadAudio: jest.fn(),
  SUPPORTED_EXTENSIONS: ['.mp3', '.wav', '.m4a', '.ogg'],
  SUPPORTED_FORMATS: ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/ogg'],
  MAX_FILE_SIZE: 100 * 1024 * 1024,
}));

import { validateFile } from '../../../services/uploadService';

describe('AudioUploader', () => {
  const mockOnFileSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render the drop zone with instructions', () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    expect(screen.getByText(/drag and drop an audio file/i)).toBeInTheDocument();
    expect(screen.getByText(/supported formats/i)).toBeInTheDocument();
  });

  it('should have accessible drop zone with proper aria attributes', () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const dropZone = screen.getByTestId('drop-zone');
    expect(dropZone).toHaveAttribute('role', 'button');
    expect(dropZone).toHaveAttribute('aria-label', 'Upload audio file. Click or drag and drop');
    expect(dropZone).toHaveAttribute('tabIndex', '0');
  });

  it('should call onFileSelect when a valid file is selected', async () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const file = new File(['audio content'], 'lecture.mp3', { type: 'audio/mpeg' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);
    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('should not call onFileSelect for invalid file format', async () => {
    // The mock returns invalid for non-audio files
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const file = new File(['text content'], 'document.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);
    // For invalid files, onFileSelect should not be called
    expect(mockOnFileSelect).not.toHaveBeenCalled();
  });

  it('should display selected file information', async () => {
    validateFile.mockReturnValue({ valid: true });
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const file = new File(['audio content'], 'lecture.mp3', { type: 'audio/mpeg' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);
    await waitFor(() => {
      expect(screen.getByTestId('selected-file')).toBeInTheDocument();
    });
    expect(screen.getByText('lecture.mp3')).toBeInTheDocument();
  });

  it('should allow clearing selected file', async () => {
    validateFile.mockReturnValue({ valid: true });
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const file = new File(['audio content'], 'lecture.mp3', { type: 'audio/mpeg' });
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);
    await waitFor(() => {
      expect(screen.getByTestId('selected-file')).toBeInTheDocument();
    });
    const clearButton = screen.getByTestId('clear-button');
    await userEvent.click(clearButton);
    await waitFor(() => {
      expect(screen.queryByTestId('selected-file')).not.toBeInTheDocument();
    });
    expect(screen.getByText(/drag and drop an audio file/i)).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} disabled={true} />);
    const dropZone = screen.getByTestId('drop-zone');
    expect(dropZone).toHaveAttribute('aria-disabled', 'true');
    expect(dropZone).toHaveAttribute('tabIndex', '-1');
  });

  it('should handle drag and drop events', async () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const dropZone = screen.getByTestId('drop-zone');
    fireEvent.dragEnter(dropZone, { dataTransfer: { files: [] } });
    expect(dropZone).toHaveClass('dragging');
    fireEvent.dragLeave(dropZone);
    expect(dropZone).not.toHaveClass('dragging');
  });

  it('should handle file drop', async () => {
    validateFile.mockReturnValue({ valid: true });
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    const dropZone = screen.getByTestId('drop-zone');
    const file = new File(['audio content'], 'lecture.mp3', { type: 'audio/mpeg' });
    fireEvent.drop(dropZone, { dataTransfer: { files: [file] } });
    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it('should have aria-live for accessibility announcements', () => {
    render(<AudioUploader onFileSelect={mockOnFileSelect} />);
    expect(document.querySelector('[aria-live="polite"]')).toBeInTheDocument();
  });
});
