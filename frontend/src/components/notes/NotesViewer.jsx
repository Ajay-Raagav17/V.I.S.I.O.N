/**
 * NotesViewer component - Structured display of topic-wise notes
 * Requirements: 3.5, 5.5, 9.4
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import TopicSection from './TopicSection';
import SummaryPanel from './SummaryPanel';
import PDFExporter from './PDFExporter';
import '../../styles/notes.css';

const NotesViewer = ({ 
  notes, 
  lectureId, 
  lectureTitle, 
  onDownloadPDF,
  loading = false,
  error = null 
}) => {
  const [expandAll, setExpandAll] = useState(false);

  const handleExpandAll = () => {
    setExpandAll(!expandAll);
  };

  if (loading) {
    return (
      <div className="notes-viewer loading" data-testid="notes-viewer-loading">
        <div className="loading-spinner" aria-label="Loading notes">
          <span className="spinner"></span>
          <p>Loading notes...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notes-viewer error" data-testid="notes-viewer-error">
        <div className="error-message" role="alert">
          <h3>Error Loading Notes</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!notes) {
    return (
      <div className="notes-viewer empty" data-testid="notes-viewer-empty">
        <p>No notes available for this lecture.</p>
      </div>
    );
  }

  return (
    <div className="notes-viewer" data-testid="notes-viewer">
      <header className="notes-header">
        <h1 className="text-h1">{lectureTitle || 'Lecture Notes'}</h1>
        <div className="notes-actions">
          <button
            className="expand-all-button"
            onClick={handleExpandAll}
            aria-pressed={expandAll}
            data-testid="expand-all-button"
          >
            {expandAll ? 'Collapse All' : 'Expand All'}
          </button>
          <PDFExporter
            lectureId={lectureId}
            lectureTitle={lectureTitle}
            onDownload={onDownloadPDF}
          />
        </div>
      </header>

      <SummaryPanel
        summary={notes.summary}
        keyPoints={notes.key_points}
      />

      {notes.topics && notes.topics.length > 0 && (
        <section className="topics-section" aria-label="Topics">
          <h2 className="text-h2">Topics</h2>
          <div className="topics-list" data-testid="topics-list">
            {notes.topics.map((topic, index) => (
              <TopicSection
                key={index}
                topic={topic}
                defaultExpanded={expandAll}
              />
            ))}
          </div>
        </section>
      )}

      {(!notes.topics || notes.topics.length === 0) && (
        <p className="text-body no-topics" data-testid="no-topics">
          No topics extracted from this lecture.
        </p>
      )}
    </div>
  );
};

NotesViewer.propTypes = {
  notes: PropTypes.shape({
    topics: PropTypes.arrayOf(
      PropTypes.shape({
        title: PropTypes.string.isRequired,
        subtopics: PropTypes.arrayOf(PropTypes.string),
        keywords: PropTypes.arrayOf(PropTypes.string),
        definitions: PropTypes.objectOf(PropTypes.string),
        formulas: PropTypes.arrayOf(PropTypes.string),
        content: PropTypes.string,
      })
    ),
    summary: PropTypes.string,
    key_points: PropTypes.arrayOf(PropTypes.string),
  }),
  lectureId: PropTypes.string.isRequired,
  lectureTitle: PropTypes.string,
  onDownloadPDF: PropTypes.func,
  loading: PropTypes.bool,
  error: PropTypes.string,
};

export default NotesViewer;
