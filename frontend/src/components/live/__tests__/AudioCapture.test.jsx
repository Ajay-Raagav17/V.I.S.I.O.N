/**
 * Unit tests for AudioCapture component
 * Tests microphone permission handling
 * Requirements: 1.1
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import AudioCapture from '../AudioCapture';

// Mock navigator.mediaDevices
const mockGetUserMedia = jest.fn();
const mockMediaStream = {
  getTracks: jest.fn().mockReturnValue([
    { stop: jest.fn() }
  ])
};

// Mock AudioContext
const mockAudioContext = {
  createMediaStreamSource: jest.fn().mockReturnValue({
    connect: jest.fn(),
    disconnect: jest.fn()
  }),
  createScriptProcessor: jest.fn().mockReturnValue({
    connect: jest.fn(),
    disconnect: jest.fn(),
    onaudioprocess: null
  }),
  close: jest.fn(),
  resume: jest.fn(),
  state: 'running',
  destination: {}
};

// Setup mocks before tests
beforeAll(() => {
  Object.defineProperty(global.navigator, 'mediaDevices', {
    value: {
      getUserMedia: mockGetUserMedia
    },
    writable: true
  });

  global.AudioContext = jest.fn().mockImplementation(() => mockAudioContext);
  global.webkitAudioContext = jest.fn().mockImplementation(() => mockAudioContext);
});

describe('AudioCapture', () => {
  const mockOnAudioData = jest.fn();
  const mockOnError = jest.fn();
  const mockOnPermissionChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUserMedia.mockReset();
  });

  it('should request microphone permission on mount', async () => {
    mockGetUserMedia.mockResolvedValue(mockMediaStream);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith({
        audio: expect.objectContaining({
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        })
      });
    });
  });

  it('should call onPermissionChange with granted when permission is allowed', async () => {
    mockGetUserMedia.mockResolvedValue(mockMediaStream);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    await waitFor(() => {
      expect(mockOnPermissionChange).toHaveBeenCalledWith('granted');
    });
  });

  it('should call onPermissionChange with denied when permission is denied', async () => {
    const permissionError = new Error('Permission denied');
    permissionError.name = 'NotAllowedError';
    mockGetUserMedia.mockRejectedValue(permissionError);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    await waitFor(() => {
      expect(mockOnPermissionChange).toHaveBeenCalledWith('denied');
    });
  });

  it('should call onError when microphone access fails', async () => {
    const permissionError = new Error('Permission denied');
    permissionError.name = 'NotAllowedError';
    mockGetUserMedia.mockRejectedValue(permissionError);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  it('should display permission denied message when access is denied', async () => {
    const permissionError = new Error('Permission denied');
    permissionError.name = 'NotAllowedError';
    mockGetUserMedia.mockRejectedValue(permissionError);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/microphone access denied/i)).toBeInTheDocument();
    });
  });

  it('should have aria-live attribute for accessibility', async () => {
    mockGetUserMedia.mockResolvedValue(mockMediaStream);

    render(
      <AudioCapture
        isCapturing={false}
        onAudioData={mockOnAudioData}
        onError={mockOnError}
        onPermissionChange={mockOnPermissionChange}
      />
    );

    // The component should have aria-live for screen readers
    expect(document.querySelector('[aria-live="polite"]')).toBeInTheDocument();
  });
});
