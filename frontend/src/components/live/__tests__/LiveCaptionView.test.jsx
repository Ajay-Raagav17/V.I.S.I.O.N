/**
 * Unit tests for LiveCaptionView component
 * Requirements: 1.1, 9.1, 9.3
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LiveCaptionView from '../LiveCaptionView';

// Mock the live service
jest.mock('../../../services/liveService', () => ({
  startSession: jest.fn(),
  stopSession: jest.fn(),
  LiveCaptionWebSocket: jest.fn().mockImplementation(() => ({
    connect: jest.fn().mockResolvedValue(),
    disconnect: jest.fn(),
    sendAudio: jest.fn(),
    isConnected: jest.fn().mockReturnValue(true),
    onCaption: null,
    onError: null,
    onStatusChange: null
  }))
}));

// Mock AudioCapture component
jest.mock('../AudioCapture', () => {
  return function MockAudioCapture() {
    return <div data-testid="audio-capture">Audio Capture Mock</div>;
  };
});

// Mock CaptionDisplay component
jest.mock('../CaptionDisplay', () => {
  return function MockCaptionDisplay({ captions, isActive }) {
    return (
      <div data-testid="caption-display">
        <span data-testid="caption-count">{captions.length}</span>
        <span data-testid="is-active">{isActive ? 'active' : 'inactive'}</span>
      </div>
    );
  };
});

describe('LiveCaptionView', () => {
  const mockOnSessionComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render the live caption view with title input', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    expect(screen.getByText('Transcription')).toBeInTheDocument();
    expect(screen.getByLabelText(/session name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start live captioning/i })).toBeInTheDocument();
  });

  it('should show error when starting without a title', async () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    const startButton = screen.getByRole('button', { name: /start live captioning/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/please enter a lecture title/i)).toBeInTheDocument();
    });
  });

  it('should render AudioCapture component', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    expect(screen.getByTestId('audio-capture')).toBeInTheDocument();
  });

  it('should render CaptionDisplay component', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    expect(screen.getByTestId('caption-display')).toBeInTheDocument();
  });

  it('should show status bar with connection status', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
  });

  it('should allow entering lecture title', async () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    const titleInput = screen.getByLabelText(/session name/i);
    await userEvent.type(titleInput, 'Introduction to Biology');

    expect(titleInput).toHaveValue('Introduction to Biology');
  });

  it('should have accessible start button', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    const startButton = screen.getByRole('button', { name: /start live captioning/i });
    expect(startButton).toHaveAttribute('aria-label', 'Start live captioning');
  });

  it('should display subtitle explaining the feature', () => {
    render(<LiveCaptionView onSessionComplete={mockOnSessionComplete} />);

    expect(screen.getByText(/real-time speech-to-text/i)).toBeInTheDocument();
  });
});
