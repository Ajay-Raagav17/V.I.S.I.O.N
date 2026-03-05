"""Audio processing pipeline for segmentation and real-time streaming."""

from typing import Iterator, List
from dataclasses import dataclass
from datetime import datetime
import io

from services.error_handling import (
    ProcessingError,
    log_error,
    log_info,
    log_warning
)


@dataclass
class TranscriptSegment:
    """Represents a transcribed audio segment."""
    segment_id: int
    text: str
    timestamp: float
    confidence: float


class AudioProcessingPipeline:
    """
    Pipeline for processing audio streams with segmentation.
    
    Handles:
    - Audio segmentation into fixed-duration chunks
    - Individual segment processing
    - Real-time stream processing
    """
    
    def __init__(self, segment_duration: int = 10):
        """
        Initialize the audio processing pipeline.
        
        Args:
            segment_duration: Duration of each segment in seconds (default: 10)
        """
        self.segment_duration = segment_duration
    
    def segment_audio(self, audio_data: bytes, sample_rate: int = 16000, 
                     channels: int = 1, sample_width: int = 2) -> Iterator[bytes]:
        """
        Split audio data into fixed-duration segments.
        
        Args:
            audio_data: Raw audio data as bytes
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
            
        Yields:
            Audio segment as bytes
            
        Raises:
            ProcessingError: If audio data is invalid
            
        Requirements: 4.1
        """
        try:
            # Calculate bytes per second
            bytes_per_second = sample_rate * channels * sample_width
            
            # Calculate bytes per segment (ensure integer)
            bytes_per_segment = int(bytes_per_second * self.segment_duration)
            
            # Split audio into segments
            total_bytes = len(audio_data)
            offset = 0
            segment_count = 0
            
            while offset < total_bytes:
                end = min(offset + bytes_per_segment, total_bytes)
                segment = audio_data[offset:end]
                yield segment
                offset = end
                segment_count += 1
            
            log_info(
                "Audio segmentation completed",
                context={
                    "total_bytes": total_bytes,
                    "segment_count": segment_count,
                    "segment_duration": self.segment_duration
                }
            )
            
        except Exception as e:
            log_error(e, context={"operation": "audio_segmentation"})
            raise ProcessingError(
                operation="Audio",
                message=f"Failed to segment audio: {str(e)}",
                original_exception=e
            )
    
    def process_segment(self, segment: bytes, segment_id: int, 
                       transcription_func=None) -> TranscriptSegment:
        """
        Process a single audio segment through transcription.
        
        Args:
            segment: Audio segment as bytes
            segment_id: Unique identifier for this segment
            transcription_func: Optional function to transcribe audio
                              (for testing, can be None)
            
        Returns:
            TranscriptSegment with transcribed text
            
        Raises:
            ProcessingError: If segment processing fails
            
        Requirements: 4.2
        """
        try:
            # If no transcription function provided, return empty segment
            # (In production, this would call the actual transcription service)
            if transcription_func is None:
                return TranscriptSegment(
                    segment_id=segment_id,
                    text="",
                    timestamp=segment_id * self.segment_duration,
                    confidence=0.0
                )
            
            # Call the transcription function
            text, confidence = transcription_func(segment)
            
            log_info(
                f"Segment {segment_id} processed",
                context={
                    "segment_id": segment_id,
                    "text_length": len(text),
                    "confidence": confidence
                }
            )
            
            return TranscriptSegment(
                segment_id=segment_id,
                text=text,
                timestamp=segment_id * self.segment_duration,
                confidence=confidence
            )
            
        except Exception as e:
            log_error(e, context={
                "operation": "segment_processing",
                "segment_id": segment_id
            })
            raise ProcessingError(
                operation="Audio",
                message=f"Failed to process segment {segment_id}: {str(e)}",
                details={"segment_id": segment_id},
                original_exception=e
            )
    
    def process_live_stream(self, audio_stream: Iterator[bytes], 
                           transcription_func=None) -> Iterator[TranscriptSegment]:
        """
        Process a live audio stream with real-time segmentation and transcription.
        
        Args:
            audio_stream: Iterator yielding audio chunks
            transcription_func: Optional function to transcribe audio segments
            
        Yields:
            TranscriptSegment for each processed segment
            
        Requirements: 1.4, 4.1, 4.2
        """
        segment_id = 0
        buffer = bytearray()
        
        # Assume 16kHz, mono, 16-bit audio
        bytes_per_segment = 16000 * 1 * 2 * self.segment_duration
        
        for chunk in audio_stream:
            buffer.extend(chunk)
            
            # Process complete segments
            while len(buffer) >= bytes_per_segment:
                segment = bytes(buffer[:bytes_per_segment])
                buffer = buffer[bytes_per_segment:]
                
                # Process the segment
                transcript_segment = self.process_segment(
                    segment, segment_id, transcription_func
                )
                
                yield transcript_segment
                segment_id += 1
        
        # Process remaining buffer if any
        if len(buffer) > 0:
            segment = bytes(buffer)
            transcript_segment = self.process_segment(
                segment, segment_id, transcription_func
            )
            yield transcript_segment
    
    def calculate_segment_count(self, audio_duration_seconds: float) -> int:
        """
        Calculate the expected number of segments for a given audio duration.
        
        Args:
            audio_duration_seconds: Duration of audio in seconds
            
        Returns:
            Expected number of segments (ceiling division)
            
        Requirements: 4.1
        """
        import math
        return math.ceil(audio_duration_seconds / self.segment_duration)
    
    def get_segment_duration_seconds(self, segment_bytes: bytes, 
                                    sample_rate: int = 16000,
                                    channels: int = 1, 
                                    sample_width: int = 2) -> float:
        """
        Calculate the duration of an audio segment in seconds.
        
        Args:
            segment_bytes: Audio segment as bytes
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            sample_width: Sample width in bytes
            
        Returns:
            Duration in seconds
        """
        bytes_per_second = sample_rate * channels * sample_width
        return len(segment_bytes) / bytes_per_second
