/**
 * Upload Service
 * Handles audio file uploads and status polling
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */

import axios from 'axios';

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '/api';

// Supported audio formats
export const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/ogg', 'audio/mp3', 'audio/x-wav'];
export const SUPPORTED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg'];
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

/**
 * Validate file format and size
 * @param {File} file - The file to validate
 * @returns {{ valid: boolean, error?: string }}
 */
export const validateFile = (file) => {
  if (!file) {
    return { valid: false, error: 'No file selected' };
  }

  // Check file extension
  const fileName = file.name.toLowerCase();
  const hasValidExtension = SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext));
  
  // Check MIME type
  const hasValidMimeType = SUPPORTED_FORMATS.includes(file.type);

  if (!hasValidExtension && !hasValidMimeType) {
    return { 
      valid: false, 
      error: 'Invalid file format. Supported formats: MP3, WAV, M4A, OGG' 
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return { 
      valid: false, 
      error: `File size exceeds limit. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB` 
    };
  }

  return { valid: true };
};

/**
 * Upload audio file
 * @param {File} file - The audio file to upload
 * @param {string} title - Lecture title
 * @param {function} onProgress - Progress callback (0-100)
 * @returns {Promise<{ uploadId: string }>}
 */
export const uploadAudio = async (file, title, onProgress = () => {}) => {
  const validation = validateFile(file);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  const formData = new FormData();
  formData.append('audio', file);
  formData.append('title', title);

  const response = await axios.post(`${API_BASE_URL}/upload/audio`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    },
  });

  return response.data;
};

/**
 * Get upload/processing status
 * @param {string} uploadId - The upload ID to check
 * @returns {Promise<{ status: string, progress?: number, error?: string }>}
 */
export const getUploadStatus = async (uploadId) => {
  const response = await axios.get(`${API_BASE_URL}/upload/status/${uploadId}`);
  return response.data;
};

/**
 * Poll for upload status until complete or failed
 * @param {string} uploadId - The upload ID to poll
 * @param {function} onStatusChange - Callback for status updates
 * @param {number} interval - Polling interval in ms (default: 2000)
 * @returns {Promise<{ status: string, lectureId?: string }>}
 */
export const pollUploadStatus = async (uploadId, onStatusChange = () => {}, interval = 2000) => {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getUploadStatus(uploadId);
        onStatusChange(status);

        if (status.status === 'completed') {
          resolve(status);
        } else if (status.status === 'failed') {
          reject(new Error(status.error || 'Processing failed'));
        } else {
          setTimeout(poll, interval);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
};

export default {
  validateFile,
  uploadAudio,
  getUploadStatus,
  pollUploadStatus,
  SUPPORTED_FORMATS,
  SUPPORTED_EXTENSIONS,
  MAX_FILE_SIZE,
};
