/**
 * LiveCaptionView component - Main interface for real-time captioning.
 * Provides start/stop controls and coordinates audio capture with caption display.
 * 
 * Requirements: 1.1 - Initiate live captioning and activate Speech-to-Text API
 * Requirements: 9.1 - Clean interface with clearly labeled options
 * Requirements: 9.3 - Display progress indicators for system status
 */

import React, { useState, useCallback, useRef } from 'react';
import AudioCapture from './AudioCapture';
import CaptionDisplay from './CaptionDisplay';
import SegmentProcessor from '../../utils/SegmentProcessor';
import { startSession, stopSession, LiveCaptionWebSocket } from '../../services/liveService';

/**
 * Session status enum
 */
const SessionStatus = {
  IDLE: 'idle',
  STARTING: 'starting',
  ACTIVE: 'active',
  STOPPING: 'stopping',
  ERROR: 'error'
};

/**
 * LiveCaptionView component
 * @param {Object} props - Component props
 * @param {Function} props.onSessionComplete - Callback when session completes with results
 */
const LiveCaptionView = ({ onSessionComplete }) => {
  // Session state
  const [sessionStatus, setSessionStatus] = useState(SessionStatus.IDLE);
  const [sessionId, setSessionId] = useState(null);
  const [lectureTitle, setLectureTitle] = useState('');
  const [error, setError] = useState(null);
  
  // Caption state
  const [captions, setCaptions] = useState([]);
  const [partialCaption, setPartialCaption] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // Permission state
  const [micPermission, setMicPermission] = useState('prompt');
  
  // Refs for WebSocket and processor
  const wsRef = useRef(null);
  const processorRef = useRef(null);

  /**
   * Handle incoming caption from WebSocket
   */
  const handleCaption = useCallback((caption) => {
    if (caption.partial) {
      // Update partial caption for real-time feedback
      setPartialCaption(caption.text);
    } else {
      // Final caption - add to list and clear partial
      setCaptions(prev => [...prev, caption]);
      setPartialCaption('');
    }
  }, []);

  /**
   * Handle WebSocket error
   */
  const handleWsError = useCallback((errorMsg) => {
    setError(errorMsg);
    setSessionStatus(SessionStatus.ERROR);
  }, []);

  /**
   * Handle WebSocket status change
   */
  const handleWsStatusChange = useCallback((status) => {
    setConnectionStatus(status);
  }, []);

  /**
   * Handle audio data from AudioCapture
   */
  const handleAudioData = useCallback((audioData) => {
    if (processorRef.current) {
      processorRef.current.addData(audioData);
    }
  }, []);

  /**
   * Handle segment ready from processor
   */
  const handleSegmentReady = useCallback((segment) => {
    if (wsRef.current && wsRef.current.isConnected()) {
      wsRef.current.sendAudio(segment.data);
    }
  }, []);

  /**
   * Handle microphone permission change
   */
  const handlePermissionChange = useCallback((status) => {
    setMicPermission(status);
  }, []);

  /**
   * Handle audio capture error
   */
  const handleAudioError = useCallback((errorMsg) => {
    setError(errorMsg);
  }, []);

  /**
   * Start live captioning session
   */
  const handleStart = async () => {
    if (!lectureTitle.trim()) {
      setError('Please enter a lecture title');
      return;
    }

    setError(null);
    setSessionStatus(SessionStatus.STARTING);
    setCaptions([]);

    try {
      // Start session on backend
      const response = await startSession(lectureTitle);
      setSessionId(response.session_id);

      // Initialize segment processor - 5 second segments to match backend
      processorRef.current = new SegmentProcessor({
        segmentDuration: 5,
        sampleRate: 16000,
        channels: 1,
        sampleWidth: 2
      });
      processorRef.current.onSegment = handleSegmentReady;

      // Initialize WebSocket connection
      wsRef.current = new LiveCaptionWebSocket();
      wsRef.current.onCaption = handleCaption;
      wsRef.current.onError = handleWsError;
      wsRef.current.onStatusChange = handleWsStatusChange;

      await wsRef.current.connect(response.session_id);
      
      setSessionStatus(SessionStatus.ACTIVE);
    } catch (err) {
      setError(err.message || 'Failed to start session');
      setSessionStatus(SessionStatus.ERROR);
    }
  };

  /**
   * Stop live captioning session
   */
  const handleStop = async () => {
    setSessionStatus(SessionStatus.STOPPING);

    try {
      // Flush remaining audio
      if (processorRef.current) {
        processorRef.current.flush();
      }

      // Disconnect WebSocket
      if (wsRef.current) {
        wsRef.current.disconnect();
        wsRef.current = null;
      }

      // Stop session on backend
      if (sessionId) {
        const response = await stopSession(sessionId);
        
        if (onSessionComplete) {
          onSessionComplete({
            lectureId: response.lecture_id,
            transcript: response.transcript,
            duration: response.duration_seconds
          });
        }
      }

      // Reset state
      setSessionId(null);
      setSessionStatus(SessionStatus.IDLE);
      processorRef.current = null;
    } catch (err) {
      setError(err.message || 'Failed to stop session');
      setSessionStatus(SessionStatus.ERROR);
    }
  };

  /**
   * Clear error and reset to idle
   */
  const handleDismissError = () => {
    setError(null);
    setSessionStatus(SessionStatus.IDLE);
  };

  const isActive = sessionStatus === SessionStatus.ACTIVE;
  const isLoading = sessionStatus === SessionStatus.STARTING || sessionStatus === SessionStatus.STOPPING;

  return (
    <div className="live-caption-view">
      {/* Header */}
      <div className="live-caption-header">
        <h1 className="text-h1">Transcription</h1>
        <p className="text-body live-caption-subtitle">
          Real-time speech-to-text for classroom accessibility
        </p>
      </div>

      {/* Session setup */}
      {sessionStatus === SessionStatus.IDLE && (
        <div className="session-setup">
          <div className="form-group">
            <label htmlFor="lecture-title" className="input-label">
              Session Name
            </label>
            <input
              id="lecture-title"
              type="text"
              value={lectureTitle}
              onChange={(e) => setLectureTitle(e.target.value)}
              className="input-field"
              placeholder="e.g. Machine Learning Lecture – Day 1"
              disabled={isLoading}
            />
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="live-caption-error" role="alert">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button 
            onClick={handleDismissError}
            className="error-dismiss"
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Audio capture component */}
      <AudioCapture
        isCapturing={isActive}
        onAudioData={handleAudioData}
        onError={handleAudioError}
        onPermissionChange={handlePermissionChange}
      />

      {/* Status indicators */}
      <div className="status-bar">
        <div className={`status-indicator ${connectionStatus}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {connectionStatus === 'connected' ? 'Connected' : 
             connectionStatus === 'connecting' ? 'Connecting...' : 
             connectionStatus === 'error' ? 'Connection Error' : 'Disconnected'}
          </span>
        </div>
        {isActive && (
          <div className="session-info">
            <span className="session-title">{lectureTitle}</span>
            <span className="segment-count">{captions.length} segments</span>
          </div>
        )}
      </div>

      {/* Caption display */}
      <CaptionDisplay
        captions={captions}
        partialCaption={partialCaption}
        isActive={isActive}
        autoScroll={true}
      />

      {/* AI Summary section */}
      <div className="ai-summary-section">
        <h2 className="text-h2 ai-summary-title">AI Summary</h2>
        <div className="ai-summary-content">
          <p className="text-body ai-summary-placeholder">
            Summary will appear here after transcription begins.
          </p>
        </div>
      </div>

      {/* Control buttons */}
      <div className="control-buttons">
        {!isActive ? (
          <button
            onClick={handleStart}
            disabled={isLoading || micPermission === 'denied'}
            className="btn btn-primary control-button start-button"
            aria-label="Start live captioning"
          >
            {isLoading ? (
              <>
                <span className="button-spinner"></span>
                Starting...
              </>
            ) : (
              <>
                <span className="button-icon">▶</span>
                Start Transcribing
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleStop}
            disabled={isLoading}
            className="btn btn-primary control-button stop-button"
            aria-label="Stop live captioning"
          >
            {sessionStatus === SessionStatus.STOPPING ? (
              <>
                <span className="button-spinner"></span>
                Stopping...
              </>
            ) : (
              <>
                <span className="button-icon">■</span>
                Stop Transcribing
              </>
            )}
          </button>
        )}
      </div>

      {/* Help text */}
      {micPermission === 'denied' && (
        <div className="help-text warning">
          <p>
            Microphone access is required for live captioning. 
            Please enable microphone permissions in your browser settings and refresh the page.
          </p>
        </div>
      )}
    </div>
  );
};

export default LiveCaptionView;
