/**
 * Unit tests for TopicSection component
 * Tests collapsible topic sections
 * Requirements: 3.5, 9.4
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TopicSection from '../TopicSection';

const mockTopic = {
  title: 'Introduction to Machine Learning',
  content: 'Machine learning is a subset of artificial intelligence.',
  subtopics: ['Supervised Learning', 'Unsupervised Learning'],
  keywords: ['AI', 'Neural Networks', 'Deep Learning'],
  definitions: {
    'Machine Learning': 'A type of AI that learns from data',
    'Neural Network': 'A computing system inspired by biological neural networks',
  },
  formulas: ['y = mx + b', 'E = mc²'],
};

describe('TopicSection', () => {
  it('should render topic title', () => {
    render(<TopicSection topic={mockTopic} />);
    expect(screen.getByText('Introduction to Machine Learning')).toBeInTheDocument();
  });

  it('should be collapsed by default', () => {
    render(<TopicSection topic={mockTopic} />);
    expect(screen.queryByTestId('topic-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('topic-header')).toHaveAttribute('aria-expanded', 'false');
  });

  it('should expand when header is clicked', async () => {
    render(<TopicSection topic={mockTopic} />);
    const header = screen.getByTestId('topic-header');
    
    await userEvent.click(header);
    
    expect(screen.getByTestId('topic-content')).toBeInTheDocument();
    expect(header).toHaveAttribute('aria-expanded', 'true');
  });

  it('should collapse when expanded header is clicked', async () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    const header = screen.getByTestId('topic-header');
    
    expect(screen.getByTestId('topic-content')).toBeInTheDocument();
    
    await userEvent.click(header);
    
    expect(screen.queryByTestId('topic-content')).not.toBeInTheDocument();
  });


  it('should be expanded by default when defaultExpanded is true', () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    expect(screen.getByTestId('topic-content')).toBeInTheDocument();
    expect(screen.getByTestId('topic-header')).toHaveAttribute('aria-expanded', 'true');
  });

  it('should display subtopics when expanded', async () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    
    expect(screen.getByText('Subtopics')).toBeInTheDocument();
    expect(screen.getByText('Supervised Learning')).toBeInTheDocument();
    expect(screen.getByText('Unsupervised Learning')).toBeInTheDocument();
  });

  it('should display keywords when expanded', async () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    
    expect(screen.getByText('Keywords')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
    expect(screen.getByText('Neural Networks')).toBeInTheDocument();
  });

  it('should display definitions when expanded', async () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    
    expect(screen.getByText('Definitions')).toBeInTheDocument();
    expect(screen.getByText('Machine Learning')).toBeInTheDocument();
    expect(screen.getByText('A type of AI that learns from data')).toBeInTheDocument();
  });

  it('should display formulas when expanded', async () => {
    render(<TopicSection topic={mockTopic} defaultExpanded={true} />);
    
    expect(screen.getByText('Formulas')).toBeInTheDocument();
    expect(screen.getByText('y = mx + b')).toBeInTheDocument();
    expect(screen.getByText('E = mc²')).toBeInTheDocument();
  });

  it('should handle keyboard navigation with Enter key', async () => {
    render(<TopicSection topic={mockTopic} />);
    const header = screen.getByTestId('topic-header');
    
    header.focus();
    fireEvent.keyDown(header, { key: 'Enter' });
    
    expect(screen.getByTestId('topic-content')).toBeInTheDocument();
  });

  it('should handle keyboard navigation with Space key', async () => {
    render(<TopicSection topic={mockTopic} />);
    const header = screen.getByTestId('topic-header');
    
    header.focus();
    fireEvent.keyDown(header, { key: ' ' });
    
    expect(screen.getByTestId('topic-content')).toBeInTheDocument();
  });

  it('should render topic with minimal data', () => {
    const minimalTopic = { title: 'Simple Topic' };
    render(<TopicSection topic={minimalTopic} defaultExpanded={true} />);
    
    expect(screen.getByText('Simple Topic')).toBeInTheDocument();
    expect(screen.queryByText('Subtopics')).not.toBeInTheDocument();
    expect(screen.queryByText('Keywords')).not.toBeInTheDocument();
  });
});
