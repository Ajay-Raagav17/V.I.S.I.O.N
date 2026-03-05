/**
 * SummaryPanel component - Key points and summary display
 * Requirements: 3.5, 9.4
 */

import React from 'react';
import PropTypes from 'prop-types';
import '../../styles/notes.css';

const SummaryPanel = ({ summary, keyPoints }) => {
  return (
    <div className="summary-panel" data-testid="summary-panel">
      {summary && (
        <div className="summary-section">
          <h2 className="text-h2">AI Summary</h2>
          <p className="text-body summary-text" data-testid="summary-text">
            {summary}
          </p>
        </div>
      )}

      {keyPoints && keyPoints.length > 0 && (
        <div className="key-points-section">
          <h3 className="text-h3">Key Points</h3>
          <ul className="key-points-list" data-testid="key-points-list">
            {keyPoints.map((point, index) => (
              <li key={index} className="text-body key-point-item">
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!summary && (!keyPoints || keyPoints.length === 0) && (
        <p className="text-body no-summary" data-testid="no-summary">
          Summary will appear here after transcription begins.
        </p>
      )}
    </div>
  );
};

SummaryPanel.propTypes = {
  summary: PropTypes.string,
  keyPoints: PropTypes.arrayOf(PropTypes.string),
};

export default SummaryPanel;
