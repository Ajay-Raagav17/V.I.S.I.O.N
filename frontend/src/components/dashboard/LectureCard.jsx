/**
 * LectureCard Component
 * Individual lecture preview with metadata
 * Requirements: 6.4, 6.5, 9.1
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDuration, createShareLink } from '../../services/lectureService';

/**
 * Format date as "12 Dec 2025" per Requirement 11.4
 */
const formatSessionDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
};

/**
 * Format duration as "42 minutes" per Requirement 11.4
 */
const formatSessionDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0 minutes';
  const minutes = Math.round(seconds / 60);
  return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
};

const LectureCard = ({ lecture, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [shareUrl, setShareUrl] = useState(null);
  const [isSharing, setIsSharing] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  const handleDeleteClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDeleting(true);
    try {
      await onDelete(lecture.id);
    } catch (error) {
      console.error('Delete failed:', error);
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleCancelDelete = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowDeleteConfirm(false);
  };

  const handleShareClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsSharing(true);
    try {
      const result = await createShareLink(lecture.id);
      const fullUrl = `${window.location.origin}${result.share_url}`;
      setShareUrl(fullUrl);
      setShowShareModal(true);
    } catch (error) {
      console.error('Share failed:', error);
    } finally {
      setIsSharing(false);
    }
  };

  const handleCopyLink = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(shareUrl);
      alert('Link copied to clipboard!');
    }
  };

  const handleCloseShareModal = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowShareModal(false);
  };

  const getTypeIcon = () => {
    return lecture.lecture_type === 'live' ? '🎤' : '📁';
  };

  const getTypeLabel = () => {
    return lecture.lecture_type === 'live' ? 'Live Session' : 'Uploaded';
  };

  const getStatusBadge = () => {
    const statusMap = {
      completed: { label: 'Ready', className: 'status-completed' },
      processing: { label: 'Processing', className: 'status-processing' },
      pending: { label: 'Pending', className: 'status-pending' },
      failed: { label: 'Failed', className: 'status-failed' },
    };
    return statusMap[lecture.processing_status] || statusMap.pending;
  };

  const status = getStatusBadge();

  return (
    <div className="lecture-card" data-testid="lecture-card">
      {showDeleteConfirm ? (
        <div className="delete-confirm" data-testid="delete-confirm">
          <p className="text-body delete-confirm-text">Delete this lecture?</p>
          <p className="text-small delete-confirm-subtitle">This action cannot be undone.</p>
          <div className="delete-confirm-actions">
            <button
              onClick={handleCancelDelete}
              className="cancel-delete-button"
              disabled={isDeleting}
              aria-label="Cancel deletion"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmDelete}
              className="confirm-delete-button"
              disabled={isDeleting}
              aria-label="Confirm deletion"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      ) : (
        <Link
          to={lecture.processing_status === 'completed' ? `/notes/${lecture.id}` : '#'}
          className={`lecture-card-link ${lecture.processing_status !== 'completed' ? 'disabled' : ''}`}
          aria-label={`View ${lecture.title}`}
        >
          <div className="lecture-card-header">
            <span className="lecture-type-icon" aria-hidden="true">
              {getTypeIcon()}
            </span>
            <span className={`lecture-status-badge ${status.className}`}>
              {status.label}
            </span>
          </div>

          <h3 className="text-h3 lecture-card-title">{lecture.title || 'Untitled Lecture'}</h3>

          <div className="lecture-card-meta">
            <span className="text-small lecture-date">{formatSessionDate(lecture.created_at)}</span>
            <span className="text-small lecture-separator">·</span>
            <span className="text-small lecture-duration">{formatSessionDuration(lecture.duration_seconds)}</span>
          </div>

          <div className="text-small lecture-card-status color-muted">
            {getStatusBadge().label}
          </div>

          <div className="lecture-card-actions">
            <button
              onClick={handleShareClick}
              className="lecture-share-button"
              aria-label={`Share ${lecture.title}`}
              data-testid="share-button"
              disabled={isSharing || lecture.processing_status !== 'completed'}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
              </svg>
            </button>
            <button
              onClick={handleDeleteClick}
              className="lecture-delete-button"
              aria-label={`Delete ${lecture.title}`}
              data-testid="delete-button"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" width="18" height="18">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            </button>
          </div>
        </Link>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="share-modal-overlay" onClick={handleCloseShareModal}>
          <div className="share-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-h3">Share Lecture</h3>
            <p className="text-body">Anyone with this link can view this lecture:</p>
            <div className="share-link-container">
              <input
                type="text"
                value={shareUrl || ''}
                readOnly
                className="share-link-input"
              />
              <button onClick={handleCopyLink} className="copy-link-button">
                Copy
              </button>
            </div>
            <button onClick={handleCloseShareModal} className="close-modal-button">
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LectureCard;
