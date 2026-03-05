/**
 * LectureHistory Component
 * List view of past lectures with filtering and sorting
 * Requirements: 6.4, 6.5, 9.1
 */

import React, { useState, useEffect, useCallback } from 'react';
import LectureCard from './LectureCard';
import { getLectures, deleteLecture } from '../../services/lectureService';

const LectureHistory = () => {
  const [lectures, setLectures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchLectures = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLectures({ sortBy, sortOrder, filterType });
      setLectures(data.lectures || data || []);
    } catch (err) {
      setError(err.message || 'Failed to load lectures');
      setLectures([]);
    } finally {
      setLoading(false);
    }
  }, [sortBy, sortOrder, filterType]);

  useEffect(() => {
    fetchLectures();
  }, [fetchLectures]);

  const handleDelete = async (lectureId) => {
    try {
      await deleteLecture(lectureId);
      setLectures((prev) => prev.filter((l) => l.id !== lectureId));
    } catch (err) {
      setError(err.message || 'Failed to delete lecture');
      throw err;
    }
  };

  const handleSortChange = (e) => {
    const value = e.target.value;
    if (value === 'date-desc') {
      setSortBy('date');
      setSortOrder('desc');
    } else if (value === 'date-asc') {
      setSortBy('date');
      setSortOrder('asc');
    } else if (value === 'title-asc') {
      setSortBy('title');
      setSortOrder('asc');
    } else if (value === 'title-desc') {
      setSortBy('title');
      setSortOrder('desc');
    }
  };

  const handleFilterChange = (e) => {
    setFilterType(e.target.value);
  };

  const getSortValue = () => {
    return `${sortBy}-${sortOrder}`;
  };

  // Filter lectures by search query
  const filteredLectures = lectures.filter((lecture) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return lecture.title?.toLowerCase().includes(query);
  });

  return (
    <div className="lecture-history" data-testid="lecture-history">
      <div className="lecture-history-header">
        <h1 className="text-h1 lecture-history-title">Session History</h1>
        <div className="lecture-history-search">
          <input
            type="text"
            className="input-field search-input"
            placeholder="Search sessions…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search sessions"
          />
        </div>
        <div className="lecture-history-controls">
          <div className="control-group">
            <label htmlFor="filter-type" className="control-label">
              Filter:
            </label>
            <select
              id="filter-type"
              value={filterType}
              onChange={handleFilterChange}
              className="control-select"
              aria-label="Filter lectures by type"
            >
              <option value="all">All Types</option>
              <option value="live">Live Sessions</option>
              <option value="upload">Uploaded</option>
            </select>
          </div>
          <div className="control-group">
            <label htmlFor="sort-by" className="control-label">
              Sort:
            </label>
            <select
              id="sort-by"
              value={getSortValue()}
              onChange={handleSortChange}
              className="control-select"
              aria-label="Sort lectures"
            >
              <option value="date-desc">Newest First</option>
              <option value="date-asc">Oldest First</option>
              <option value="title-asc">Title A-Z</option>
              <option value="title-desc">Title Z-A</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="lecture-history-error" role="alert">
          {error}
          <button onClick={fetchLectures} className="retry-button">
            Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="lecture-history-loading" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true"></div>
          <span>Loading lectures...</span>
        </div>
      ) : lectures.length === 0 ? (
        <div className="lecture-history-empty" data-testid="empty-state">
          <span className="empty-icon" aria-hidden="true">📚</span>
          <p className="text-body empty-text">No lectures yet</p>
          <p className="text-small empty-subtext">
            Start a live captioning session or upload an audio file to get started.
          </p>
        </div>
      ) : (
        <div className="lecture-grid" data-testid="lecture-grid">
          {filteredLectures.map((lecture) => (
            <LectureCard
              key={lecture.id}
              lecture={lecture}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default LectureHistory;
