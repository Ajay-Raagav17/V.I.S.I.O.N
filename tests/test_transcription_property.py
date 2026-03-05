"""
Property-based tests for AssemblyAI transcription service.

Uses Hypothesis to test properties that should hold across all inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch
import os
import string

from services.transcription_service import TranscriptionService


# Strategies for generating test data
supported_formats = st.sampled_from(['mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'mp4', 'mpeg'])
unsupported_formats = st.text(
    alphabet=string.ascii_lowercase,
    min_size=1,
    max_size=5
).filter(lambda x: x not in {'mp3', 'wav', 'm4a', 'ogg', 'webm', 'flac', 'mp4', 'mpeg'})

file_names = st.text(
    alphabet=string.ascii_letters + string.digits + '_-',
    min_size=1,
    max_size=50
)


@pytest.fixture
def transcription_service():
    """Create a TranscriptionService instance with mocked API key."""
    with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_api_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
        service = TranscriptionService()
        yield service


class TestFormatValidationProperties:
    """Property tests for format validation."""
    
    @given(extension=supported_formats, filename=file_names)
    @settings(max_examples=50)
    def test_supported_formats_always_accepted(self, extension, filename):
        """
        Property: All supported formats should always be accepted.
        
        **Feature: vision-accessibility, Property 1: Format validation consistency**
        **Validates: Requirements 3.1**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            file_path = f"{filename}.{extension}"
            assert service.validate_audio_format(file_path) is True
    
    @given(extension=unsupported_formats, filename=file_names)
    @settings(max_examples=50)
    def test_unsupported_formats_always_rejected(self, extension, filename):
        """
        Property: All unsupported formats should always be rejected.
        
        **Feature: vision-accessibility, Property 2: Format rejection consistency**
        **Validates: Requirements 3.1**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            file_path = f"{filename}.{extension}"
            assert service.validate_audio_format(file_path) is False
    
    @given(extension=supported_formats)
    @settings(max_examples=20)
    def test_case_insensitive_format_validation(self, extension):
        """
        Property: Format validation should be case-insensitive.
        
        **Feature: vision-accessibility, Property 3: Case insensitivity**
        **Validates: Requirements 3.1**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            # Test lowercase
            assert service.validate_audio_format(f"test.{extension.lower()}") is True
            # Test uppercase
            assert service.validate_audio_format(f"test.{extension.upper()}") is True


class TestFileSizeValidationProperties:
    """Property tests for file size validation."""
    
    @given(file_size=st.integers(min_value=1, max_value=100 * 1024 * 1024))
    @settings(max_examples=100)
    def test_valid_sizes_always_accepted(self, file_size):
        """
        Property: All valid file sizes (1 byte to MAX_FILE_SIZE) should be accepted.
        
        **Feature: vision-accessibility, Property 4: Valid size acceptance**
        **Validates: Requirements 3.2**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            assert service.validate_file_size(file_size) is True
    
    @given(file_size=st.integers(min_value=100 * 1024 * 1024 + 1, max_value=500 * 1024 * 1024))
    @settings(max_examples=50)
    def test_oversized_files_always_rejected(self, file_size):
        """
        Property: All files exceeding MAX_FILE_SIZE should be rejected.
        
        **Feature: vision-accessibility, Property 5: Oversize rejection**
        **Validates: Requirements 3.2**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            assert service.validate_file_size(file_size) is False
    
    @given(file_size=st.integers(max_value=0))
    @settings(max_examples=50)
    def test_zero_and_negative_sizes_rejected(self, file_size):
        """
        Property: Zero and negative file sizes should always be rejected.
        
        **Feature: vision-accessibility, Property 6: Invalid size rejection**
        **Validates: Requirements 3.2**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            assert service.validate_file_size(file_size) is False


class TestSupportedFormatsProperty:
    """Property tests for supported formats set."""
    
    @given(st.data())
    @settings(max_examples=20)
    def test_get_supported_formats_returns_copy(self, data):
        """
        Property: get_supported_formats should return a copy, not the original set.
        
        **Feature: vision-accessibility, Property 7: Immutable formats**
        **Validates: Requirements 3.1**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            formats1 = service.get_supported_formats()
            formats2 = service.get_supported_formats()
            
            # Should be equal but not the same object
            assert formats1 == formats2
            assert formats1 is not formats2
            
            # Modifying one shouldn't affect the other
            formats1.add('fake_format')
            assert 'fake_format' not in formats2
            assert 'fake_format' not in service.SUPPORTED_FORMATS


class TestValidationConsistencyProperties:
    """Property tests for validation consistency."""
    
    @given(
        filename=file_names,
        extension=supported_formats,
        file_size=st.integers(min_value=1, max_value=100 * 1024 * 1024)
    )
    @settings(max_examples=50)
    def test_valid_inputs_are_consistently_valid(self, filename, extension, file_size):
        """
        Property: Valid format + valid size should always pass both validations.
        
        **Feature: vision-accessibility, Property 8: Validation consistency**
        **Validates: Requirements 3.1, 3.2**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            file_path = f"{filename}.{extension}"
            
            # Both validations should pass
            assert service.validate_audio_format(file_path) is True
            assert service.validate_file_size(file_size) is True
    
    @given(
        filename=file_names,
        extension=unsupported_formats,
        file_size=st.integers(min_value=100 * 1024 * 1024 + 1, max_value=500 * 1024 * 1024)
    )
    @settings(max_examples=50)
    def test_invalid_inputs_are_consistently_invalid(self, filename, extension, file_size):
        """
        Property: Invalid format + invalid size should always fail both validations.
        
        **Feature: vision-accessibility, Property 9: Invalid input rejection**
        **Validates: Requirements 3.1, 3.2**
        """
        with patch.dict(os.environ, {'ASSEMBLYAI_API_KEY': 'test_key', 'MAX_UPLOAD_SIZE_MB': '100'}):
            service = TranscriptionService()
            file_path = f"{filename}.{extension}"
            
            # Both validations should fail
            assert service.validate_audio_format(file_path) is False
            assert service.validate_file_size(file_size) is False


class TestConfigurationProperties:
    """Property tests for configuration."""
    
    @given(max_size_mb=st.integers(min_value=1, max_value=1000))
    @settings(max_examples=20)
    def test_max_file_size_scales_correctly(self, max_size_mb):
        """
        Property: MAX_FILE_SIZE should always be MAX_UPLOAD_SIZE_MB * 1024 * 1024.
        
        **Feature: vision-accessibility, Property 10: Configuration scaling**
        **Validates: Requirements 3.2**
        """
        with patch.dict(os.environ, {
            'ASSEMBLYAI_API_KEY': 'test_key',
            'MAX_UPLOAD_SIZE_MB': str(max_size_mb)
        }):
            service = TranscriptionService()
            expected_bytes = max_size_mb * 1024 * 1024
            assert service.MAX_FILE_SIZE == expected_bytes
