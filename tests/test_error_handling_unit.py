"""Unit tests for error handling and logging utilities.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import time
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.error_handling import (
    ErrorCode,
    ErrorDetails,
    VisionError,
    ExternalAPIError,
    ValidationError,
    ProcessingError,
    NetworkError,
    log_error,
    log_info,
    log_warning,
    retry_with_backoff,
    GracefulDegradation,
    format_error_response,
    create_error_response,
    logger
)


class TestErrorCode:
    """Tests for ErrorCode enumeration."""
    
    def test_error_codes_are_strings(self):
        """Verify all error codes are string values."""
        assert isinstance(ErrorCode.SPEECH_TO_TEXT_ERROR.value, str)
        assert isinstance(ErrorCode.GEMINI_AI_ERROR.value, str)
        assert isinstance(ErrorCode.VALIDATION_ERROR.value, str)
    
    def test_error_codes_unique(self):
        """Verify all error codes have unique values."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))


class TestErrorDetails:
    """Tests for ErrorDetails dataclass."""
    
    def test_error_details_creation(self):
        """Test creating ErrorDetails with all fields."""
        details = ErrorDetails(
            code="TEST_ERROR",
            message="Test error message",
            details={"key": "value"},
            retry_possible=True
        )
        
        assert details.code == "TEST_ERROR"
        assert details.message == "Test error message"
        assert details.details == {"key": "value"}
        assert details.retry_possible is True
        assert details.timestamp is not None
    
    def test_error_details_to_dict(self):
        """Test converting ErrorDetails to dictionary."""
        details = ErrorDetails(
            code="TEST_ERROR",
            message="Test message",
            retry_possible=False
        )
        
        result = details.to_dict()
        
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Test message"
        assert result["retry_possible"] is False
        assert "details" not in result  # Should not include None details


class TestVisionError:
    """Tests for VisionError exception class."""
    
    def test_vision_error_creation(self):
        """Test creating VisionError with all parameters."""
        with patch.object(logger, 'log'):  # Suppress logging during test
            error = VisionError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Test error",
                details={"context": "test"},
                retry_possible=True
            )
        
        assert error.code == ErrorCode.INTERNAL_ERROR
        assert error.message == "Test error"
        assert error.details == {"context": "test"}
        assert error.retry_possible is True
        assert error.timestamp is not None
    
    def test_vision_error_to_response(self):
        """Test converting VisionError to API response format."""
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid input"
            )
        
        response = error.to_response()
        
        assert "error" in response
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Invalid input"


class TestExternalAPIError:
    """Tests for ExternalAPIError exception class."""
    
    def test_speech_to_text_error(self):
        """Test creating error for Speech-to-Text service."""
        with patch.object(logger, 'log'):
            error = ExternalAPIError(
                service="Google Speech-to-Text",
                message="API timeout"
            )
        
        assert error.code == ErrorCode.SPEECH_TO_TEXT_ERROR
        assert "Google Speech-to-Text" in error.message
        assert error.retry_possible is True
    
    def test_gemini_ai_error(self):
        """Test creating error for Gemini AI service."""
        with patch.object(logger, 'log'):
            error = ExternalAPIError(
                service="Gemini AI",
                message="Rate limit exceeded"
            )
        
        assert error.code == ErrorCode.GEMINI_AI_ERROR
        assert "Gemini AI" in error.message


class TestValidationError:
    """Tests for ValidationError exception class."""
    
    def test_validation_error_with_field(self):
        """Test creating validation error with field name."""
        with patch.object(logger, 'log'):
            error = ValidationError(
                message="Invalid format",
                field="audio_file"
            )
        
        assert error.code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "audio_file"
        assert error.retry_possible is False


class TestProcessingError:
    """Tests for ProcessingError exception class."""
    
    def test_audio_processing_error(self):
        """Test creating audio processing error."""
        with patch.object(logger, 'log'):
            error = ProcessingError(
                operation="audio",
                message="Segmentation failed"
            )
        
        assert error.code == ErrorCode.AUDIO_PROCESSING_ERROR
        assert "audio" in error.message.lower()
    
    def test_pdf_processing_error(self):
        """Test creating PDF processing error."""
        with patch.object(logger, 'log'):
            error = ProcessingError(
                operation="pdf",
                message="Generation failed"
            )
        
        assert error.code == ErrorCode.PDF_GENERATION_ERROR


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""
    
    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test that failures trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_then_success()
        
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        
        assert call_count == 3  # Initial + 2 retries


class TestGracefulDegradation:
    """Tests for GracefulDegradation context manager."""
    
    def test_successful_operation(self):
        """Test graceful degradation with successful operation."""
        with GracefulDegradation(
            service_name="Test Service",
            fallback_value="fallback"
        ) as degradation:
            result = "success"
        
        final_result = degradation.get_result(result)
        
        assert final_result["value"] == "success"
        assert final_result["degraded"] is False
    
    def test_failed_operation_uses_fallback(self):
        """Test graceful degradation uses fallback on failure."""
        with GracefulDegradation(
            service_name="Test Service",
            fallback_value="fallback"
        ) as degradation:
            raise ValueError("Service failed")
        
        final_result = degradation.get_result("should_not_use")
        
        assert final_result["value"] == "fallback"
        assert final_result["degraded"] is True
    
    def test_user_notification_included(self):
        """Test that user notification is included when enabled."""
        with GracefulDegradation(
            service_name="Test Service",
            fallback_value="fallback",
            notify_user=True
        ) as degradation:
            raise ValueError("Service failed")
        
        final_result = degradation.get_result("unused")
        
        assert "message" in final_result
        assert "Test Service" in final_result["message"]


class TestFormatErrorResponse:
    """Tests for format_error_response function."""
    
    def test_format_vision_error(self):
        """Test formatting VisionError to response."""
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Test error"
            )
        
        response = format_error_response(error)
        
        assert "error" in response
        assert response["error"]["code"] == "VALIDATION_ERROR"
    
    def test_format_standard_exception(self):
        """Test formatting standard exception to response."""
        error = ValueError("Standard error")
        
        response = format_error_response(error, include_details=True)
        
        assert "error" in response
        assert response["error"]["code"] == "INTERNAL_ERROR"


class TestCreateErrorResponse:
    """Tests for create_error_response function."""
    
    def test_create_error_response(self):
        """Test creating error response with all parameters."""
        response = create_error_response(
            code=ErrorCode.NOT_FOUND,
            message="Resource not found",
            details={"resource_id": "123"},
            retry_possible=False
        )
        
        assert response["error"]["code"] == "NOT_FOUND"
        assert response["error"]["message"] == "Resource not found"
        assert response["error"]["retry_possible"] is False


class TestLogging:
    """Tests for logging functions."""
    
    def test_log_error_with_vision_error(self):
        """Test logging VisionError."""
        with patch.object(logger, 'log') as mock_log:
            error = VisionError(
                code=ErrorCode.INTERNAL_ERROR,
                message="Test error"
            )
        
        # VisionError logs automatically on creation
        mock_log.assert_called()
    
    def test_log_info(self):
        """Test logging info message."""
        with patch.object(logger, 'info') as mock_info:
            log_info("Test message", context={"key": "value"})
        
        mock_info.assert_called_once()
    
    def test_log_warning(self):
        """Test logging warning message."""
        with patch.object(logger, 'warning') as mock_warning:
            log_warning("Test warning", context={"key": "value"})
        
        mock_warning.assert_called_once()


class TestAPIFailureErrorMessages:
    """Tests for API failure error messages.
    
    Requirements: 7.1, 7.2
    """
    
    def test_speech_to_text_api_failure_message(self):
        """Test error message when Google Speech-to-Text API fails.
        
        Requirements: 7.1
        """
        with patch.object(logger, 'log'):
            error = ExternalAPIError(
                service="Google Speech-to-Text",
                message="API timeout",
                details={"timeout_seconds": 30}
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "SPEECH_TO_TEXT_ERROR"
        assert "Google Speech-to-Text" in response["error"]["message"]
        assert "API timeout" in response["error"]["message"]
        assert response["error"]["retry_possible"] is True
    
    def test_speech_to_text_timeout_error(self):
        """Test error message for Speech-to-Text timeout.
        
        Requirements: 7.1
        """
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.SPEECH_TO_TEXT_TIMEOUT,
                message="Request timed out after 60 seconds",
                retry_possible=True
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "SPEECH_TO_TEXT_TIMEOUT"
        assert "timed out" in response["error"]["message"]
        assert response["error"]["retry_possible"] is True
    
    def test_gemini_ai_unavailable_message(self):
        """Test error message when Gemini AI service is unavailable.
        
        Requirements: 7.2
        """
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.GEMINI_AI_UNAVAILABLE,
                message="Gemini AI service is temporarily unavailable",
                details={"status_code": 503},
                retry_possible=True
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "GEMINI_AI_UNAVAILABLE"
        assert "unavailable" in response["error"]["message"].lower()
        assert response["error"]["retry_possible"] is True
    
    def test_gemini_ai_rate_limit_error(self):
        """Test error message for Gemini AI rate limit exceeded.
        
        Requirements: 7.2
        """
        with patch.object(logger, 'log'):
            error = ExternalAPIError(
                service="Gemini AI",
                message="Rate limit exceeded",
                details={"retry_after": 60}
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "GEMINI_AI_ERROR"
        assert "Gemini AI" in response["error"]["message"]
        assert response["error"]["retry_possible"] is True
    
    def test_error_response_includes_retry_suggestion(self):
        """Test that API failure errors suggest retry options.
        
        Requirements: 7.1
        """
        with patch.object(logger, 'log'):
            error = ExternalAPIError(
                service="Google Speech-to-Text",
                message="Service temporarily unavailable"
            )
        
        response = error.to_response()
        
        # Verify retry_possible flag is set for external API errors
        assert response["error"]["retry_possible"] is True


class TestGracefulDegradationScenarios:
    """Tests for graceful degradation scenarios.
    
    Requirements: 7.2
    """
    
    def test_gemini_ai_failure_provides_raw_transcript(self):
        """Test that raw transcript is provided when Gemini AI fails.
        
        Requirements: 7.2
        """
        raw_transcript = "This is the raw transcript from the lecture."
        
        with GracefulDegradation(
            service_name="Gemini AI",
            fallback_value=raw_transcript,
            notify_user=True
        ) as degradation:
            # Simulate Gemini AI failure
            raise ConnectionError("Gemini AI service unavailable")
        
        result = degradation.get_result("processed_notes")
        
        assert result["degraded"] is True
        assert result["value"] == raw_transcript
        assert "message" in result
        assert "Gemini AI" in result["message"]
        assert "unavailable" in result["message"].lower()
    
    def test_graceful_degradation_preserves_partial_results(self):
        """Test that partial results are preserved during degradation.
        
        Requirements: 7.2
        """
        partial_result = {
            "transcript": "Lecture content...",
            "topics": None,  # Failed to extract
            "summary": None  # Failed to generate
        }
        
        with GracefulDegradation(
            service_name="AI Analysis",
            fallback_value=partial_result,
            notify_user=True
        ) as degradation:
            raise TimeoutError("AI analysis timed out")
        
        result = degradation.get_result("full_analysis")
        
        assert result["degraded"] is True
        assert result["value"]["transcript"] == "Lecture content..."
        assert result["value"]["topics"] is None
    
    def test_graceful_degradation_without_user_notification(self):
        """Test graceful degradation without user notification.
        
        Requirements: 7.2
        """
        with GracefulDegradation(
            service_name="Background Service",
            fallback_value="default",
            notify_user=False
        ) as degradation:
            raise RuntimeError("Background service failed")
        
        result = degradation.get_result("success_value")
        
        assert result["degraded"] is True
        assert "message" not in result
    
    def test_multiple_service_degradation(self):
        """Test handling multiple service failures with degradation.
        
        Requirements: 7.2
        """
        # First service fails
        with GracefulDegradation(
            service_name="Service A",
            fallback_value="fallback_a"
        ) as deg_a:
            raise ValueError("Service A failed")
        
        result_a = deg_a.get_result("success_a")
        
        # Second service succeeds
        with GracefulDegradation(
            service_name="Service B",
            fallback_value="fallback_b"
        ) as deg_b:
            pass  # No exception
        
        result_b = deg_b.get_result("success_b")
        
        assert result_a["degraded"] is True
        assert result_a["value"] == "fallback_a"
        assert result_b["degraded"] is False
        assert result_b["value"] == "success_b"


class TestNetworkErrorBuffering:
    """Tests for network error buffering during live captioning.
    
    Requirements: 7.3
    """
    
    def test_network_error_creation(self):
        """Test creating network error with buffering context.
        
        Requirements: 7.3
        """
        with patch.object(logger, 'log'):
            error = NetworkError(
                message="Connection lost during live captioning",
                details={
                    "buffered_segments": 5,
                    "last_successful_timestamp": "2024-01-15T10:30:00Z"
                }
            )
        
        assert error.code == ErrorCode.NETWORK_ERROR
        assert error.retry_possible is True
        assert error.details["buffered_segments"] == 5
    
    def test_network_error_response_format(self):
        """Test network error response includes retry information.
        
        Requirements: 7.3
        """
        with patch.object(logger, 'log'):
            error = NetworkError(
                message="Network connectivity lost",
                details={"reconnect_attempts": 3}
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "NETWORK_ERROR"
        assert response["error"]["retry_possible"] is True
    
    def test_connection_lost_error(self):
        """Test connection lost error during streaming.
        
        Requirements: 7.3
        """
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.CONNECTION_LOST,
                message="WebSocket connection lost",
                details={
                    "session_id": "abc123",
                    "buffered_audio_seconds": 15
                },
                retry_possible=True
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "CONNECTION_LOST"
        assert response["error"]["retry_possible"] is True
    
    def test_network_error_with_original_exception(self):
        """Test network error preserves original exception.
        
        Requirements: 7.3
        """
        original = ConnectionResetError("Connection reset by peer")
        
        with patch.object(logger, 'log'):
            error = NetworkError(
                message="Network connection failed",
                original_exception=original
            )
        
        assert error.original_exception is original
        assert "Connection reset" in str(error.original_exception)


class TestPDFGenerationFailureFallback:
    """Tests for PDF generation failure fallback.
    
    Requirements: 7.4
    """
    
    def test_pdf_generation_error_creation(self):
        """Test creating PDF generation error.
        
        Requirements: 7.4
        """
        with patch.object(logger, 'log'):
            error = ProcessingError(
                operation="pdf",
                message="Failed to render PDF document",
                details={"lecture_id": "123", "error_type": "rendering"}
            )
        
        assert error.code == ErrorCode.PDF_GENERATION_ERROR
        assert error.retry_possible is True
        assert "pdf" in error.message.lower()
    
    def test_pdf_error_response_format(self):
        """Test PDF error response format for fallback handling.
        
        Requirements: 7.4
        """
        with patch.object(logger, 'log'):
            error = ProcessingError(
                operation="pdf",
                message="PDF generation failed due to memory limit"
            )
        
        response = error.to_response()
        
        assert response["error"]["code"] == "PDF_GENERATION_ERROR"
        assert response["error"]["retry_possible"] is True
    
    def test_pdf_fallback_allows_web_view(self):
        """Test that PDF failure allows viewing notes in web interface.
        
        Requirements: 7.4
        """
        # Simulate PDF generation failure with graceful degradation
        notes_data = {
            "topics": [{"title": "Topic 1", "content": "Content..."}],
            "summary": "Lecture summary",
            "key_points": ["Point 1", "Point 2"]
        }
        
        with GracefulDegradation(
            service_name="PDF Generation",
            fallback_value=notes_data,
            notify_user=True
        ) as degradation:
            raise MemoryError("Insufficient memory for PDF generation")
        
        result = degradation.get_result("pdf_bytes")
        
        assert result["degraded"] is True
        assert result["value"] == notes_data
        assert "message" in result
        assert "PDF Generation" in result["message"]
    
    def test_pdf_error_with_original_exception(self):
        """Test PDF error preserves original exception for debugging.
        
        Requirements: 7.4
        """
        original = IOError("Disk write failed")
        
        with patch.object(logger, 'log'):
            error = ProcessingError(
                operation="pdf",
                message="Failed to save PDF",
                original_exception=original
            )
        
        assert error.original_exception is original
        assert error.code == ErrorCode.PDF_GENERATION_ERROR
    
    def test_pdf_retry_after_failure(self):
        """Test that PDF generation can be retried after failure.
        
        Requirements: 7.4
        """
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def generate_pdf_with_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MemoryError("Temporary memory issue")
            return b"PDF content"
        
        result = generate_pdf_with_retry()
        
        assert result == b"PDF content"
        assert call_count == 2


class TestErrorResponseConsistency:
    """Tests for consistent error response formatting.
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    
    def test_all_error_types_have_consistent_structure(self):
        """Test that all error types produce consistent response structure."""
        with patch.object(logger, 'log'):
            errors = [
                ExternalAPIError("Speech-to-Text", "API failed"),
                ValidationError("Invalid input", field="audio_file"),
                ProcessingError("audio", "Processing failed"),
                NetworkError("Connection lost"),
                VisionError(ErrorCode.INTERNAL_ERROR, "Internal error")
            ]
        
        for error in errors:
            response = error.to_response()
            
            # Verify consistent structure
            assert "error" in response
            assert "code" in response["error"]
            assert "message" in response["error"]
            assert "retry_possible" in response["error"]
    
    def test_error_response_json_serializable(self):
        """Test that error responses are JSON serializable."""
        import json
        
        with patch.object(logger, 'log'):
            error = VisionError(
                code=ErrorCode.VALIDATION_ERROR,
                message="Test error",
                details={"field": "test", "value": 123}
            )
        
        response = error.to_response()
        
        # Should not raise
        json_str = json.dumps(response)
        assert json_str is not None
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["error"]["code"] == "VALIDATION_ERROR"
