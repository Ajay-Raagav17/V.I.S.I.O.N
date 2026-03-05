/**
 * Unit tests for UploadProgress component
 * Tests upload progress display
 * Requirements: 9.3
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import UploadProgress from '../UploadProgress';

describe('UploadProgress', () => {
  it('should render progress bar with default values', () => {
    render(<UploadProgress />);

    const progressBar = screen.getByTestId('upload-progress');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('role', 'progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  it('should display uploading status with percentage', () => {
    render(<UploadProgress progress={45} status="uploading" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/uploading.*45%/i);
    expect(screen.getByTestId('progress-percentage')).toHaveTextContent('45%');
  });

  it('should display processing status', () => {
    render(<UploadProgress progress={100} status="processing" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/processing audio/i);
    expect(screen.queryByTestId('progress-percentage')).not.toBeInTheDocument();
  });

  it('should display transcribing status', () => {
    render(<UploadProgress progress={100} status="transcribing" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/transcribing audio/i);
  });

  it('should display analyzing status', () => {
    render(<UploadProgress progress={100} status="analyzing" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/analyzing content/i);
  });

  it('should display completed status', () => {
    render(<UploadProgress progress={100} status="completed" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/complete/i);
  });

  it('should display failed status', () => {
    render(<UploadProgress progress={50} status="failed" />);

    expect(screen.getByTestId('progress-status')).toHaveTextContent(/upload failed/i);
  });

  it('should update progress bar width based on progress', () => {
    render(<UploadProgress progress={75} status="uploading" />);

    const progressBar = screen.getByTestId('progress-bar');
    expect(progressBar).toHaveStyle({ width: '75%' });
  });

  it('should have complete class when status is completed', () => {
    render(<UploadProgress progress={100} status="completed" />);

    const progressBar = screen.getByTestId('progress-bar');
    expect(progressBar).toHaveClass('complete');
  });

  it('should have failed class when status is failed', () => {
    render(<UploadProgress progress={50} status="failed" />);

    const progressBar = screen.getByTestId('progress-bar');
    expect(progressBar).toHaveClass('failed');
  });

  it('should show processing indicator during processing', () => {
    render(<UploadProgress progress={100} status="processing" />);

    expect(screen.getByText(/this may take a few minutes/i)).toBeInTheDocument();
  });

  it('should have accessible aria-label', () => {
    render(<UploadProgress progress={50} status="uploading" />);

    const progressBar = screen.getByTestId('upload-progress');
    expect(progressBar).toHaveAttribute('aria-label', 'Uploading... 50%');
  });
});
