"""Tests for the utility functions."""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
from PIL import Image

from src.kita_scraper.utils import (
    create_filename,
    download_file,
    add_date_to_exif,
    download_media_files,
)


class TestCreateFilename:
    """Tests for the create_filename function."""

    def test_create_filename_with_extension(self):
        """Test creating a filename with an extension."""
        day = datetime(2023, 1, 1)
        title = "Test Title"
        counter = 1
        url = "https://example.com/image.jpg"

        filename = create_filename(day, title, counter, url)
        
        assert filename == "2023-01-01_Test Title-1.jpg"
        
    def test_create_filename_without_extension(self):
        """Test creating a filename without an extension."""
        day = datetime(2023, 1, 1)
        title = "Test Title"
        counter = 1
        url = "https://example.com/image"

        filename = create_filename(day, title, counter, url)
        
        assert filename == "2023-01-01_Test Title-1"
        
    def test_create_filename_with_special_chars(self):
        """Test creating a filename with special characters."""
        day = datetime(2023, 1, 1)
        title = "Test: Title / With * Special & Chars"
        counter = 1
        url = "https://example.com/image.jpg"

        filename = create_filename(day, title, counter, url)
        
        # The sanitize_filename function should remove or replace special characters
        assert ":" not in filename
        assert "/" not in filename
        assert "*" not in filename
        assert "&" not in filename
        assert filename.endswith(".jpg")


class TestDownloadFile:
    """Tests for the download_file function."""

    @mock.patch("src.kita_scraper.utils.urlopen")
    def test_download_file_success(self, mock_urlopen):
        """Test downloading a file successfully."""
        # Create a mock response
        mock_response = mock.MagicMock()
        mock_response.read.return_value = b"test content"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Test the function
            result = download_file("https://example.com/test.txt", temp_path)
            
            # Check the result
            assert result is True
            assert temp_path.read_bytes() == b"test content"
            
            # Verify the mock was called correctly
            mock_urlopen.assert_called_once_with("https://example.com/test.txt")
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
    
    @mock.patch("src.kita_scraper.utils.urlopen")
    def test_download_file_failure(self, mock_urlopen):
        """Test downloading a file with an error."""
        # Make the mock raise an exception
        mock_urlopen.side_effect = Exception("Download error")
        
        # Create a temporary file path (but don't create the file)
        temp_path = Path(tempfile.gettempdir()) / "test_download_failure.txt"
        
        # Test the function
        result = download_file("https://example.com/test.txt", temp_path)
        
        # Check the result
        assert result is False
        assert not temp_path.exists()


class TestAddDateToExif:
    """Tests for the add_date_to_exif function."""

    def test_add_date_to_exif_non_image(self):
        """Test adding EXIF data to a non-image file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"test content")
        
        try:
            # Test the function
            day = datetime(2023, 1, 1)
            result = add_date_to_exif(temp_path, day)
            
            # Check the result
            assert result is False
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
    
    @pytest.mark.skipif(not os.path.exists("/usr/bin/convert"), 
                       reason="ImageMagick convert not available")
    def test_add_date_to_exif_no_exif(self):
        """Test adding EXIF data to an image without EXIF data."""
        # This test requires ImageMagick to create a test image
        # Skip if not available
        
        # Create a temporary image file without EXIF data
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(temp_path)
            
            # Test the function
            day = datetime(2023, 1, 1)
            result = add_date_to_exif(temp_path, day)
            
            # Check the result - should return False since there's no EXIF data
            assert result is False
        finally:
            # Clean up
            if temp_path.exists():
                temp_path.unlink()


class TestDownloadMediaFiles:
    """Tests for the download_media_files function."""

    @mock.patch("src.kita_scraper.utils.download_file")
    @mock.patch("src.kita_scraper.utils.add_date_to_exif")
    def test_download_media_files_all_success(self, mock_add_date, mock_download):
        """Test downloading media files with all successful."""
        # Configure mocks
        mock_download.return_value = True
        mock_add_date.return_value = True
        
        # Test data
        day = datetime(2023, 1, 1)
        title = "Test Title"
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
        ]
        output_dir = "/tmp"
        
        # Test the function
        success, failed = download_media_files(day, title, urls, output_dir)
        
        # Check the results
        assert success == 2
        assert failed == 0
        assert mock_download.call_count == 2
        assert mock_add_date.call_count == 2
    
    @mock.patch("src.kita_scraper.utils.download_file")
    @mock.patch("src.kita_scraper.utils.add_date_to_exif")
    def test_download_media_files_some_failed(self, mock_add_date, mock_download):
        """Test downloading media files with some failures."""
        # Configure mocks to alternate success/failure
        mock_download.side_effect = [True, False]
        mock_add_date.return_value = True
        
        # Test data
        day = datetime(2023, 1, 1)
        title = "Test Title"
        urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
        ]
        output_dir = "/tmp"
        
        # Test the function
        success, failed = download_media_files(day, title, urls, output_dir)
        
        # Check the results
        assert success == 1
        assert failed == 1
        assert mock_download.call_count == 2
        assert mock_add_date.call_count == 1  # Only called for successful download
    
    @mock.patch("src.kita_scraper.utils.download_file")
    @mock.patch("src.kita_scraper.utils.add_date_to_exif")
    def test_download_media_files_empty_list(self, mock_add_date, mock_download):
        """Test downloading media files with an empty list."""
        # Test data
        day = datetime(2023, 1, 1)
        title = "Test Title"
        urls = []
        output_dir = "/tmp"
        
        # Test the function
        success, failed = download_media_files(day, title, urls, output_dir)
        
        # Check the results
        assert success == 0
        assert failed == 0
        assert mock_download.call_count == 0
        assert mock_add_date.call_count == 0
