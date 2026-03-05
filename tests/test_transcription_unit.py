"""
Unit tests for AssemblyAI transcription service.

Tests the TranscriptionService class that uses AssemblyAI for speech-to-text.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from services.transcription_service import TranscriptionService, AssemblyAIRealtime
from services.error_handling import ExternalAPIError


@pytest.fixture
def transcription_service():
    """Create a TranscriptionService instance with mocked API key."""
    with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_api_key'}):
        service = TranscriptionService()
        yield service


@pytest.fixture
def transcription_service_no_key():
    """Create a TranscriptionService instance without API key."""
    with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': ''}, clear=False):
        # Remove the key if it exists
        env_copy = os.environ.copy()
        if 'ASSEMBLYAI_API_KEY' in env_copy:
            del env_copy['ASSEMBLYAI_API_KEY']
        with patch.dict(os.environ, env_copy, clear=True):
            service = TranscriptionService()
            yield service


class TestAPIInitialization:
    """Tests for service initialization."""
    
    def test_service_initialization_with_api_key(self):
        """Service should initialize correctly with API key."""
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key_123'}):
            service = TranscriptionService()
            assert service.api_key == 'test_key_123'
            assert service.headers['authorization'] == 'test_key_123'
    
    def test_service_initialization_without_api_key(self):
        """Service should initialize but warn when no API key."""
        env = os.environ.copy()
        env.pop('ASSEMBLYAI_API_KEY', None)
        with patch.dict(os.environ, env, clear=True):
            with patch.dict(os.environ, {'MAX_UPLOAD_SIZE_MB': '100'}):
                service = TranscriptionService()
                assert service.api_key is None or service.api_key == ''
    
    def test_base_url_is_correct(self, transcription_service):
        """Base URL should point to AssemblyAI API."""
        assert transcription_service.BASE_URL == "https://api.assemblyai.com/v2"


class TestAudioFormatValidation:
    """Tests for audio format validation."""
    
    def test_validate_mp3_format(self, transcription_service):
        """MP3 format should be accepted."""
        assert transcription_service.validate_audio_format("test.mp3") is True
    
    def test_validate_wav_format(self, transcription_service):
        """WAV format should be accepted."""
        assert transcription_service.validate_audio_format("test.wav") is True
    
    def test_validate_m4a_format(self, transcription_service):
        """M4A format should be accepted."""
        assert transcription_service.validate_audio_format("test.m4a") is True
    
    def test_validate_ogg_format(self, transcription_service):
        """OGG format should be accepted."""
        assert transcription_service.validate_audio_format("test.ogg") is True
    
    def test_validate_webm_format(self, transcription_service):
        """WebM format should be accepted."""
        assert transcription_service.validate_audio_format("test.webm") is True
    
    def test_validate_flac_format(self, transcription_service):
        """FLAC format should be accepted."""
        assert transcription_service.validate_audio_format("test.flac") is True
    
    def test_reject_unsupported_formats(self, transcription_service):
        """Unsupported formats should be rejected."""
        assert transcription_service.validate_audio_format("test.txt") is False
        assert transcription_service.validate_audio_format("test.pdf") is False
        assert transcription_service.validate_audio_format("test.doc") is False
    
    def test_reject_empty_path(self, transcription_service):
        """Empty path should be rejected."""
        assert transcription_service.validate_audio_format("") is False
        assert transcription_service.validate_audio_format(None) is False
    
    def test_reject_no_extension(self, transcription_service):
        """Files without extension should be rejected."""
        assert transcription_service.validate_audio_format("testfile") is False
    
    def test_get_supported_formats(self, transcription_service):
        """Should return set of supported formats."""
        formats = transcription_service.get_supported_formats()
        assert 'mp3' in formats
        assert 'wav' in formats
        assert 'webm' in formats
        assert isinstance(formats, set)


class TestFileSizeValidation:
    """Tests for file size validation."""
    
    def test_validate_normal_file_size(self, transcription_service):
        """Normal file sizes should be accepted."""
        assert transcription_service.validate_file_size(1024) is True
        assert transcription_service.validate_file_size(1024 * 1024) is True
    
    def test_validate_maximum_file_size(self, transcription_service):
        """Maximum allowed file size should be accepted."""
        max_size = transcription_service.MAX_FILE_SIZE
        assert transcription_service.validate_file_size(max_size) is True
    
    def test_reject_oversized_files(self, transcription_service):
        """Files exceeding max size should be rejected."""
        max_size = transcription_service.MAX_FILE_SIZE
        assert transcription_service.validate_file_size(max_size + 1) is False
    
    def test_reject_zero_size(self, transcription_service):
        """Zero-size files should be rejected."""
        assert transcription_service.validate_file_size(0) is False
    
    def test_reject_negative_size(self, transcription_service):
        """Negative sizes should be rejected."""
        assert transcription_service.validate_file_size(-1) is False
        assert transcription_service.validate_file_size(-1000) is False
    
    def test_validate_small_file_size(self, transcription_service):
        """Small but valid file sizes should be accepted."""
        assert transcription_service.validate_file_size(1) is True
        assert transcription_service.validate_file_size(100) is True


class TestTranscribeFile:
    """Tests for file transcription."""
    
    def test_transcribe_file_requires_api_key(self):
        """Transcription should fail without API key."""
        env = os.environ.copy()
        env.pop('ASSEMBLYAI_API_KEY', None)
        with patch.dict(os.environ, env, clear=True):
            with patch.dict(os.environ, {'MAX_UPLOAD_SIZE_MB': '100'}):
                service = TranscriptionService()
                with pytest.raises(ExternalAPIError) as exc_info:
                    service.transcribe_file(b"audio data", "mp3")
                assert "ASSEMBLYAI_API_KEY" in str(exc_info.value)
    
    def test_transcribe_file_with_unsupported_format(self, transcription_service):
        """Transcription should fail with unsupported format."""
        with pytest.raises(ValueError) as exc_info:
            transcription_service.transcribe_file(b"audio data", "txt")
        assert "Unsupported format" in str(exc_info.value)
    
    def test_transcribe_file_exceeding_size_limit(self, transcription_service):
        """Transcription should fail when file exceeds size limit."""
        large_data = b"x" * (transcription_service.MAX_FILE_SIZE + 1)
        with pytest.raises(ValueError) as exc_info:
            transcription_service.transcribe_file(large_data, "mp3")
        assert "too large" in str(exc_info.value)
    
    @patch('services.transcription_service.requests.post')
    @patch('services.transcription_service.requests.get')
    def test_transcribe_file_success(self, mock_get, mock_post, transcription_service):
        """Successful transcription should return text."""
        # Mock upload response
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"upload_url": "https://cdn.assemblyai.com/upload/123"}
        
        # Mock transcript request response
        mock_transcript_response = MagicMock()
        mock_transcript_response.status_code = 200
        mock_transcript_response.json.return_value = {"id": "transcript_123"}
        
        mock_post.side_effect = [mock_upload_response, mock_transcript_response]
        
        # Mock polling response
        mock_poll_response = MagicMock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {"status": "completed", "text": "Hello world"}
        mock_get.return_value = mock_poll_response
        
        result = transcription_service.transcribe_file(b"audio data", "mp3")
        assert result == "Hello world"
    
    @patch('services.transcription_service.requests.post')
    def test_transcribe_file_upload_failure(self, mock_post, transcription_service):
        """Should handle upload failure gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response
        
        with pytest.raises(ExternalAPIError) as exc_info:
            transcription_service.transcribe_file(b"audio data", "mp3")
        assert "Upload failed" in str(exc_info.value)


class TestTranscribeStream:
    """Tests for streaming transcription."""
    
    @patch('services.transcription_service.requests.post')
    @patch('services.transcription_service.requests.get')
    def test_transcribe_stream_yields_results(self, mock_get, mock_post, transcription_service):
        """Stream transcription should yield results."""
        # Mock upload response
        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"upload_url": "https://cdn.assemblyai.com/upload/123"}
        
        # Mock transcript request response
        mock_transcript_response = MagicMock()
        mock_transcript_response.status_code = 200
        mock_transcript_response.json.return_value = {"id": "transcript_123"}
        
        mock_post.side_effect = [mock_upload_response, mock_transcript_response]
        
        # Mock polling response
        mock_poll_response = MagicMock()
        mock_poll_response.status_code = 200
        mock_poll_response.json.return_value = {"status": "completed", "text": "Streamed text"}
        mock_get.return_value = mock_poll_response
        
        def audio_generator():
            yield b"chunk1"
            yield b"chunk2"
        
        results = list(transcription_service.transcribe_stream(audio_generator()))
        assert len(results) == 1
        assert results[0] == "Streamed text"
    
    def test_transcribe_stream_empty_input(self, transcription_service):
        """Empty stream should yield no results."""
        def empty_generator():
            return
            yield  # Make it a generator
        
        results = list(transcription_service.transcribe_stream(empty_generator()))
        assert len(results) == 0


class TestEnvironmentConfiguration:
    """Tests for environment-based configuration."""
    
    def test_max_file_size_from_environment(self):
        """MAX_FILE_SIZE should be configurable via environment."""
        with patch.dict(os.environ, {
            'ASSEMBLYAI_API_KEY': 'test_key',
            'MAX_UPLOAD_SIZE_MB': '50'
        }):
            service = TranscriptionService()
            assert service.MAX_FILE_SIZE == 50 * 1024 * 1024
    
    def test_default_max_file_size(self):
        """Default MAX_FILE_SIZE should be 100MB."""
        env = os.environ.copy()
        env.pop('MAX_UPLOAD_SIZE_MB', None)
        with patch.dict(os.environ, env, clear=True):
            with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key'}):
                service = TranscriptionService()
                assert service.MAX_FILE_SIZE == 100 * 1024 * 1024


class TestAssemblyAIRealtime:
    """Tests for real-time transcription class."""
    
    def test_realtime_websocket_url(self):
        """Should generate correct WebSocket URL."""
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key'}):
            realtime = AssemblyAIRealtime()
            url = realtime.get_websocket_url(16000)
            assert "wss://api.assemblyai.com/v2/realtime/ws" in url
            assert "sample_rate=16000" in url
    
    def test_realtime_auth_header(self):
        """Should return correct auth header."""
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key_abc'}):
            realtime = AssemblyAIRealtime()
            header = realtime.get_auth_header()
            assert header['authorization'] == 'test_key_abc'
