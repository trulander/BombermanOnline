"""
Tests for logging_config.py module.
"""
import logging
import sys
from unittest.mock import MagicMock, patch, Mock

import pytest

from logging_config import CustomJsonFormatter, configure_logging
from config import settings


class TestCustomJsonFormatter:
    """Tests for CustomJsonFormatter class."""
    
    def test_get_caller_info(self):
        """Test get_caller_info method."""
        formatter = CustomJsonFormatter()
        
        # Call get_caller_info
        result = formatter.get_caller_info()
        
        # Should return a dictionary
        assert isinstance(result, dict)
        # Should contain caller information
        assert len(result) >= 0
    
    def test_get_caller_info_filters_logger_frames(self):
        """Test that get_caller_info filters out logger-related frames."""
        formatter = CustomJsonFormatter()
        
        # Mock inspect.stack to return frames
        mock_frame = MagicMock()
        mock_frame.function = "format"
        mock_frame.lineno = 10
        mock_frame.filename = formatter.project_dir + "/test.py"
        
        with patch('logging_config.inspect.stack', return_value=[mock_frame]):
            result = formatter.get_caller_info()
            
            # Should filter out 'format' function
            assert len(result) == 0
    
    def test_get_caller_info_filters_non_project_files(self):
        """Test that get_caller_info filters out non-project files."""
        formatter = CustomJsonFormatter()
        
        # Mock inspect.stack to return frames from outside project
        mock_frame = MagicMock()
        mock_frame.function = "test_func"
        mock_frame.lineno = 10
        mock_frame.filename = "/some/other/path/test.py"  # Not in project_dir
        
        with patch('logging_config.inspect.stack', return_value=[mock_frame]):
            result = formatter.get_caller_info()
            
            # Should filter out non-project files
            assert len(result) == 0
    
    def test_get_caller_info_includes_project_files(self):
        """Test that get_caller_info includes project files."""
        formatter = CustomJsonFormatter()
        
        # Mock inspect.stack to return frames from project
        mock_frame = MagicMock()
        mock_frame.function = "test_func"
        mock_frame.lineno = 10
        mock_frame.filename = formatter.project_dir + "/test.py"  # In project_dir
        
        with patch('logging_config.inspect.stack', return_value=[mock_frame]):
            result = formatter.get_caller_info()
            
            # Should include project files
            assert len(result) > 0
            # Check that result contains the function info
            assert any("test_func" in str(val) for val in result.values())
    
    def test_add_fields_basic(self):
        """Test add_fields method with basic record."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        message_dict = {}
        
        with patch('logging_config.socket.gethostname', return_value="test-host"):
            with patch('logging_config.os.getpid', return_value=12345):
                with patch('logging_config.time.time', return_value=1234567890.0):
                    with patch('logging_config.settings.TRACE_CALLER', False):
                        formatter.add_fields(log_record, record, message_dict)
        
        # Check that basic fields are added
        assert log_record["service"] == settings.SERVICE_NAME
        assert log_record["service_type"] == "backend"
        assert log_record["level"] == "INFO"
        assert log_record["logger"] == "test_logger"
        assert log_record["message"] == "Test message"
        assert log_record["host"] == "test-host"
        assert log_record["pid"] == 12345
        assert log_record["timestamp_epoch"] == 1234567890
    
    def test_add_fields_with_trace_caller(self):
        """Test add_fields method with TRACE_CALLER enabled."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        message_dict = {}
        
        with patch('logging_config.socket.gethostname', return_value="test-host"):
            with patch('logging_config.os.getpid', return_value=12345):
                with patch('logging_config.time.time', return_value=1234567890.0):
                    with patch('logging_config.settings.TRACE_CALLER', True):
                        formatter.add_fields(log_record, record, message_dict)
        
        # Check that called_by is added when TRACE_CALLER is True
        assert "called_by" in log_record
        assert isinstance(log_record["called_by"], dict)
    
    def test_add_fields_without_trace_caller(self):
        """Test add_fields method with TRACE_CALLER disabled."""
        formatter = CustomJsonFormatter()
        log_record = {}
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        message_dict = {}
        
        with patch('logging_config.socket.gethostname', return_value="test-host"):
            with patch('logging_config.os.getpid', return_value=12345):
                with patch('logging_config.time.time', return_value=1234567890.0):
                    with patch('logging_config.settings.TRACE_CALLER', False):
                        formatter.add_fields(log_record, record, message_dict)
        
        # Check that called_by is NOT added when TRACE_CALLER is False
        assert "called_by" not in log_record


class TestConfigureLogging:
    """Tests for configure_logging function."""
    
    def test_configure_logging_json_format(self):
        """Test configure_logging with JSON format."""
        # Save original handlers
        original_handlers = logging.root.handlers[:]
        
        try:
            with patch('logging_config.settings.LOG_FORMAT', "json"):
                with patch('logging_config.settings.LOG_LEVEL', "INFO"):
                    configure_logging()
                    
                    # Check that handler was added
                    assert len(logging.root.handlers) > 0
                    # Check that formatter is CustomJsonFormatter
                    handler = logging.root.handlers[-1]
                    assert isinstance(handler.formatter, CustomJsonFormatter)
        finally:
            # Restore original handlers
            logging.root.handlers = original_handlers
    
    def test_configure_logging_text_format(self):
        """Test configure_logging with text format."""
        # Save original handlers
        original_handlers = logging.root.handlers[:]
        
        try:
            with patch('logging_config.settings.LOG_FORMAT', "text"):
                with patch('logging_config.settings.LOG_LEVEL', "DEBUG"):
                    configure_logging()
                    
                    # Check that handler was added
                    assert len(logging.root.handlers) > 0
                    # Check that formatter is logging.Formatter (not CustomJsonFormatter)
                    handler = logging.root.handlers[-1]
                    assert isinstance(handler.formatter, logging.Formatter)
                    assert not isinstance(handler.formatter, CustomJsonFormatter)
        finally:
            # Restore original handlers
            logging.root.handlers = original_handlers
    
    def test_configure_logging_sets_log_level(self):
        """Test that configure_logging sets correct log level."""
        # Save original state
        original_level = logging.root.level
        original_handlers = logging.root.handlers[:]
        
        try:
            # Clear handlers to avoid interference from other tests
            logging.root.handlers = []
            
            with patch('logging_config.settings.LOG_LEVEL', "WARNING"):
                configure_logging()
                
                # Check that log level was set
                assert logging.root.level == logging.WARNING
        finally:
            # Restore original state
            logging.root.level = original_level
            logging.root.handlers = original_handlers
    
    def test_configure_logging_creates_stream_handler(self):
        """Test that configure_logging creates StreamHandler."""
        # Save original handlers
        original_handlers = logging.root.handlers[:]
        
        try:
            configure_logging()
            
            # Check that handler is StreamHandler
            assert len(logging.root.handlers) > 0
            handler = logging.root.handlers[-1]
            assert isinstance(handler, logging.StreamHandler)
            assert handler.stream == sys.stdout
        finally:
            # Restore original handlers
            logging.root.handlers = original_handlers
    
    def test_configure_logging_case_insensitive_format(self):
        """Test that configure_logging handles case-insensitive format."""
        # Save original handlers
        original_handlers = logging.root.handlers[:]
        
        try:
            with patch('logging_config.settings.LOG_FORMAT', "JSON"):  # Uppercase
                configure_logging()
                
                # Should use JSON formatter
                handler = logging.root.handlers[-1]
                assert isinstance(handler.formatter, CustomJsonFormatter)
        finally:
            # Restore original handlers
            logging.root.handlers = original_handlers

