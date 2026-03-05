/**
 * SegmentProcessor for client-side audio chunking.
 * Handles audio segmentation into 10-second chunks for processing.
 * 
 * Requirements: 4.1 - Audio stream segmentation into 10-second segments
 */

/**
 * Audio segment processor class
 * Buffers incoming audio data and emits complete segments
 */
export class SegmentProcessor {
  /**
   * Create a new SegmentProcessor
   * @param {Object} options - Configuration options
   * @param {number} options.segmentDuration - Duration of each segment in seconds (default: 10)
   * @param {number} options.sampleRate - Audio sample rate in Hz (default: 16000)
   * @param {number} options.channels - Number of audio channels (default: 1)
   * @param {number} options.sampleWidth - Bytes per sample (default: 2 for 16-bit)
   */
  constructor(options = {}) {
    this.segmentDuration = options.segmentDuration || 10;
    this.sampleRate = options.sampleRate || 16000;
    this.channels = options.channels || 1;
    this.sampleWidth = options.sampleWidth || 2;
    
    // Calculate bytes per segment
    this.bytesPerSegment = this.sampleRate * this.channels * this.sampleWidth * this.segmentDuration;
    
    // Audio buffer
    this.buffer = new Uint8Array(0);
    
    // Segment counter
    this.segmentCount = 0;
    
    // Callback for when a segment is ready
    this.onSegment = null;
  }

  /**
   * Add audio data to the buffer
   * @param {ArrayBuffer|Uint8Array} audioData - Raw audio data
   */
  addData(audioData) {
    const newData = audioData instanceof Uint8Array 
      ? audioData 
      : new Uint8Array(audioData);
    
    // Concatenate with existing buffer
    const combined = new Uint8Array(this.buffer.length + newData.length);
    combined.set(this.buffer);
    combined.set(newData, this.buffer.length);
    this.buffer = combined;
    
    // Process complete segments
    this.processSegments();
  }

  /**
   * Process and emit complete segments from the buffer
   */
  processSegments() {
    while (this.buffer.length >= this.bytesPerSegment) {
      // Extract segment
      const segment = this.buffer.slice(0, this.bytesPerSegment);
      
      // Remove segment from buffer
      this.buffer = this.buffer.slice(this.bytesPerSegment);
      
      // Emit segment
      if (this.onSegment) {
        this.onSegment({
          segmentId: this.segmentCount,
          data: segment.buffer,
          timestamp: this.segmentCount * this.segmentDuration,
          duration: this.segmentDuration
        });
      }
      
      this.segmentCount++;
    }
  }

  /**
   * Flush any remaining data in the buffer as a final segment
   * @returns {Object|null} Final segment or null if buffer is empty
   */
  flush() {
    if (this.buffer.length > 0) {
      const segment = {
        segmentId: this.segmentCount,
        data: this.buffer.buffer,
        timestamp: this.segmentCount * this.segmentDuration,
        duration: this.buffer.length / (this.sampleRate * this.channels * this.sampleWidth),
        isFinal: true
      };
      
      this.segmentCount++;
      this.buffer = new Uint8Array(0);
      
      if (this.onSegment) {
        this.onSegment(segment);
      }
      
      return segment;
    }
    return null;
  }

  /**
   * Reset the processor state
   */
  reset() {
    this.buffer = new Uint8Array(0);
    this.segmentCount = 0;
  }

  /**
   * Get the current buffer size in bytes
   * @returns {number}
   */
  getBufferSize() {
    return this.buffer.length;
  }

  /**
   * Get the number of segments processed
   * @returns {number}
   */
  getSegmentCount() {
    return this.segmentCount;
  }

  /**
   * Get the progress towards the next segment (0-1)
   * @returns {number}
   */
  getSegmentProgress() {
    return this.buffer.length / this.bytesPerSegment;
  }
}

export default SegmentProcessor;
