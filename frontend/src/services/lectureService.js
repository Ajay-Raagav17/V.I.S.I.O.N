/**
 * Lecture Service - API integration for lecture history endpoints
 * Requirements: 6.4, 6.5
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Get authorization headers
 * @returns {Object} Headers object with authorization
 */
const getAuthHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
});

/**
 * Fetch all lectures for the current user
 * @param {Object} options - Query options
 * @param {string} options.sortBy - Sort field ('date', 'title')
 * @param {string} options.sortOrder - Sort order ('asc', 'desc')
 * @param {string} options.filterType - Filter by lecture type ('all', 'live', 'upload')
 * @returns {Promise<Array>} - Array of lecture objects
 */
export const getLectures = async ({ sortBy = 'date', sortOrder = 'desc', filterType = 'all' } = {}) => {
  const params = new URLSearchParams();
  if (sortBy) params.append('sort_by', sortBy);
  if (sortOrder) params.append('sort_order', sortOrder);
  if (filterType && filterType !== 'all') params.append('type', filterType);

  const response = await fetch(`${API_BASE_URL}/lectures?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch lectures');
  }

  return response.json();
};

/**
 * Get a specific lecture by ID
 * @param {string} lectureId - The lecture ID
 * @returns {Promise<Object>} - The lecture object
 */
export const getLecture = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/lectures/${lectureId}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch lecture');
  }

  return response.json();
};

/**
 * Delete a lecture by ID
 * @param {string} lectureId - The lecture ID to delete
 * @returns {Promise<Object>} - Deletion confirmation
 */
export const deleteLecture = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/lectures/${lectureId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to delete lecture');
  }

  return response.json();
};

/**
 * Format lecture date for display
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date string
 */
export const formatLectureDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Format lecture duration for display
 * @param {number} seconds - Duration in seconds
 * @returns {string} - Formatted duration string
 */
export const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Create a shareable link for a lecture
 * @param {string} lectureId - The lecture ID
 * @returns {Promise<Object>} - Share token and URL
 */
export const createShareLink = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/lectures/${lectureId}/share`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to create share link');
  }

  return response.json();
};

/**
 * Revoke a shareable link for a lecture
 * @param {string} lectureId - The lecture ID
 * @returns {Promise<Object>} - Success message
 */
export const revokeShareLink = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/lectures/${lectureId}/share`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to revoke share link');
  }

  return response.json();
};

/**
 * Get a shared lecture by token (no auth required)
 * @param {string} shareToken - The share token
 * @returns {Promise<Object>} - The shared lecture data
 */
export const getSharedLecture = async (shareToken) => {
  const response = await fetch(`${API_BASE_URL}/lectures/shared/${shareToken}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Failed to fetch shared lecture');
  }

  return response.json();
};

export default {
  getLectures,
  getLecture,
  deleteLecture,
  formatLectureDate,
  formatDuration,
  createShareLink,
  revokeShareLink,
  getSharedLecture,
};
