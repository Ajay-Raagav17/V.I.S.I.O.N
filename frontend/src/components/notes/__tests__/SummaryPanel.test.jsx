/**
 * Unit tests for SummaryPanel component
 * Tests summary and key points display
 * Requirements: 3.5, 9.4
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import SummaryPanel from '../SummaryPanel';

describe('SummaryPanel', () => {
  const mockSummary = 'This lecture covers the fundamentals of machine learning.';
  const mockKeyPoints = [
    'Machine learning is a subset of AI',
    'Supervised learning uses labeled data',
    'Neural networks mimic brain structure',
  ];

  it('should render summary text', () => {
    render(<SummaryPanel summary={mockSummary} keyPoints={[]} />);
    
    // Design system update: "Summary" is now "AI Summary" per Requirement 10.5
    expect(screen.getByText('AI Summary')).toBeInTheDocument();
    expect(screen.getByTestId('summary-text')).toHaveTextContent(mockSummary);
  });

  it('should render key points list', () => {
    render(<SummaryPanel summary="" keyPoints={mockKeyPoints} />);
    
    expect(screen.getByText('Key Points')).toBeInTheDocument();
    expect(screen.getByTestId('key-points-list')).toBeInTheDocument();
    
    mockKeyPoints.forEach(point => {
      expect(screen.getByText(point)).toBeInTheDocument();
    });
  });

  it('should render both summary and key points', () => {
    render(<SummaryPanel summary={mockSummary} keyPoints={mockKeyPoints} />);
    
    // Design system update: "Summary" is now "AI Summary" per Requirement 10.5
    expect(screen.getByText('AI Summary')).toBeInTheDocument();
    expect(screen.getByText('Key Points')).toBeInTheDocument();
    expect(screen.getByTestId('summary-text')).toBeInTheDocument();
    expect(screen.getByTestId('key-points-list')).toBeInTheDocument();
  });

  it('should show no summary message when both are empty', () => {
    render(<SummaryPanel summary="" keyPoints={[]} />);
    
    expect(screen.getByTestId('no-summary')).toBeInTheDocument();
    // Design system update: Empty state message per Requirement 10.5
    expect(screen.getByText('Summary will appear here after transcription begins.')).toBeInTheDocument();
  });

  it('should show no summary message when props are undefined', () => {
    render(<SummaryPanel />);
    
    expect(screen.getByTestId('no-summary')).toBeInTheDocument();
  });

  it('should not show summary section when summary is empty', () => {
    render(<SummaryPanel summary="" keyPoints={mockKeyPoints} />);
    
    expect(screen.queryByTestId('summary-text')).not.toBeInTheDocument();
    expect(screen.getByTestId('key-points-list')).toBeInTheDocument();
  });

  it('should not show key points section when array is empty', () => {
    render(<SummaryPanel summary={mockSummary} keyPoints={[]} />);
    
    expect(screen.getByTestId('summary-text')).toBeInTheDocument();
    expect(screen.queryByTestId('key-points-list')).not.toBeInTheDocument();
  });

  it('should have proper accessibility structure', () => {
    render(<SummaryPanel summary={mockSummary} keyPoints={mockKeyPoints} />);
    
    const panel = screen.getByTestId('summary-panel');
    expect(panel).toBeInTheDocument();
    
    // Design system update: "Summary" is now "AI Summary" per Requirement 10.5
    // Check headings are present
    expect(screen.getByRole('heading', { name: 'AI Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Key Points' })).toBeInTheDocument();
  });
});
