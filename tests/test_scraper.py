"""Tests for the scraper module."""

from datetime import datetime
from unittest import mock

import pytest
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

from src.kita_scraper.config import ScraperConfig
from src.kita_scraper.scraper import KitaScraper


class TestKitaScraper:
    """Tests for the KitaScraper class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
            day_from="2023-01-01",
            day_to="2023-01-31",
            output_dir="/tmp/data",
        )

    @pytest.fixture
    def mock_driver(self):
        """Create a mock Selenium WebDriver."""
        driver = mock.MagicMock()
        driver.current_url = "https://example.com/dashboard"
        return driver

    def test_init(self, config):
        """Test initialization of the scraper."""
        scraper = KitaScraper(config)
        
        assert scraper.config == config
        assert scraper.driver is None
        assert scraper.stats == {
            "days_checked": 0,
            "journal_entries": 0,
            "gallery_images": 0,
            "attachments": 0,
            "download_success": 0,
            "download_failed": 0,
        }

    @mock.patch("src.kita_scraper.scraper.webdriver.Firefox")
    @mock.patch("src.kita_scraper.scraper.Service")
    @mock.patch("src.kita_scraper.scraper.GeckoDriverManager")
    def test_setup_driver(self, mock_gecko_manager, mock_service, mock_firefox, config):
        """Test setting up the WebDriver."""
        # Configure mocks
        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"
        mock_service.return_value = "mock_service"
        mock_firefox.return_value = "mock_driver"
        
        # Create scraper and call setup_driver
        scraper = KitaScraper(config)
        scraper.setup_driver()
        
        # Check that the driver was set up correctly
        assert scraper.driver == "mock_driver"
        mock_firefox.assert_called_once()
        
    @mock.patch("src.kita_scraper.scraper.webdriver.Firefox")
    @mock.patch("src.kita_scraper.scraper.Service")
    @mock.patch("src.kita_scraper.scraper.GeckoDriverManager")
    def test_setup_driver_error(self, mock_gecko_manager, mock_service, mock_firefox, config):
        """Test error handling when setting up the WebDriver."""
        # Configure mocks to raise an exception
        mock_firefox.side_effect = WebDriverException("Driver error")
        
        # Create scraper and call setup_driver
        scraper = KitaScraper(config)
        
        # Check that the exception is raised
        with pytest.raises(WebDriverException):
            scraper.setup_driver()

    def test_login_success(self, config, mock_driver):
        """Test successful login."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior
        mock_driver.find_element.return_value = mock.MagicMock()
        
        # Call login
        result = scraper.login()
        
        # Check that login was successful
        assert result is True
        
        # Verify that the driver methods were called correctly
        mock_driver.get.assert_called_once_with("https://example.com/sessions/sign_in")
        assert mock_driver.find_element.call_count == 3  # email, password, submit button
        
    def test_login_failure_still_on_login_page(self, config, mock_driver):
        """Test login failure when still on login page."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior
        mock_driver.find_element.return_value = mock.MagicMock()
        mock_driver.current_url = "https://example.com/sessions/sign_in"
        
        # Call login
        result = scraper.login()
        
        # Check that login failed
        assert result is False
        
    def test_login_failure_exception(self, config, mock_driver):
        """Test login failure when an exception is raised."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior to raise an exception
        mock_driver.find_element.side_effect = NoSuchElementException("Element not found")
        
        # Call login
        result = scraper.login()
        
        # Check that login failed
        assert result is False

    def test_get_work_week_days(self, config):
        """Test getting work week days."""
        # Create scraper
        scraper = KitaScraper(config)
        
        # Call get_work_week_days
        days = scraper.get_work_week_days()
        
        # Check that the result is a list of datetime objects
        assert isinstance(days, list)
        assert all(isinstance(day, datetime) for day in days)
        
        # Check that only weekdays are included
        assert all(day.weekday() < 5 for day in days)  # 0-4 are Monday-Friday
        
        # Check that the dates are within the configured range
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31, 23, 59, 59)
        assert all(start_date <= day <= end_date for day in days)

    def test_navigate_to_day_success(self, config, mock_driver):
        """Test successful navigation to a day view."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Call navigate_to_day
        day = datetime(2023, 1, 15)
        result = scraper.navigate_to_day(day)
        
        # Check that navigation was successful
        assert result is True
        
        # Verify that the driver methods were called correctly
        expected_url = "https://example.com/groups/123/calendar/2023-01-15/day"
        mock_driver.get.assert_called_once_with(expected_url)
        
    def test_navigate_to_day_failure(self, config, mock_driver):
        """Test navigation failure."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior to raise an exception
        mock_driver.get.side_effect = TimeoutException("Timeout")
        
        # Call navigate_to_day
        day = datetime(2023, 1, 15)
        result = scraper.navigate_to_day(day)
        
        # Check that navigation failed
        assert result is False

    @mock.patch("src.kita_scraper.scraper.download_media_files")
    def test_scrape_journal_entries(self, mock_download, config, mock_driver):
        """Test scraping journal entries."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior
        mock_entry = mock.MagicMock()
        mock_driver.find_elements.side_effect = [
            [mock_entry],  # First call returns journal entries
            [mock.MagicMock()],  # Second call returns title elements
            [mock.MagicMock()],  # Third call returns photo elements
            [mock.MagicMock()],  # Fourth call returns attachment elements
        ]
        
        # Configure mock element behavior
        mock_photo = mock_driver.find_elements.return_value[0]
        mock_photo.get_attribute.return_value = "https://example.com/image.jpg"
        
        mock_attachment = mock_driver.find_elements.return_value[0]
        mock_attachment.get_attribute.return_value = "https://example.com/file.pdf"
        
        # Configure mock download_media_files
        mock_download.return_value = (1, 0)  # 1 success, 0 failures
        
        # Call scrape_journal_entries
        day = datetime(2023, 1, 15)
        scraper.scrape_journal_entries(day)
        
        # Check that the stats were updated
        assert scraper.stats["journal_entries"] == 1
        assert scraper.stats["gallery_images"] == 1
        assert scraper.stats["attachments"] == 1
        assert scraper.stats["download_success"] == 2
        assert scraper.stats["download_failed"] == 0
        
        # Verify that download_media_files was called
        assert mock_download.call_count == 2

    @mock.patch("src.kita_scraper.scraper.download_media_files")
    def test_scrape_journal_entries_error(self, mock_download, config, mock_driver):
        """Test error handling when scraping journal entries."""
        # Create scraper with mock driver
        scraper = KitaScraper(config)
        scraper.driver = mock_driver
        
        # Configure mock driver behavior to raise an exception
        mock_driver.find_elements.side_effect = NoSuchElementException("Element not found")
        
        # Call scrape_journal_entries
        day = datetime(2023, 1, 15)
        scraper.scrape_journal_entries(day)
        
        # Check that the stats were not updated
        assert scraper.stats["journal_entries"] == 0
        assert scraper.stats["gallery_images"] == 0
        assert scraper.stats["attachments"] == 0
        assert scraper.stats["download_success"] == 0
        assert scraper.stats["download_failed"] == 0
        
        # Verify that download_media_files was not called
        mock_download.assert_not_called()

    @mock.patch.object(KitaScraper, "setup_driver")
    @mock.patch.object(KitaScraper, "login")
    @mock.patch.object(KitaScraper, "get_work_week_days")
    @mock.patch.object(KitaScraper, "navigate_to_day")
    @mock.patch.object(KitaScraper, "scrape_journal_entries")
    def test_run_success(self, mock_scrape, mock_navigate, mock_get_days, mock_login, mock_setup, config):
        """Test successful run of the scraper."""
        # Configure mocks
        mock_login.return_value = True
        mock_get_days.return_value = [datetime(2023, 1, 15), datetime(2023, 1, 16)]
        mock_navigate.return_value = True
        
        # Create scraper
        scraper = KitaScraper(config)
        scraper.driver = mock.MagicMock()
        
        # Call run
        stats = scraper.run()
        
        # Check that the methods were called correctly
        mock_setup.assert_called_once()
        mock_login.assert_called_once()
        mock_get_days.assert_called_once()
        assert mock_navigate.call_count == 2
        assert mock_scrape.call_count == 2
        
        # Check that the stats were updated
        assert stats["days_checked"] == 2
        
        # Check that the driver was quit
        scraper.driver.quit.assert_called_once()

    @mock.patch.object(KitaScraper, "setup_driver")
    @mock.patch.object(KitaScraper, "login")
    def test_run_login_failure(self, mock_login, mock_setup, config):
        """Test run with login failure."""
        # Configure mocks
        mock_login.return_value = False
        
        # Create scraper
        scraper = KitaScraper(config)
        scraper.driver = mock.MagicMock()
        
        # Call run
        stats = scraper.run()
        
        # Check that only setup and login were called
        mock_setup.assert_called_once()
        mock_login.assert_called_once()
        
        # Check that the stats were not updated
        assert stats["days_checked"] == 0
        
        # Check that the driver was quit
        scraper.driver.quit.assert_called_once()

    @mock.patch.object(KitaScraper, "setup_driver")
    def test_run_setup_error(self, mock_setup, config):
        """Test run with setup error."""
        # Configure mocks to raise an exception
        mock_setup.side_effect = WebDriverException("Driver error")
        
        # Create scraper
        scraper = KitaScraper(config)
        
        # Call run
        stats = scraper.run()
        
        # Check that only setup was called
        mock_setup.assert_called_once()
        
        # Check that the stats were not updated
        assert stats["days_checked"] == 0
