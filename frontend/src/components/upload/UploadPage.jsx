/**
 * UploadPage Component
 * Combines AudioUploader, UploadProgress, and ProcessingStatus
 * Requirements: 2.1, 2.2, 9.1, 9.3
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AudioUploader from './AudioUploader';
import UploadProgress from './UploadProgress';
import ProcessingStatus from './ProcessingStatus';
import { uploadAudio, pollUploadStatus } from '../../services/uploadService';

const UploadPage = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploadState, setUploadState] = useState('idle'); // idle, uploading, processing, completed, error
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [error, setError] = useState(null);
  const [lectureId, setLectureId] = useState(null);

  const handleFileSelect = useCallback((file) => {
    setSelectedFile(file);
    setError(null);
    // Auto-generate title from filename if not set
    if (!title) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
      setTitle(nameWithoutExt);
    }
  }, [title]);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title for the lecture');
      return;
    }

    setError(null);
    setUploadState('uploading');
    setUploadProgress(0);

    try {
      // Upload the file
      const result = await uploadAudio(selectedFile, title.trim(), (progress) => {
        setUploadProgress(progress);
      });

      setUploadState('processing');
      setProcessingStatus({ status: 'processing', progress: 0 });

      // Poll for processing status
      const finalStatus = await pollUploadStatus(
        result.uploadId || result.upload_id,
        (status) => {
          setProcessingStatus(status);
        }
      );

      setUploadState('completed');
      setLectureId(finalStatus.lectureId || finalStatus.lecture_id);
    } catch (err) {
      setError(err.message || 'Upload failed');
      setUploadState('error');
    }
  };

  const handleViewNotes = () => {
    if (lectureId) {
      navigate(`/notes/${lectureId}`);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setTitle('');
    setUploadState('idle');
    setUploadProgress(0);
    setProcessingStatus(null);
    setError(null);
    setLectureId(null);
  };

  return (
    <div className="upload-page">
      <div className="upload-page-header">
        <h1 className="text-h1">Upload Audio</h1>
        <p className="text-body upload-page-subtitle">
          Upload a recorded lecture to generate transcripts and study notes
        </p>
      </div>

      {uploadState === 'idle' && (
        <div className="upload-form">
          <div className="form-group">
            <label htmlFor="lecture-title" className="text-label form-label">
              Lecture Title
            </label>
            <input
              id="lecture-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for this lecture"
              className="form-input"
              aria-describedby="title-hint"
            />
            <span id="title-hint" className="text-small form-hint">
              Give your lecture a descriptive name for easy reference
            </span>
          </div>

          <AudioUploader onFileSelect={handleFileSelect} />

          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!selectedFile}
            className="upload-submit-button"
            aria-label="Start upload"
          >
            Upload and Process
          </button>
        </div>
      )}

      {uploadState === 'uploading' && (
        <div className="upload-progress-container">
          <h2 className="text-h2">Uploading...</h2>
          <UploadProgress progress={uploadProgress} />
          <p className="text-body progress-text">Uploading your audio file</p>
        </div>
      )}

      {uploadState === 'processing' && processingStatus && (
        <div className="processing-container">
          <h2 className="text-h2">Processing...</h2>
          <ProcessingStatus 
            status={processingStatus.status || 'processing'} 
            progress={processingStatus.progress || 0}
            error={processingStatus.error}
            onRetry={handleReset}
          />
        </div>
      )}

      {uploadState === 'completed' && (
        <div className="upload-complete">
          <div className="success-icon" aria-hidden="true">✓</div>
          <h2 className="text-h2">Processing Complete!</h2>
          <p className="text-body">Your lecture has been transcribed and study notes have been generated.</p>
          <div className="complete-actions">
            <button onClick={handleViewNotes} className="view-notes-button">
              View Notes
            </button>
            <button onClick={handleReset} className="upload-another-button">
              Upload Another
            </button>
          </div>
        </div>
      )}

      {uploadState === 'error' && (
        <div className="upload-error">
          <div className="error-icon" aria-hidden="true">✕</div>
          <h2 className="text-h2">Upload Failed</h2>
          <p className="text-body error-message">{error}</p>
          <button onClick={handleReset} className="try-again-button">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
