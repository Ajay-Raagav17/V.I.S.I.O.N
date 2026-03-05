/**
 * Unit tests for NotesViewer component
 * Tests notes rendering with mock data
 * Requirements: 3.5, 5.5, 9.4
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NotesViewer from '../NotesViewer';

const mockNotes = {
  summary: 'This lecture covers machine learning fundamentals.',
  key_points: [
    'ML is a subset of AI',
    'Supervised learning uses labeled data',
  ],
  topics: [
    {
      title: 'Introduction',
      content: 'Overview of machine learning concepts.',
      subtopics: ['History', 'Applications'],
      keywords: ['AI', 'ML'],
      definitions: { 'ML': 'Machine Learning' },
      formulas: [],
    },
    {
      title: 'Supervised Learning',
      content: 'Learning from labeled examples.',
      subtopics: ['Classification', 'Regression'],
      keywords: ['Labels', 'Training'],
      definitions: {},
      formulas: ['y = f(x)'],
    },
  ],
};

const defaultProps = {
  notes: mockNotes,
  lectureId: 'lecture-123',
  lectureTitle: 'Machine Learning 101',
  onDownloadPDF: jest.fn(),
};

describe('NotesViewer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render notes with lecture title', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByText('Machine Learning 101')).toBeInTheDocument();
    expect(screen.getByTestId('notes-viewer')).toBeInTheDocument();
  });

  it('should render summary panel', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByTestId('summary-panel')).toBeInTheDocument();
    expect(screen.getByText(mockNotes.summary)).toBeInTheDocument();
  });


  it('should render all topics', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByTestId('topics-list')).toBeInTheDocument();
    expect(screen.getByText('Introduction')).toBeInTheDocument();
    expect(screen.getByText('Supervised Learning')).toBeInTheDocument();
  });

  it('should render PDF exporter', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByTestId('pdf-exporter')).toBeInTheDocument();
    expect(screen.getByTestId('pdf-download-button')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    render(<NotesViewer {...defaultProps} loading={true} />);
    
    expect(screen.getByTestId('notes-viewer-loading')).toBeInTheDocument();
    expect(screen.getByText('Loading notes...')).toBeInTheDocument();
  });

  it('should show error state', () => {
    render(<NotesViewer {...defaultProps} error="Failed to load notes" />);
    
    expect(screen.getByTestId('notes-viewer-error')).toBeInTheDocument();
    expect(screen.getByText('Failed to load notes')).toBeInTheDocument();
  });

  it('should show empty state when notes is null', () => {
    render(<NotesViewer {...defaultProps} notes={null} />);
    
    expect(screen.getByTestId('notes-viewer-empty')).toBeInTheDocument();
    expect(screen.getByText('No notes available for this lecture.')).toBeInTheDocument();
  });

  it('should show no topics message when topics array is empty', () => {
    const notesWithoutTopics = { ...mockNotes, topics: [] };
    render(<NotesViewer {...defaultProps} notes={notesWithoutTopics} />);
    
    expect(screen.getByTestId('no-topics')).toBeInTheDocument();
    expect(screen.getByText('No topics extracted from this lecture.')).toBeInTheDocument();
  });

  it('should have expand all button', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByTestId('expand-all-button')).toBeInTheDocument();
    expect(screen.getByText('Expand All')).toBeInTheDocument();
  });

  it('should toggle expand all button text when clicked', async () => {
    render(<NotesViewer {...defaultProps} />);
    
    const expandButton = screen.getByTestId('expand-all-button');
    expect(expandButton).toHaveTextContent('Expand All');
    
    await userEvent.click(expandButton);
    
    expect(expandButton).toHaveTextContent('Collapse All');
  });

  it('should call onDownloadPDF when PDF button is clicked', async () => {
    const mockDownload = jest.fn().mockResolvedValue();
    render(<NotesViewer {...defaultProps} onDownloadPDF={mockDownload} />);
    
    const pdfButton = screen.getByTestId('pdf-download-button');
    await userEvent.click(pdfButton);
    
    expect(mockDownload).toHaveBeenCalledWith('lecture-123');
  });

  it('should use default title when lectureTitle is not provided', () => {
    render(<NotesViewer notes={mockNotes} lectureId="lecture-123" />);
    
    expect(screen.getByText('Lecture Notes')).toBeInTheDocument();
  });

  it('should render key points', () => {
    render(<NotesViewer {...defaultProps} />);
    
    mockNotes.key_points.forEach(point => {
      expect(screen.getByText(point)).toBeInTheDocument();
    });
  });

  it('should have proper accessibility structure', () => {
    render(<NotesViewer {...defaultProps} />);
    
    expect(screen.getByRole('region', { name: 'Topics' })).toBeInTheDocument();
  });
});
