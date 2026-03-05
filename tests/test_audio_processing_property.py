"""
Property-based tests for audio processing pipeline.

**Feature: vision-accessibility, Property 4: Audio segmentation consistency**
**Validates: Requirements 4.1**

**Feature: vision-accessibility, Property 1: Complete segment processing**
**Validates: Requirements 1.4, 4.2**
"""

import pytest
import math
from hypothesis import given, strategies as st, settings, assume
from services.audio_processing import AudioProcessingPipeline, TranscriptSegment


# Strategy for generating audio durations (in seconds)
# Range from 0.1 seconds to 120 seconds (2 minutes)
audio_duration_strategy = st.floats(min_value=0.1, max_value=120.0, allow_nan=False, allow_infinity=False)

# Strategy for segment durations (typically 10 seconds, but test with variations)
segment_duration_strategy = st.integers(min_value=1, max_value=30)

# Strategy for sample rates (common audio sample rates)
sample_rate_strategy = st.sampled_from([8000, 16000, 22050, 44100, 48000])

# Strategy for channels (mono or stereo)
channels_strategy = st.integers(min_value=1, max_value=2)

# Strategy for sample width (8-bit, 16-bit, 24-bit, 32-bit)
sample_width_strategy = st.sampled_from([1, 2, 3, 4])


@pytest.fixture
def audio_pipeline():
    """Create an AudioProcessingPipeline instance."""
    return AudioProcessingPipeline(segment_duration=10)


@settings(max_examples=100, deadline=None)
@given(
    audio_duration=audio_duration_strategy,
    sample_rate=sample_rate_strategy,
    channels=channels_strategy,
    sample_width=sample_width_strategy
)
def test_audio_segmentation_consistency(audio_duration, sample_rate, channels, sample_width):
    """
    Property 4: Audio segmentation consistency
    
    For any audio stream of duration D seconds, segmenting with 10-second 
    intervals should produce exactly ⌈D/10⌉ segments, with each segment 
    (except possibly the last) being 10 seconds in duration.
    
    **Feature: vision-accessibility, Property 4: Audio segmentation consistency**
    **Validates: Requirements 4.1**
    """
    segment_duration = 10
    pipeline = AudioProcessingPipeline(segment_duration=segment_duration)
    
    # Calculate expected number of segments
    expected_segment_count = math.ceil(audio_duration / segment_duration)
    
    # Generate synthetic audio data
    bytes_per_second = sample_rate * channels * sample_width
    total_bytes = int(audio_duration * bytes_per_second)
    audio_data = b'\x00' * total_bytes
    
    # Segment the audio
    segments = list(pipeline.segment_audio(
        audio_data, 
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width
    ))
    
    # Property 1: Number of segments should match expected count
    assert len(segments) == expected_segment_count, \
        f"Expected {expected_segment_count} segments for {audio_duration}s audio, got {len(segments)}"
    
    # Property 2: All segments except possibly the last should be exactly segment_duration seconds
    bytes_per_segment = bytes_per_second * segment_duration
    
    for i, segment in enumerate(segments[:-1]):  # All but last segment
        assert len(segment) == bytes_per_segment, \
            f"Segment {i} should be {bytes_per_segment} bytes (exactly {segment_duration}s), got {len(segment)}"
    
    # Property 3: Last segment should be <= segment_duration seconds
    if len(segments) > 0:
        last_segment = segments[-1]
        assert len(last_segment) <= bytes_per_segment, \
            f"Last segment should be <= {bytes_per_segment} bytes, got {len(last_segment)}"
        assert len(last_segment) > 0, \
            "Last segment should not be empty"
    
    # Property 4: Total bytes should be preserved
    total_segmented_bytes = sum(len(seg) for seg in segments)
    assert total_segmented_bytes == total_bytes, \
        f"Total bytes should be preserved: expected {total_bytes}, got {total_segmented_bytes}"


@settings(max_examples=100, deadline=None)
@given(
    audio_duration=audio_duration_strategy,
    segment_duration=segment_duration_strategy,
    sample_rate=sample_rate_strategy
)
def test_segment_count_calculation(audio_duration, segment_duration, sample_rate):
    """
    Property: Segment count calculation should match actual segmentation.
    
    The calculate_segment_count method should return the same number of 
    segments as actually produced by segment_audio when given the actual
    byte-based duration.
    
    **Feature: vision-accessibility, Property 4: Audio segmentation consistency**
    **Validates: Requirements 4.1**
    """
    pipeline = AudioProcessingPipeline(segment_duration=segment_duration)
    
    # Generate audio and segment it
    bytes_per_second = sample_rate * 1 * 2  # mono, 16-bit
    total_bytes = int(audio_duration * bytes_per_second)
    audio_data = b'\x00' * total_bytes
    
    # Calculate actual duration based on bytes (this handles truncation)
    actual_duration = total_bytes / bytes_per_second
    
    # Calculate expected count based on actual duration
    expected_count = pipeline.calculate_segment_count(actual_duration)
    
    segments = list(pipeline.segment_audio(
        audio_data,
        sample_rate=sample_rate,
        channels=1,
        sample_width=2
    ))
    
    # Property: Calculated count should match actual count
    assert len(segments) == expected_count, \
        f"Calculated segment count {expected_count} should match actual count {len(segments)}"


@settings(max_examples=100, deadline=None)
@given(
    num_chunks=st.integers(min_value=1, max_value=50),
    chunk_size=st.integers(min_value=1000, max_value=50000)
)
def test_complete_segment_processing(num_chunks, chunk_size):
    """
    Property 1: Complete segment processing
    
    For any audio stream, when divided into segments, every segment should 
    produce a transcript output with no segments skipped or dropped.
    
    **Feature: vision-accessibility, Property 1: Complete segment processing**
    **Validates: Requirements 1.4, 4.2**
    """
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # Create a mock transcription function that returns segment info
    def mock_transcription(segment_bytes):
        return f"Transcribed {len(segment_bytes)} bytes", 0.95
    
    # Generate audio stream as iterator
    def audio_stream_generator():
        for i in range(num_chunks):
            yield b'\x00' * chunk_size
    
    # Process the stream
    transcript_segments = list(pipeline.process_live_stream(
        audio_stream_generator(),
        transcription_func=mock_transcription
    ))
    
    # Property 1: Every segment should produce output (no segments dropped)
    # Calculate expected number of segments
    total_bytes = num_chunks * chunk_size
    bytes_per_segment = 16000 * 1 * 2 * 10  # 16kHz, mono, 16-bit, 10 seconds
    expected_segments = math.ceil(total_bytes / bytes_per_segment)
    
    assert len(transcript_segments) == expected_segments, \
        f"Expected {expected_segments} transcript segments, got {len(transcript_segments)}"
    
    # Property 2: All segments should have sequential IDs (no gaps)
    for i, segment in enumerate(transcript_segments):
        assert segment.segment_id == i, \
            f"Segment ID should be {i}, got {segment.segment_id}"
    
    # Property 3: All segments should have non-empty text (since we provided transcription)
    for segment in transcript_segments:
        assert len(segment.text) > 0, \
            f"Segment {segment.segment_id} should have transcribed text"
    
    # Property 4: All segments should have confidence scores
    for segment in transcript_segments:
        assert 0.0 <= segment.confidence <= 1.0, \
            f"Segment {segment.segment_id} confidence should be between 0 and 1"


@settings(max_examples=100, deadline=None)
@given(
    audio_duration=audio_duration_strategy,
    sample_rate=sample_rate_strategy
)
def test_segment_duration_calculation(audio_duration, sample_rate):
    """
    Property: Segment duration calculation should be accurate.
    
    For any audio segment, calculating its duration should match the 
    expected duration based on its byte size.
    
    **Feature: vision-accessibility, Property 4: Audio segmentation consistency**
    **Validates: Requirements 4.1**
    """
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # Generate audio data
    channels = 1
    sample_width = 2
    bytes_per_second = sample_rate * channels * sample_width
    total_bytes = int(audio_duration * bytes_per_second)
    audio_data = b'\x00' * total_bytes
    
    # Segment the audio
    segments = list(pipeline.segment_audio(
        audio_data,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width
    ))
    
    # Property: Sum of all segment durations should equal original duration
    total_calculated_duration = sum(
        pipeline.get_segment_duration_seconds(
            seg, sample_rate, channels, sample_width
        )
        for seg in segments
    )
    
    # Allow small floating point error (within 0.01 seconds)
    assert abs(total_calculated_duration - audio_duration) < 0.01, \
        f"Total calculated duration {total_calculated_duration}s should match original {audio_duration}s"


@settings(max_examples=100, deadline=None)
@given(
    segment_bytes=st.integers(min_value=1, max_value=1000000)
)
def test_process_segment_always_returns_result(segment_bytes):
    """
    Property: process_segment should always return a TranscriptSegment.
    
    For any audio segment, process_segment should always return a valid 
    TranscriptSegment object, never None or raise an exception.
    
    **Feature: vision-accessibility, Property 1: Complete segment processing**
    **Validates: Requirements 1.4, 4.2**
    """
    pipeline = AudioProcessingPipeline(segment_duration=10)
    
    # Create synthetic segment
    segment = b'\x00' * segment_bytes
    segment_id = 0
    
    # Process without transcription function
    result = pipeline.process_segment(segment, segment_id)
    
    # Property: Result should be a TranscriptSegment
    assert isinstance(result, TranscriptSegment), \
        "process_segment should return TranscriptSegment"
    assert result.segment_id == segment_id, \
        "Segment ID should match input"
    
    # Process with transcription function
    def mock_transcription(seg):
        return "test", 0.9
    
    result_with_transcription = pipeline.process_segment(
        segment, segment_id, transcription_func=mock_transcription
    )
    
    # Property: Result should be a TranscriptSegment with transcribed text
    assert isinstance(result_with_transcription, TranscriptSegment), \
        "process_segment should return TranscriptSegment"
    assert result_with_transcription.text == "test", \
        "Transcribed text should match mock output"
    assert result_with_transcription.confidence == 0.9, \
        "Confidence should match mock output"
