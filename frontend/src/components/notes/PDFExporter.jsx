/**
 * PDFExporter component - PDF generation and download trigger
 * Requirements: 5.5, 9.4
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import '../../styles/notes.css';

const PDFExporter = ({ lectureId, lectureTitle, onDownload, disabled = false }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    if (disabled || isDownloading) return;

    setIsDownloading(true);
    setError(null);

    try {
      if (onDownload) {
        await onDownload(lectureId);
      }
    } catch (err) {
      setError(err.message || 'Failed to download PDF');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleDownload();
    }
  };

  return (
    <div className="pdf-exporter" data-testid="pdf-exporter">
      <button
        className={`pdf-download-button ${isDownloading ? 'downloading' : ''}`}
        onClick={handleDownload}
        onKeyDown={handleKeyDown}
        disabled={disabled || isDownloading}
        aria-busy={isDownloading}
        aria-label={`Download PDF for ${lectureTitle || 'lecture'}`}
        data-testid="pdf-download-button"
      >
        {isDownloading ? (
          <>
            <span className="spinner" aria-hidden="true"></span>
            <span>Generating PDF...</span>
          </>
        ) : (
          <>
            <span className="download-icon" aria-hidden="true">📄</span>
            <span>Download PDF</span>
          </>
        )}
      </button>

      {error && (
        <div className="pdf-error" role="alert" data-testid="pdf-error">
          {error}
        </div>
      )}
    </div>
  );
};

PDFExporter.propTypes = {
  lectureId: PropTypes.string.isRequired,
  lectureTitle: PropTypes.string,
  onDownload: PropTypes.func,
  disabled: PropTypes.bool,
};

export default PDFExporter;
