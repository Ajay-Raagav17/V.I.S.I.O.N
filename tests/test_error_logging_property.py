"""
Property-based tests for error logging universality.

**Feature: vision-accessibility, Property 8: Error logging universality**
**Validates: Requirements 7.5**
"""

import pytest
import json
import logging
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.error_handling import (
    ErrorCode,
    VisionError,
    ExternalAPIError,
    ValidationError,
    ProcessingError,
    NetworkError,
    log_error,
    logger
)


# Strategy for generating error messages
error_message_strategy = st.text(
    min_size=1,
    max_size=100,
    alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_')
).filter(lambda x: x.strip())

# Strategy for generating context keys (valid Python identifiers)
context_key_strategy = st.sampled_from(['key', 'field', 'value', 'data', 'info', 'status', 'code', 'name'])

# Strategy for generating context values
context_value_strategy = st.one_of(
    st.text(min_size=1, max_size=20, alphabet=st.sampled_from('abcdefghijklmnopqrstuvwxyz')),
    st.integers(min_value=-1000, max_value=1000),
    st.booleans()
)

# Strategy for generating context dictionaries
context_strategy = st.dictionaries(
    keys=context_key_strategy,
    values=context_value_strategy,
    min_size=0,
    max_size=3
)

# Strategy for generating error codes
error_code_strategy = st.sampled_from(list(ErrorCode))

# Strategy for generating service names for ExternalAPIError
service_name_strategy = st.sampled_from([
    "Google Speech-to-Text",
    "Gemini AI",
    "External Service",
    "API Gateway"
])

# Strategy for generating operation names for ProcessingError
operation_strategy = st.sampled_from([
    "audio",
    "pdf",
    "transcription",
    "processing"
])

# Strategy for generating field names for ValidationError
field_name_strategy = st.one_of(
    st.none(),
    st.sampled_from(['audio_file', 'email', 'password', 'title', 'content', 'format', 'size'])
)


class TestErrorLoggingUniversality:
    """
    Property 8: Error logging universality
    
    For any error condition that occurs during system operation (API failures, 
    validation errors, processing failures), the system should create a log entry 
    containing error type, timestamp, and relevant context details.
    
    **Feature: vision-accessibility, Property 8: Error logging universality**
    **Validates: Requirements 7.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        code=error_code_strategy,
        message=error_message_strategy,
        context=context_strategy
    )
    def test_vision_error_logs_with_required_fields(self, code, message, context):
        """
        Property: For any VisionError, the system should create a log entry 
        containing error type, timestamp, and relevant context details.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        with patch.object(logger, 'log', side_effect=capture_log):
            error = VisionError(
                code=code,
                message=message,
                details=context if context else None,
                retry_possible=True
            )
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"VisionError should create a log entry for code={code}, message={message}"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "VisionError", \
            f"Error type should be VisionError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(log_data["timestamp"])
        except ValueError:
            pytest.fail(f"Timestamp should be valid ISO format, got {log_data['timestamp']}")
        
        # Must contain message
        assert "message" in log_data, \
            "Log entry must contain message"
        
        # Must contain error code
        assert "code" in log_data, \
            "Log entry must contain error code"
        assert log_data["code"] == code.value, \
            f"Error code should be {code.value}, got {log_data['code']}"
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        service=service_name_strategy,
        message=error_message_strategy
    )
    def test_external_api_error_logs_with_required_fields(self, service, message):
        """
        Property: For any ExternalAPIError (API failures), the system should 
        create a log entry containing error type, timestamp, and service context.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        with patch.object(logger, 'log', side_effect=capture_log):
            error = ExternalAPIError(
                service=service,
                message=message
            )
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"ExternalAPIError should create a log entry for service={service}"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "ExternalAPIError", \
            f"Error type should be ExternalAPIError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        
        # Must contain details with service information
        assert "details" in log_data, \
            "Log entry must contain details"
        assert "service" in log_data["details"], \
            "Log entry details must contain service name"
        assert log_data["details"]["service"] == service, \
            f"Service should be {service}, got {log_data['details']['service']}"
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        message=error_message_strategy,
        field=field_name_strategy
    )
    def test_validation_error_logs_with_required_fields(self, message, field):
        """
        Property: For any ValidationError, the system should create a log entry 
        containing error type, timestamp, and field context when provided.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        with patch.object(logger, 'log', side_effect=capture_log):
            error = ValidationError(
                message=message,
                field=field
            )
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"ValidationError should create a log entry for message={message}"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "ValidationError", \
            f"Error type should be ValidationError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        
        # Must contain error code
        assert "code" in log_data, \
            "Log entry must contain error code"
        assert log_data["code"] == ErrorCode.VALIDATION_ERROR.value, \
            f"Error code should be VALIDATION_ERROR"
        
        # If field was provided, it should be in details
        if field:
            assert "details" in log_data, \
                "Log entry must contain details when field is provided"
            assert "field" in log_data["details"], \
                "Log entry details must contain field name"
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        operation=operation_strategy,
        message=error_message_strategy
    )
    def test_processing_error_logs_with_required_fields(self, operation, message):
        """
        Property: For any ProcessingError, the system should create a log entry 
        containing error type, timestamp, and operation context.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        with patch.object(logger, 'log', side_effect=capture_log):
            error = ProcessingError(
                operation=operation,
                message=message
            )
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"ProcessingError should create a log entry for operation={operation}"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "ProcessingError", \
            f"Error type should be ProcessingError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        
        # Must contain details with operation information
        assert "details" in log_data, \
            "Log entry must contain details"
        assert "operation" in log_data["details"], \
            "Log entry details must contain operation name"
        assert log_data["details"]["operation"] == operation, \
            f"Operation should be {operation}, got {log_data['details']['operation']}"
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        message=error_message_strategy,
        context=context_strategy
    )
    def test_network_error_logs_with_required_fields(self, message, context):
        """
        Property: For any NetworkError, the system should create a log entry 
        containing error type, timestamp, and relevant context details.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        with patch.object(logger, 'log', side_effect=capture_log):
            error = NetworkError(
                message=message,
                details=context if context else None
            )
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"NetworkError should create a log entry for message={message}"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "NetworkError", \
            f"Error type should be NetworkError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        
        # Must contain error code
        assert "code" in log_data, \
            "Log entry must contain error code"
        assert log_data["code"] == ErrorCode.NETWORK_ERROR.value, \
            f"Error code should be NETWORK_ERROR"
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(
        message=error_message_strategy,
        context=context_strategy
    )
    def test_log_error_function_logs_standard_exceptions(self, message, context):
        """
        Property: For any standard Python exception, the log_error function 
        should create a log entry containing error type, timestamp, and traceback.
        
        **Feature: vision-accessibility, Property 8: Error logging universality**
        **Validates: Requirements 7.5**
        """
        logged_messages = []
        
        def capture_log(level, msg, *args, **kwargs):
            logged_messages.append((level, msg))
        
        # Create a standard exception
        standard_error = ValueError(message)
        
        with patch.object(logger, 'log', side_effect=capture_log):
            log_error(standard_error, context=context if context else None)
        
        # Property: At least one log entry should be created
        assert len(logged_messages) > 0, \
            f"log_error should create a log entry for standard exception"
        
        # Property: Log entry should contain required fields
        log_level, log_message = logged_messages[0]
        log_data = json.loads(log_message)
        
        # Must contain error_type
        assert "error_type" in log_data, \
            "Log entry must contain error_type"
        assert log_data["error_type"] == "ValueError", \
            f"Error type should be ValueError, got {log_data['error_type']}"
        
        # Must contain timestamp
        assert "timestamp" in log_data, \
            "Log entry must contain timestamp"
        
        # Must contain message
        assert "message" in log_data, \
            "Log entry must contain message"
        
        # Must contain traceback for standard exceptions
        assert "traceback" in log_data, \
            "Log entry must contain traceback for standard exceptions"
        
        # If context was provided, it should be in the log
        if context:
            assert "context" in log_data, \
                "Log entry must contain context when provided"

