/**
 * UploadProgress Component
 * Progress indicator during file upload
 * Requirements: 9.3
 */

import React from 'react';

const UploadProgress = ({ progress = 0, status = 'uploading' }) => {
  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return `Uploading... ${progress}%`;
      case 'processing':
        return 'Processing audio...';
      case 'transcribing':
        return 'Transcribing audio...';
      case 'analyzing':
        return 'Analyzing content...';
      case 'completed':
        return 'Complete!';
      case 'failed':
        return 'Upload failed';
      default:
        return 'Preparing...';
    }
  };

  const isComplete = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div 
      className="upload-progress" 
      role="progressbar" 
      aria-valuenow={progress} 
      aria-valuemin={0} 
      aria-valuemax={100}
      aria-label={getStatusText()}
      data-testid="upload-progress"
    >
      <div className="progress-header">
        <span className="progress-status" data-testid="progress-status">
          {getStatusText()}
        </span>
        {status === 'uploading' && (
          <span className="progress-percentage" data-testid="progress-percentage">
            {progress}%
          </span>
        )}
      </div>
      
      <div className="progress-bar-container">
        <div 
          className={`progress-bar ${isComplete ? 'complete' : ''} ${isFailed ? 'failed' : ''}`}
          style={{ width: `${progress}%` }}
          data-testid="progress-bar"
        />
      </div>

      {status === 'processing' && (
        <div className="processing-indicator" aria-live="polite">
          <div className="spinner" aria-hidden="true" />
          <span className="processing-text">This may take a few minutes...</span>
        </div>
      )}
    </div>
  );
};

export default UploadProgress;
