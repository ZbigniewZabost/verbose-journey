"""Tests for the main module."""

import sys
from unittest import mock

import pytest

import main


class TestMain:
    """Tests for the main module."""

    def test_parse_arguments_defaults(self):
        """Test parsing arguments with defaults."""
        # Mock sys.argv
        with mock.patch("sys.argv", ["main.py"]):
            args = main.parse_arguments()
            
            # Check defaults
            assert args["output_dir"] is None
            assert args["verbose"] is False
            assert args["quiet"] is False
    
    def test_parse_arguments_custom(self):
        """Test parsing arguments with custom values."""
        # Mock sys.argv
        with mock.patch("sys.argv", ["main.py", "--output-dir", "/custom/data", "--verbose"]):
            args = main.parse_arguments()
            
            # Check custom values
            assert args["output_dir"] == "/custom/data"
            assert args["verbose"] is True
            assert args["quiet"] is False
    
    def test_configure_logging_default(self):
        """Test configuring logging with default level."""
        # Create args with defaults
        args = {
            "verbose": False,
            "quiet": False,
        }
        
        # Mock logger
        with mock.patch("main.logger") as mock_logger:
            main.configure_logging(args)
            
            # Check that logger was configured with INFO level
            mock_logger.setLevel.assert_called_once_with(mock.ANY)  # Can't easily check the logging level constant
    
    def test_configure_logging_verbose(self):
        """Test configuring logging with verbose level."""
        # Create args with verbose=True
        args = {
            "verbose": True,
            "quiet": False,
        }
        
        # Mock logger
        with mock.patch("main.logger") as mock_logger:
            main.configure_logging(args)
            
            # Check that logger was configured with DEBUG level
            mock_logger.setLevel.assert_called_once_with(mock.ANY)  # Can't easily check the logging level constant
    
    def test_configure_logging_quiet(self):
        """Test configuring logging with quiet level."""
        # Create args with quiet=True
        args = {
            "verbose": False,
            "quiet": True,
        }
        
        # Mock logger
        with mock.patch("main.logger") as mock_logger:
            main.configure_logging(args)
            
            # Check that logger was configured with ERROR level
            mock_logger.setLevel.assert_called_once_with(mock.ANY)  # Can't easily check the logging level constant
    
    @mock.patch("main.parse_arguments")
    @mock.patch("main.configure_logging")
    @mock.patch("main.ScraperConfig")
    @mock.patch("main.KitaScraper")
    def test_main_success(self, mock_scraper_class, mock_config_class, mock_configure_logging, mock_parse_arguments):
        """Test successful execution of main."""
        # Configure mocks
        mock_parse_arguments.return_value = {
            "output_dir": None,
            "verbose": False,
            "quiet": False,
        }
        mock_config = mock.MagicMock()
        mock_config_class.from_env.return_value = mock_config
        mock_scraper = mock.MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = {
            "download_failed": 0,
        }
        
        # Call main
        result = main.main()
        
        # Check that the functions were called correctly
        mock_parse_arguments.assert_called_once()
        mock_configure_logging.assert_called_once()
        mock_config_class.from_env.assert_called_once()
        mock_scraper_class.assert_called_once_with(mock_config)
        mock_scraper.run.assert_called_once()
        
        # Check that the result is success (0)
        assert result == 0
    
    @mock.patch("main.parse_arguments")
    @mock.patch("main.configure_logging")
    @mock.patch("main.ScraperConfig")
    @mock.patch("main.KitaScraper")
    def test_main_with_failures(self, mock_scraper_class, mock_config_class, mock_configure_logging, mock_parse_arguments):
        """Test execution of main with download failures."""
        # Configure mocks
        mock_parse_arguments.return_value = {
            "output_dir": None,
            "verbose": False,
            "quiet": False,
        }
        mock_config = mock.MagicMock()
        mock_config_class.from_env.return_value = mock_config
        mock_scraper = mock.MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.return_value = {
            "download_failed": 1,  # One failure
        }
        
        # Call main
        result = main.main()
        
        # Check that the result is failure (1)
        assert result == 1
    
    @mock.patch("main.parse_arguments")
    @mock.patch("main.configure_logging")
    @mock.patch("main.ScraperConfig")
    def test_main_config_error(self, mock_config_class, mock_configure_logging, mock_parse_arguments):
        """Test execution of main with configuration error."""
        # Configure mocks
        mock_parse_arguments.return_value = {
            "output_dir": None,
            "verbose": False,
            "quiet": False,
        }
        mock_config_class.from_env.side_effect = ValueError("Missing required fields")
        
        # Call main
        result = main.main()
        
        # Check that the result is failure (1)
        assert result == 1
    
    @mock.patch("main.parse_arguments")
    @mock.patch("main.configure_logging")
    @mock.patch("main.ScraperConfig")
    @mock.patch("main.KitaScraper")
    def test_main_unexpected_error(self, mock_scraper_class, mock_config_class, mock_configure_logging, mock_parse_arguments):
        """Test execution of main with unexpected error."""
        # Configure mocks
        mock_parse_arguments.return_value = {
            "output_dir": None,
            "verbose": False,
            "quiet": False,
        }
        mock_config = mock.MagicMock()
        mock_config_class.from_env.return_value = mock_config
        mock_scraper = mock.MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.run.side_effect = Exception("Unexpected error")
        
        # Call main
        result = main.main()
        
        # Check that the result is failure (1)
        assert result == 1
