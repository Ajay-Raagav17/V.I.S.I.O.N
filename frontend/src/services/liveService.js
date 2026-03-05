/**
 * Live captioning service for WebSocket communication and session management.
 * Handles real-time audio streaming and caption receiving.
 */

import { getStoredToken } from './authService';

const API_BASE_URL = '/api/live';

/**
 * Start a new live captioning session
 * @param {string} title - Title for the lecture session
 * @returns {Promise<Object>} Session start response with session_id
 */
export const startSession = async (title) => {
  const token = getStoredToken();
  
  const response = await fetch(`${API_BASE_URL}/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ title })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start session');
  }
  
  return response.json();
};

/**
 * Stop an active live captioning session
 * @param {string} sessionId - The session ID to stop
 * @returns {Promise<Object>} Session stop response with transcript
 */
export const stopSession = async (sessionId) => {
  const token = getStoredToken();
  
  const response = await fetch(`${API_BASE_URL}/stop`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ session_id: sessionId })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop session');
  }
  
  return response.json();
};

/**
 * WebSocket connection manager for live captioning
 */
export class LiveCaptionWebSocket {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.onCaption = null;
    this.onError = null;
    this.onStatusChange = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
  }

  /**
   * Connect to the WebSocket server
   * @param {string} sessionId - The session ID to connect with
   * @returns {Promise<void>}
   */
  connect(sessionId) {
    return new Promise((resolve, reject) => {
      this.sessionId = sessionId;
      
      // Determine WebSocket URL based on current protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${API_BASE_URL}/stream`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        // Send session ID as first message
        this.ws.send(JSON.stringify({ session_id: sessionId }));
        this.reconnectAttempts = 0;
        if (this.onStatusChange) {
          this.onStatusChange('connecting');
        }
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.status === 'connected') {
            if (this.onStatusChange) {
              this.onStatusChange('connected');
            }
            resolve();
          } else if (data.error) {
            if (this.onError) {
              this.onError(data.error);
            }
            reject(new Error(data.error));
          } else if (data.text !== undefined) {
            // Caption received - could be partial or final
            if (this.onCaption) {
              this.onCaption({
                segmentId: data.segment_id,
                text: data.text,
                timestamp: data.timestamp,
                confidence: data.confidence,
                partial: data.partial || false,
                isFinal: data.is_final || false
              });
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (this.onError) {
          this.onError('WebSocket connection error');
        }
        if (this.onStatusChange) {
          this.onStatusChange('error');
        }
      };
      
      this.ws.onclose = (event) => {
        if (this.onStatusChange) {
          this.onStatusChange('disconnected');
        }
        
        // Attempt reconnection if not a clean close
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          setTimeout(() => {
            this.connect(this.sessionId).catch(console.error);
          }, 1000 * this.reconnectAttempts);
        }
      };
    });
  }

  /**
   * Send audio data to the server
   * @param {ArrayBuffer} audioData - Raw audio data to send
   */
  sendAudio(audioData) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Convert ArrayBuffer to base64
      const base64Audio = arrayBufferToBase64(audioData);
      this.ws.send(JSON.stringify({ audio: base64Audio }));
    }
  }

  /**
   * Close the WebSocket connection
   */
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Session ended');
      this.ws = null;
    }
    this.sessionId = null;
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Convert ArrayBuffer to base64 string
 * @param {ArrayBuffer} buffer - The buffer to convert
 * @returns {string} Base64 encoded string
 */
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export default {
  startSession,
  stopSession,
  LiveCaptionWebSocket
};
