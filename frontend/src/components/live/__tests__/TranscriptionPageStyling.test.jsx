/**
 * Unit tests for Transcription Page Styling
 * Tests design system application on LiveCaptionView/Transcription page
 * Requirements: 10.1, 10.4, 10.5
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import LiveCaptionView from '../LiveCaptionView';
import CaptionDisplay from '../CaptionDisplay';

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

// Mock CaptionDisplay component for LiveCaptionView tests
const MockCaptionDisplay = ({ captions, isActive }) => (
  <div data-testid="caption-display">
    <h2 className="text-h2 caption-section-title">Live Transcription</h2>
    {captions.length === 0 && !isActive && (
      <p className="text-body caption-placeholder-text">Listening for audio input…</p>
    )}
    <span data-testid="caption-count">{captions.length}</span>
    <span data-testid="is-active">{isActive ? 'active' : 'inactive'}</span>
  </div>
);

describe('Transcription Page Styling - Requirements 10.1, 10.4, 10.5', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Page Title Display - Requirement 10.1', () => {
    beforeEach(() => {
      // Use mock for these tests
      jest.doMock('../CaptionDisplay', () => MockCaptionDisplay);
    });

    it('should display "Transcription" as the page title', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const pageTitle = screen.getByRole('heading', { level: 1 });
      expect(pageTitle).toHaveTextContent('Transcription');
    });

    it('should apply text-h1 class to the page title', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const pageTitle = screen.getByRole('heading', { level: 1 });
      expect(pageTitle).toHaveClass('text-h1');
    });
  });

  describe('Session Name Field - Requirement 10.2', () => {
    it('should display "Session Name" label', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const label = screen.getByText('Session Name');
      expect(label).toBeInTheDocument();
    });

    it('should apply input-label class to the session name label', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const label = screen.getByText('Session Name');
      expect(label).toHaveClass('input-label');
    });

    it('should display correct placeholder text', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const input = screen.getByPlaceholderText('e.g. Machine Learning Lecture – Day 1');
      expect(input).toBeInTheDocument();
    });

    it('should apply input-field class to the session name input', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const input = screen.getByPlaceholderText('e.g. Machine Learning Lecture – Day 1');
      expect(input).toHaveClass('input-field');
    });
  });

  describe('Action Button - Requirement 10.3', () => {
    it('should display "Start Transcribing" button text', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const button = screen.getByRole('button', { name: /start live captioning/i });
      expect(button).toHaveTextContent('Start Transcribing');
    });

    it('should apply btn-primary class to the start button', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const button = screen.getByRole('button', { name: /start live captioning/i });
      expect(button).toHaveClass('btn-primary');
    });
  });

  describe('AI Summary Section - Requirement 10.5', () => {
    it('should display "AI Summary" section title', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const summaryTitle = screen.getByText('AI Summary');
      expect(summaryTitle).toBeInTheDocument();
    });

    it('should apply text-h2 class to AI Summary title', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const summaryTitle = screen.getByText('AI Summary');
      expect(summaryTitle).toHaveClass('text-h2');
    });

    it('should display AI Summary placeholder text', () => {
      render(<LiveCaptionView onSessionComplete={jest.fn()} />);
      
      const placeholder = screen.getByText('Summary will appear here after transcription begins.');
      expect(placeholder).toBeInTheDocument();
    });
  });
});

describe('CaptionDisplay Section Styling - Requirement 10.4', () => {
  describe('Live Transcription Section Title', () => {
    it('should display "Live Transcription" as section title', () => {
      render(<CaptionDisplay captions={[]} isActive={false} />);
      
      const sectionTitle = screen.getByRole('heading', { level: 2 });
      expect(sectionTitle).toHaveTextContent('Live Transcription');
    });

    it('should apply text-h2 class to Live Transcription title', () => {
      render(<CaptionDisplay captions={[]} isActive={false} />);
      
      const sectionTitle = screen.getByRole('heading', { level: 2 });
      expect(sectionTitle).toHaveClass('text-h2');
    });
  });

  describe('Empty State - Requirement 10.4', () => {
    it('should display empty state text when no captions and not active', () => {
      render(<CaptionDisplay captions={[]} isActive={false} />);
      
      const emptyText = screen.getByText('Listening for audio input…');
      expect(emptyText).toBeInTheDocument();
    });

    it('should apply text-body class to empty state text', () => {
      render(<CaptionDisplay captions={[]} isActive={false} />);
      
      const emptyText = screen.getByText('Listening for audio input…');
      expect(emptyText).toHaveClass('text-body');
    });
  });

  describe('Waiting State', () => {
    it('should display waiting text when active but no captions', () => {
      render(<CaptionDisplay captions={[]} isActive={true} />);
      
      const waitingText = screen.getByText('Listening for audio input…');
      expect(waitingText).toBeInTheDocument();
    });
  });
});
