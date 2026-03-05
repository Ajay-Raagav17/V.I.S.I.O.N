"""
Unit tests for audio processing pipeline.

Tests audio segmentation with various durations and segment processing pipeline.
Requirements: 4.1, 4.2
"""

import pytest
from services.audio_processing import AudioProcessingPipeline, TranscriptSegment


def test_audio_segmentation_10_seconds():
    """Test segmentation of exactly 10 seconds of audio."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # 10 seconds of 16kHz mono 16-bit audio
    bytes_per_second = 16000 * 1 * 2
    audio_data = b'\x00' * (bytes_per_second * 10)
    
    segments = list(pipeline.segment_audio(audio_data))
    
    assert len(segments) == 1
    assert len(segments[0]) == bytes_per_second * 10


def test_audio_segmentation_25_seconds():
    """Test segmentation of 25 seconds of audio (2.5 segments)."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # 25 seconds of 16kHz mono 16-bit audio
    bytes_per_second = 16000 * 1 * 2
    audio_data = b'\x00' * (bytes_per_second * 25)
    
    segments = list(pipeline.segment_audio(audio_data))
    
    assert len(segments) == 3
    assert len(segments[0]) == bytes_per_second * 10
    assert len(segments[1]) == bytes_per_second * 10
    assert len(segments[2]) == bytes_per_second * 5


def test_audio_segmentation_empty():
    """Test segmentation of empty audio."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    audio_data = b''
    segments = list(pipeline.segment_audio(audio_data))
    
    assert len(segments) == 0


def test_audio_segmentation_less_than_one_segment():
    """Test segmentation of audio shorter than segment duration."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # 5 seconds of 16kHz mono 16-bit audio
    bytes_per_second = 16000 * 1 * 2
    audio_data = b'\x00' * (bytes_per_second * 5)
    
    segments = list(pipeline.segment_audio(audio_data))
    
    assert len(segments) == 1
    assert len(segments[0]) == bytes_per_second * 5


def test_audio_segmentation_different_sample_rates():
    """Test segmentation with different sample rates."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # Test with 8kHz
    bytes_per_second_8k = 8000 * 1 * 2
    audio_data_8k = b'\x00' * (bytes_per_second_8k * 10)
    segments_8k = list(pipeline.segment_audio(audio_data_8k, sample_rate=8000))
    assert len(segments_8k) == 1
    
    # Test with 44.1kHz
    bytes_per_second_44k = 44100 * 1 * 2
    audio_data_44k = b'\x00' * (bytes_per_second_44k * 10)
    segments_44k = list(pipeline.segment_audio(audio_data_44k, sample_rate=44100))
    assert len(segments_44k) == 1


def test_process_segment_without_transcription():
    """Test processing a segment without transcription function."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    segment = b'\x00' * 1000
    result = pipeline.process_segment(segment, segment_id=0)
    
    assert isinstance(result, TranscriptSegment)
    assert result.segment_id == 0
    assert result.text == ""
    assert result.confidence == 0.0
    assert result.timestamp == 0.0


def test_process_segment_with_transcription():
    """Test processing a segment with transcription function."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    def mock_transcription(segment_bytes):
        return "Hello world", 0.95
    
    segment = b'\x00' * 1000
    result = pipeline.process_segment(segment, segment_id=2, transcription_func=mock_transcription)
    
    assert isinstance(result, TranscriptSegment)
    assert result.segment_id == 2
    assert result.text == "Hello world"
    assert result.confidence == 0.95
    assert result.timestamp == 20.0  # segment_id * segment_duration


def test_process_live_stream_single_segment():
    """Test processing a live stream with a single segment."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    def mock_transcription(segment_bytes):
        return f"Segment {len(segment_bytes)} bytes", 0.9
    
    # Single chunk that forms one complete segment
    bytes_per_segment = 16000 * 1 * 2 * 10
    audio_stream = [b'\x00' * bytes_per_segment]
    
    results = list(pipeline.process_live_stream(audio_stream, transcription_func=mock_transcription))
    
    assert len(results) == 1
    assert results[0].segment_id == 0
    assert "bytes" in results[0].text


def test_process_live_stream_multiple_chunks():
    """Test processing a live stream with multiple chunks."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    def mock_transcription(segment_bytes):
        return f"Segment", 0.9
    
    # Multiple small chunks that form segments
    chunk_size = 16000 * 1 * 2 * 5  # 5 seconds per chunk
    audio_stream = [b'\x00' * chunk_size for _ in range(5)]  # 25 seconds total
    
    results = list(pipeline.process_live_stream(audio_stream, transcription_func=mock_transcription))
    
    assert len(results) == 3  # 25 seconds / 10 seconds = 2.5 -> 3 segments
    assert results[0].segment_id == 0
    assert results[1].segment_id == 1
    assert results[2].segment_id == 2


def test_calculate_segment_count():
    """Test segment count calculation."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    assert pipeline.calculate_segment_count(0) == 0
    assert pipeline.calculate_segment_count(5) == 1
    assert pipeline.calculate_segment_count(10) == 1
    assert pipeline.calculate_segment_count(10.1) == 2
    assert pipeline.calculate_segment_count(20) == 2
    assert pipeline.calculate_segment_count(25) == 3
    assert pipeline.calculate_segment_count(100) == 10


def test_get_segment_duration_seconds():
    """Test segment duration calculation."""
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # 10 seconds of 16kHz mono 16-bit audio
    bytes_per_second = 16000 * 1 * 2
    segment_10s = b'\x00' * (bytes_per_second * 10)
    
    duration = pipeline.get_segment_duration_seconds(segment_10s)
    assert abs(duration - 10.0) < 0.01
    
    # 5 seconds
    segment_5s = b'\x00' * (bytes_per_second * 5)
    duration = pipeline.get_segment_duration_seconds(segment_5s)
    assert abs(duration - 5.0) < 0.01


def test_custom_segment_duration():
    """Test pipeline with custom segment duration."""
    pipeline = AudioProcessingPipeline(segment_duration=5)
    
    # 15 seconds of audio with 5-second segments
    bytes_per_second = 16000 * 1 * 2
    audio_data = b'\x00' * (bytes_per_second * 15)
    
    segments = list(pipeline.segment_audio(audio_data))
    
    assert len(segments) == 3
    for segment in segments:
        assert len(segment) == bytes_per_second * 5
