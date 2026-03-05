/**
 * ProcessingStatus Component
 * Status updates for transcription and AI analysis
 * Requirements: 9.3
 */

import React from 'react';

const ProcessingStatus = ({ 
  status = 'pending', 
  progress = 0, 
  error = null,
  onRetry = null 
}) => {
  const stages = [
    { key: 'uploading', label: 'Upload', icon: '📤' },
    { key: 'transcribing', label: 'Transcription', icon: '🎤' },
    { key: 'analyzing', label: 'AI Analysis', icon: '🤖' },
    { key: 'generating', label: 'Notes Generation', icon: '📝' },
    { key: 'completed', label: 'Complete', icon: '✅' },
  ];

  const getStageIndex = (currentStatus) => {
    const index = stages.findIndex(s => s.key === currentStatus);
    return index >= 0 ? index : 0;
  };

  const currentStageIndex = getStageIndex(status);
  const isFailed = status === 'failed';

  return (
    <div className="processing-status" aria-live="polite" data-testid="processing-status">
      <h3 className="status-title">Processing Status</h3>
      
      <div className="stages-container">
        {stages.map((stage, index) => {
          const isActive = index === currentStageIndex && !isFailed;
          const isComplete = index < currentStageIndex || status === 'completed';
          const isPending = index > currentStageIndex;

          return (
            <div 
              key={stage.key}
              className={`stage ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''} ${isPending ? 'pending' : ''}`}
              data-testid={`stage-${stage.key}`}
            >
              <div className="stage-icon" aria-hidden="true">
                {isComplete ? '✓' : stage.icon}
              </div>
              <div className="stage-label">{stage.label}</div>
              {isActive && (
                <div className="stage-progress">
                  <div className="mini-spinner" aria-hidden="true" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {isFailed && error && (
        <div className="error-container" role="alert" data-testid="error-container">
          <div className="error-icon" aria-hidden="true">❌</div>
          <div className="error-content">
            <p className="error-title">Processing Failed</p>
            <p className="error-message">{error}</p>
            {onRetry && (
              <button 
                className="retry-button" 
                onClick={onRetry}
                aria-label="Retry processing"
                data-testid="retry-button"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      )}

      {status === 'completed' && (
        <div className="success-message" data-testid="success-message">
          <p>Your lecture has been processed successfully!</p>
          <p className="success-hint">You can now view your notes and download the PDF.</p>
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;
