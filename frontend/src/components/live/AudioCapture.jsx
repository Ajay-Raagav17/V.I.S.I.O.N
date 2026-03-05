/**
 * AudioCapture component for microphone access and audio streaming.
 * Handles browser microphone permissions and audio data capture.
 * 
 * Requirements: 1.1 - Activate audio input for live captioning
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

/**
 * AudioCapture component
 * @param {Object} props - Component props
 * @param {boolean} props.isCapturing - Whether audio capture is active
 * @param {Function} props.onAudioData - Callback when audio data is available
 * @param {Function} props.onError - Callback when an error occurs
 * @param {Function} props.onPermissionChange - Callback when permission status changes
 */
const AudioCapture = ({ 
  isCapturing, 
  onAudioData, 
  onError, 
  onPermissionChange 
}) => {
  const [permissionStatus, setPermissionStatus] = useState('prompt'); // 'prompt', 'granted', 'denied'
  const [isInitialized, setIsInitialized] = useState(false);
  
  const mediaStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);

  /**
   * Request microphone permission and initialize audio capture
   */
  const initializeAudio = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      mediaStreamRef.current = stream;
      setPermissionStatus('granted');
      
      if (onPermissionChange) {
        onPermissionChange('granted');
      }
      
      // Create audio context
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
      
      // Create source from stream
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      
      // Create script processor for audio data
      // Note: ScriptProcessorNode is deprecated but still widely supported
      // AudioWorklet would be the modern alternative
      const bufferSize = 4096;
      processorRef.current = audioContextRef.current.createScriptProcessor(
        bufferSize, 
        1, // input channels
        1  // output channels
      );
      
      processorRef.current.onaudioprocess = (event) => {
        if (onAudioData) {
          const inputData = event.inputBuffer.getChannelData(0);
          
          // Convert Float32Array to Int16Array (16-bit PCM)
          const pcmData = float32ToInt16(inputData);
          
          onAudioData(pcmData.buffer);
        }
      };
      
      setIsInitialized(true);
      
    } catch (err) {
      console.error('Error initializing audio:', err);
      
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setPermissionStatus('denied');
        if (onPermissionChange) {
          onPermissionChange('denied');
        }
      }
      
      if (onError) {
        onError(err.message || 'Failed to access microphone');
      }
    }
  }, [onAudioData, onError, onPermissionChange]);

  /**
   * Start audio capture
   */
  const startCapture = useCallback(() => {
    if (sourceRef.current && processorRef.current && audioContextRef.current) {
      // Resume audio context if suspended
      if (audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume();
      }
      
      // Connect the audio graph
      sourceRef.current.connect(processorRef.current);
      processorRef.current.connect(audioContextRef.current.destination);
    }
  }, []);

  /**
   * Stop audio capture
   */
  const stopCapture = useCallback(() => {
    if (processorRef.current && sourceRef.current) {
      try {
        sourceRef.current.disconnect();
        processorRef.current.disconnect();
      } catch (err) {
        // Ignore disconnect errors
      }
    }
  }, []);

  /**
   * Cleanup audio resources
   */
  const cleanup = useCallback(() => {
    stopCapture();
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    processorRef.current = null;
    sourceRef.current = null;
    setIsInitialized(false);
  }, [stopCapture]);

  // Initialize audio when component mounts
  useEffect(() => {
    initializeAudio();
    
    return () => {
      cleanup();
    };
  }, [initializeAudio, cleanup]);

  // Start/stop capture based on isCapturing prop
  useEffect(() => {
    if (isInitialized) {
      if (isCapturing) {
        startCapture();
      } else {
        stopCapture();
      }
    }
  }, [isCapturing, isInitialized, startCapture, stopCapture]);

  // Render permission status indicator
  return (
    <div className="audio-capture" aria-live="polite">
      {permissionStatus === 'denied' && (
        <div className="permission-denied" role="alert">
          <span className="permission-icon">🎤</span>
          <span>Microphone access denied. Please enable microphone permissions in your browser settings.</span>
        </div>
      )}
      {permissionStatus === 'prompt' && (
        <div className="permission-prompt">
          <span className="permission-icon">🎤</span>
          <span>Requesting microphone access...</span>
        </div>
      )}
      {permissionStatus === 'granted' && isCapturing && (
        <div className="capture-active">
          <span className="recording-indicator" aria-label="Recording active"></span>
          <span>Listening...</span>
        </div>
      )}
    </div>
  );
};

/**
 * Convert Float32Array audio data to Int16Array (16-bit PCM)
 * @param {Float32Array} float32Array - Input audio data
 * @returns {Int16Array} Converted audio data
 */
function float32ToInt16(float32Array) {
  const int16Array = new Int16Array(float32Array.length);
  
  for (let i = 0; i < float32Array.length; i++) {
    // Clamp value between -1 and 1
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    // Convert to 16-bit integer
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  
  return int16Array;
}

export default AudioCapture;
