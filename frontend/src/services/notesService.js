/**
 * Notes Service - API integration for notes endpoints
 * Requirements: 3.5, 5.5
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Fetch notes for a specific lecture
 * @param {string} lectureId - The lecture ID
 * @returns {Promise<Object>} - The notes data
 */
export const getNotes = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/notes/${lectureId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to fetch notes');
  }

  return response.json();
};

/**
 * Download PDF for a specific lecture
 * @param {string} lectureId - The lecture ID
 * @returns {Promise<Blob>} - The PDF blob
 */
export const downloadPDF = async (lectureId) => {
  const response = await fetch(`${API_BASE_URL}/notes/${lectureId}/pdf`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Failed to download PDF');
  }

  return response.blob();
};

/**
 * Trigger PDF download in browser
 * @param {string} lectureId - The lecture ID
 * @param {string} filename - Optional filename for the download
 */
export const triggerPDFDownload = async (lectureId, filename = 'lecture-notes.pdf') => {
  const blob = await downloadPDF(lectureId);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default {
  getNotes,
  downloadPDF,
  triggerPDFDownload,
};
