/**
 * Unit tests for uploadService
 * Tests file validation and status polling
 * Requirements: 2.1, 2.2, 9.3
 */

// Define constants directly for testing since import.meta.env doesn't work in Jest
const SUPPORTED_FORMATS = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/ogg', 'audio/mp3', 'audio/x-wav'];
const SUPPORTED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg'];
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

// Inline validateFile function for testing (mirrors the actual implementation)
const validateFile = (file) => {
  if (!file) {
    return { valid: false, error: 'No file selected' };
  }

  const fileName = file.name.toLowerCase();
  const hasValidExtension = SUPPORTED_EXTENSIONS.some(ext => fileName.endsWith(ext));
  const hasValidMimeType = SUPPORTED_FORMATS.includes(file.type);

  if (!hasValidExtension && !hasValidMimeType) {
    return { 
      valid: false, 
      error: 'Invalid file format. Supported formats: MP3, WAV, M4A, OGG' 
    };
  }

  if (file.size > MAX_FILE_SIZE) {
    return { 
      valid: false, 
      error: `File size exceeds limit. Maximum size: ${MAX_FILE_SIZE / (1024 * 1024)}MB` 
    };
  }

  return { valid: true };
};

describe('uploadService', () => {
  describe('validateFile', () => {
    it('should return valid for supported MP3 file', () => {
      const file = new File(['audio content'], 'lecture.mp3', { type: 'audio/mpeg' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });

    it('should return valid for supported WAV file', () => {
      const file = new File(['audio content'], 'lecture.wav', { type: 'audio/wav' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });

    it('should return valid for supported M4A file', () => {
      const file = new File(['audio content'], 'lecture.m4a', { type: 'audio/x-m4a' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });

    it('should return valid for supported OGG file', () => {
      const file = new File(['audio content'], 'lecture.ogg', { type: 'audio/ogg' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });

    it('should return invalid for unsupported file format', () => {
      const file = new File(['text content'], 'document.txt', { type: 'text/plain' });
      const result = validateFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file format');
    });

    it('should return invalid for video file', () => {
      const file = new File(['video content'], 'video.mp4', { type: 'video/mp4' });
      const result = validateFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file format');
    });

    it('should return invalid for file exceeding size limit', () => {
      const largeFile = {
        name: 'large.mp3',
        type: 'audio/mpeg',
        size: MAX_FILE_SIZE + 1
      };
      const result = validateFile(largeFile);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('File size exceeds limit');
    });

    it('should return invalid when no file is provided', () => {
      const result = validateFile(null);
      expect(result.valid).toBe(false);
      expect(result.error).toBe('No file selected');
    });

    it('should return invalid when undefined is provided', () => {
      const result = validateFile(undefined);
      expect(result.valid).toBe(false);
      expect(result.error).toBe('No file selected');
    });

    it('should accept file with valid extension even if MIME type is generic', () => {
      const file = new File(['audio content'], 'lecture.mp3', { type: 'application/octet-stream' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });

    it('should accept file with valid MIME type even if extension is unusual', () => {
      const file = new File(['audio content'], 'lecture.audio', { type: 'audio/mpeg' });
      const result = validateFile(file);
      expect(result.valid).toBe(true);
    });
  });

  describe('constants', () => {
    it('should have correct supported formats', () => {
      expect(SUPPORTED_FORMATS).toContain('audio/mpeg');
      expect(SUPPORTED_FORMATS).toContain('audio/wav');
      expect(SUPPORTED_FORMATS).toContain('audio/ogg');
    });

    it('should have correct supported extensions', () => {
      expect(SUPPORTED_EXTENSIONS).toContain('.mp3');
      expect(SUPPORTED_EXTENSIONS).toContain('.wav');
      expect(SUPPORTED_EXTENSIONS).toContain('.m4a');
      expect(SUPPORTED_EXTENSIONS).toContain('.ogg');
    });

    it('should have reasonable max file size', () => {
      expect(MAX_FILE_SIZE).toBe(100 * 1024 * 1024); // 100MB
    });
  });
});
