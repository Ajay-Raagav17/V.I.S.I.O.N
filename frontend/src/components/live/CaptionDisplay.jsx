/**
 * CaptionDisplay component for showing real-time captions with auto-scroll.
 * Displays transcribed text in a readable format with high contrast.
 * 
 * Requirements: 1.2 - Display transcribed text within 2 seconds
 * Requirements: 9.2 - Show captions in readable font size with high contrast
 */

import React, { useEffect, useRef } from 'react';

/**
 * CaptionDisplay component
 * @param {Object} props - Component props
 * @param {Array} props.captions - Array of caption objects with text and metadata
 * @param {string} props.partialCaption - Current partial/interim caption being transcribed
 * @param {boolean} props.isActive - Whether captioning is currently active
 * @param {boolean} props.autoScroll - Whether to auto-scroll to latest caption
 */
const CaptionDisplay = ({ 
  captions = [], 
  partialCaption = '',
  isActive = false,
  autoScroll = true 
}) => {
  const containerRef = useRef(null);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom when new captions arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current && bottomRef.current.scrollIntoView) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [captions, autoScroll]);

  /**
   * Format timestamp for display
   * @param {number} timestamp - Timestamp in seconds
   * @returns {string} Formatted time string
   */
  const formatTimestamp = (timestamp) => {
    const minutes = Math.floor(timestamp / 60);
    const seconds = Math.floor(timestamp % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className="caption-display" 
      ref={containerRef}
      role="log"
      aria-live="polite"
      aria-label="Live captions"
    >
      {/* Section title */}
      <h2 className="text-h2 caption-section-title">Live Transcription</h2>

      {/* Empty state */}
      {captions.length === 0 && !isActive && (
        <div className="caption-empty">
          <p className="text-body caption-placeholder-text">Listening for audio input…</p>
        </div>
      )}

      {/* Waiting state */}
      {captions.length === 0 && isActive && (
        <div className="caption-waiting">
          <div className="waiting-indicator">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
          <p className="text-body">Listening for audio input…</p>
        </div>
      )}

      {/* Caption list */}
      {(captions.length > 0 || partialCaption) && (
        <div className="caption-list">
          {captions.map((caption, index) => (
            <div 
              key={caption.segmentId ?? index} 
              className={`caption-item ${caption.isFinal ? 'final' : 'interim'}`}
            >
              <span className="caption-timestamp" aria-label="Timestamp">
                {formatTimestamp(caption.timestamp)}
              </span>
              <span className="caption-text">
                {caption.text}
              </span>
              {caption.confidence !== undefined && caption.confidence < 0.8 && (
                <span 
                  className="caption-confidence-warning" 
                  title="Low confidence transcription"
                  aria-label="Low confidence"
                >
                  ⚠️
                </span>
              )}
            </div>
          ))}
          {/* Show partial/interim caption while speaking */}
          {partialCaption && (
            <div className="caption-item partial">
              <span className="caption-timestamp" aria-label="Current">
                ...
              </span>
              <span className="caption-text partial-text">
                {partialCaption}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Active indicator */}
      {isActive && captions.length > 0 && (
        <div className="caption-active-indicator">
          <span className="pulse-dot"></span>
          <span>Live</span>
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
};

export default CaptionDisplay;
