"""Unit tests for logging configuration."""

import logging
import logging.handlers
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import structlog

from src.common.logging_config import (
    setup_logging, get_logger, init_logging, add_app_context
)


class TestLoggingConfig:
    """Test logging configuration."""
    
    @pytest.mark.unit
    def test_setup_logging_basic(self, test_config, temp_dir):
        """Test basic logging setup."""
        with patch("src.common.logging_config.get_config", return_value=test_config):
            setup_logging(log_level="INFO", use_json=False)
            
            # Check root logger configuration
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
    
    @pytest.mark.unit
    def test_setup_logging_with_file(self, test_config, temp_dir):
        """Test logging setup with file output."""
        log_file = temp_dir / "test.log"
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            setup_logging(log_file=log_file)
            
            # Check that file handler was added
            root_logger = logging.getLogger()
            file_handlers = [h for h in root_logger.handlers 
                           if isinstance(h, logging.handlers.RotatingFileHandler)]
            assert len(file_handlers) > 0
            assert Path(file_handlers[0].baseFilename) == log_file
    
    @pytest.mark.unit
    def test_setup_logging_json_format(self, test_config):
        """Test logging setup with JSON format."""
        # Ensure JSON format in config
        test_config.yaml_config["logging"]["format"] = "json"
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            with patch("structlog.configure") as mock_configure:
                setup_logging(use_json=True)
                
                # Check that JSON renderer was used
                mock_configure.assert_called_once()
                processors = mock_configure.call_args.kwargs["processors"]
                
                # Look for JSONRenderer in processors
                json_renderer_found = any(
                    hasattr(p, "__name__") and "JSONRenderer" in str(p)
                    for p in processors
                )
                assert json_renderer_found
    
    @pytest.mark.unit
    def test_setup_logging_console_format(self, test_config):
        """Test logging setup with console format."""
        test_config.yaml_config["logging"]["format"] = "console"
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            with patch("structlog.configure") as mock_configure:
                setup_logging(use_json=False)
                
                # Check that ConsoleRenderer was used
                mock_configure.assert_called_once()
                processors = mock_configure.call_args.kwargs["processors"]
                
                # Look for ConsoleRenderer in processors
                console_renderer_found = any(
                    hasattr(p, "__name__") and "ConsoleRenderer" in str(p)
                    for p in processors
                )
                assert console_renderer_found
    
    @pytest.mark.unit
    def test_add_app_context(self, test_config):
        """Test adding application context to log entries."""
        with patch("src.common.logging_config.get_config", return_value=test_config):
            event_dict = {"message": "test"}
            
            result = add_app_context(None, None, event_dict)
            
            assert result["environment"] == "test"
            assert result["app_name"] == "Medtech RAG Test"
            assert result["app_version"] == "0.1.0"
            assert result["message"] == "test"
    
    @pytest.mark.unit
    def test_get_logger(self):
        """Test getting a logger instance."""
        with patch("structlog.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logger = get_logger("test.module")
            
            mock_get_logger.assert_called_once_with("test.module")
            assert logger == mock_logger
    
    @pytest.mark.unit
    def test_init_logging(self, test_config):
        """Test init_logging convenience function."""
        with patch("src.common.logging_config.get_config", return_value=test_config):
            with patch("src.common.logging_config.setup_logging") as mock_setup:
                init_logging()
                
                mock_setup.assert_called_once()
    
    @pytest.mark.unit
    def test_log_level_from_config(self, test_config):
        """Test log level is read from config."""
        test_config.settings.log_level = "WARNING"
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.WARNING
    
    @pytest.mark.unit
    def test_file_logging_from_config(self, test_config, temp_dir):
        """Test file logging configuration from YAML."""
        # Enable file logging in config
        test_config.yaml_config["logging"]["file"]["enabled"] = True
        test_config.yaml_config["logging"]["file"]["path"] = str(temp_dir / "app.log")
        test_config.yaml_config["logging"]["file"]["max_size_mb"] = 5
        test_config.yaml_config["logging"]["file"]["backup_count"] = 3
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            setup_logging()
            
            # Check file handler configuration
            root_logger = logging.getLogger()
            file_handlers = [h for h in root_logger.handlers 
                           if isinstance(h, logging.handlers.RotatingFileHandler)]
            
            assert len(file_handlers) > 0
            handler = file_handlers[0]
            assert handler.maxBytes == 5 * 1024 * 1024  # 5 MB
            assert handler.backupCount == 3
    
    @pytest.mark.unit
    def test_logging_creates_directory(self, test_config, temp_dir):
        """Test that logging creates log directory if it doesn't exist."""
        log_path = temp_dir / "logs" / "subdir" / "app.log"
        test_config.yaml_config["logging"]["file"]["enabled"] = True
        test_config.yaml_config["logging"]["file"]["path"] = str(log_path)
        
        with patch("src.common.logging_config.get_config", return_value=test_config):
            setup_logging()
            
            # Check directory was created
            assert log_path.parent.exists()
            assert log_path.parent.is_dir()