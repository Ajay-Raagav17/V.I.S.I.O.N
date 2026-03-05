/**
 * Unit tests for CaptionDisplay component
 * Tests caption display updates
 * Requirements: 1.2, 9.2
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import CaptionDisplay from '../CaptionDisplay';

describe('CaptionDisplay', () => {
  it('should render empty state when no captions and not active', () => {
    render(<CaptionDisplay captions={[]} isActive={false} />);

    expect(screen.getByText(/listening for audio input/i)).toBeInTheDocument();
  });

  it('should render waiting state when active but no captions', () => {
    render(<CaptionDisplay captions={[]} isActive={true} />);

    expect(screen.getByText(/listening for audio input/i)).toBeInTheDocument();
  });

  it('should render captions when provided', () => {
    const captions = [
      { segmentId: 0, text: 'Hello world', timestamp: 0, confidence: 0.95 },
      { segmentId: 1, text: 'This is a test', timestamp: 10, confidence: 0.92 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    expect(screen.getByText('Hello world')).toBeInTheDocument();
    expect(screen.getByText('This is a test')).toBeInTheDocument();
  });

  it('should display timestamps for each caption', () => {
    const captions = [
      { segmentId: 0, text: 'First segment', timestamp: 0, confidence: 0.95 },
      { segmentId: 1, text: 'Second segment', timestamp: 65, confidence: 0.92 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    expect(screen.getByText('00:00')).toBeInTheDocument();
    expect(screen.getByText('01:05')).toBeInTheDocument();
  });

  it('should show low confidence warning for captions below threshold', () => {
    const captions = [
      { segmentId: 0, text: 'Low confidence text', timestamp: 0, confidence: 0.5 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    expect(screen.getByLabelText(/low confidence/i)).toBeInTheDocument();
  });

  it('should not show warning for high confidence captions', () => {
    const captions = [
      { segmentId: 0, text: 'High confidence text', timestamp: 0, confidence: 0.95 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    expect(screen.queryByLabelText(/low confidence/i)).not.toBeInTheDocument();
  });

  it('should show live indicator when active with captions', () => {
    const captions = [
      { segmentId: 0, text: 'Live caption', timestamp: 0, confidence: 0.95 }
    ];

    render(<CaptionDisplay captions={captions} isActive={true} />);

    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('should have accessible role and aria-live attribute', () => {
    render(<CaptionDisplay captions={[]} isActive={false} />);

    const display = screen.getByRole('log');
    expect(display).toHaveAttribute('aria-live', 'polite');
    expect(display).toHaveAttribute('aria-label', 'Live captions');
  });

  it('should handle captions without segmentId using index', () => {
    const captions = [
      { text: 'No segment ID', timestamp: 0, confidence: 0.95 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    expect(screen.getByText('No segment ID')).toBeInTheDocument();
  });

  it('should format multi-digit timestamps correctly', () => {
    const captions = [
      { segmentId: 0, text: 'Long session', timestamp: 3661, confidence: 0.95 }
    ];

    render(<CaptionDisplay captions={captions} isActive={false} />);

    // 3661 seconds = 61 minutes and 1 second = 61:01
    expect(screen.getByText('61:01')).toBeInTheDocument();
  });
});
