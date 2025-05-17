"""Main scraper module for the Kita Scraper."""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from webdriver_manager.firefox import GeckoDriverManager
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
from dateutil import parser

from src.kita_scraper.config import ScraperConfig
from src.kita_scraper.utils import download_media_files, logger


class KitaScraper:
    """A class to scrape pictures and attachments from a kita website.

    This class handles the web scraping logic, including login, navigation,
    and downloading of images and attachments.
    """

    def __init__(self, config: ScraperConfig):
        """Initialize the KitaScraper with the given configuration.

        Args:
            config: The configuration for the scraper.
        """
        self.config = config
        self.driver = None
        self.stats = {
            "days_checked": 0,
            "journal_entries": 0,
            "gallery_images": 0,
            "attachments": 0,
            "download_success": 0,
            "download_failed": 0,
        }

    def setup_driver(self) -> None:
        """Set up the Selenium WebDriver for Firefox.

        Raises:
            WebDriverException: If there's an error setting up the WebDriver.
        """
        logger.info("Setting up WebDriver")
        try:
            options = Options()
            options.add_argument("--headless")
            self.driver = webdriver.Firefox(
                service=Service(GeckoDriverManager().install()),
                options=options,
            )
        except WebDriverException as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            raise

    def login(self) -> bool:
        """Log in to the kita website.

        Returns:
            bool: True if login was successful, False otherwise.

        Raises:
            WebDriverException: If there's an error during login.
        """
        login_url = f"{self.config.base_url}/sessions/sign_in"
        logger.info(f"Signing into {self.config.base_url} with email {self.config.email}")
        
        try:
            self.driver.get(login_url)
            self.driver.find_element(By.ID, "user_email").send_keys(self.config.email)
            self.driver.find_element(By.ID, "user_password").send_keys(self.config.password)
            self.driver.find_element(By.NAME, "commit").click()
            
            # Wait for page to load
            WebDriverWait(driver=self.driver, timeout=10).until(
                lambda x: x.execute_script("return document.readyState === 'complete'")
            )
            
            # Check if login was successful (could check for error messages or redirects)
            current_url = self.driver.current_url
            if "/sessions/sign_in" in current_url:
                logger.error("Login failed - still on login page")
                return False
                
            return True
        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            logger.error(f"Error during login: {str(e)}")
            return False

    def get_work_week_days(self) -> List[datetime]:
        """Get a list of work week days (Monday to Friday) between the configured dates.

        Returns:
            List[datetime]: A list of datetime objects representing work days.
        """
        logger.info(f"Getting work week days between {self.config.day_from} and {self.config.day_to}")
        start_date = parser.parse(self.config.day_from)
        end_date = parser.parse(self.config.day_to)
        
        return list(rrule(
            DAILY,
            dtstart=start_date,
            until=end_date,
            byweekday=(MO, TU, WE, TH, FR)
        ))

    def navigate_to_day(self, day: datetime) -> bool:
        """Navigate to the day view for the specified date.

        Args:
            day: The date to navigate to.

        Returns:
            bool: True if navigation was successful, False otherwise.
        """
        day_string = day.strftime("%Y-%m-%d")
        logger.info(f"Navigating to {day_string} day view for group {self.config.group_id}")
        
        day_view_url = f"{self.config.base_url}/groups/{self.config.group_id}/calendar/{day_string}/day"
        
        try:
            self.driver.get(day_view_url)
            WebDriverWait(driver=self.driver, timeout=10).until(
                lambda x: x.execute_script("return document.readyState === 'complete'")
            )
            return True
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Error navigating to day view: {str(e)}")
            return False

    def scrape_journal_entries(self, day: datetime) -> None:
        """Scrape journal entries for the specified day.

        Args:
            day: The date to scrape journal entries for.
        """
        try:
            entries = self.driver.find_elements(By.CLASS_NAME, "JournalEntrySmall")
            self.stats["journal_entries"] += len(entries)
            logger.info(f"Found {len(entries)} journal entries in the day view")
            
            for entry in entries:
                self._process_journal_entry(entry, day)
                
        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            logger.error(f"Error scraping journal entries: {str(e)}")

    def _process_journal_entry(self, entry_element, day: datetime) -> None:
        """Process a single journal entry.

        Args:
            entry_element: The Selenium element representing the journal entry.
            day: The date of the journal entry.
        """
        images_urls = []
        attachments_urls = []
        
        try:
            # Click on the entry to open the modal
            entry_element.click()
            WebDriverWait(driver=self.driver, timeout=10).until(
                lambda x: x.execute_script("return document.readyState === 'complete'")
            )
            
            # Get the entry title
            entry_title = "no_entry_title"
            entry_title_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'title-light')]"
            )
            if entry_title_elements:
                entry_title = entry_title_elements[0].text
                logger.info(f"Entry title: {entry_title[:80]}")
                entry_title = entry_title[:25]  # Truncate for filename
            
            # Get images from the gallery
            photos_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'carousel-item')]/img[@loading='lazy']"
            )
            for photo in photos_elements:
                images_urls.append(photo.get_attribute("src"))
            
            # Download images
            if images_urls:
                success, failed = download_media_files(
                    day, entry_title, images_urls, self.config.output_dir
                )
                self.stats["gallery_images"] += len(images_urls)
                self.stats["download_success"] += success
                self.stats["download_failed"] += failed
            
            # Get attachments
            attachments = self.driver.find_elements(
                By.XPATH, "//table/tbody/tr/td/a[contains(@class, 'btn-light') and contains(@class, 'btn')]"
            )
            for attachment in attachments:
                attachments_urls.append(attachment.get_attribute("href"))
            
            # Download attachments
            if attachments_urls:
                success, failed = download_media_files(
                    day, entry_title, attachments_urls, self.config.output_dir
                )
                self.stats["attachments"] += len(attachments_urls)
                self.stats["download_success"] += success
                self.stats["download_failed"] += failed
            
            # Close the modal
            self.driver.find_element(By.XPATH, '//a[contains(@class, "new-modal__close")]').click()
            
            logger.info(f"Found {len(images_urls)} images and {len(attachments_urls)} attachments")
            
        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            logger.error(f"Error processing journal entry: {str(e)}")
            # Try to close the modal if it's open
            try:
                self.driver.find_element(By.XPATH, '//a[contains(@class, "new-modal__close")]').click()
            except:
                pass

    def run(self) -> Dict:
        """Run the scraper.

        Returns:
            Dict: Statistics about the scraping process.
        """
        # Validate and set defaults for configuration
        self.config.validate_and_set_defaults()
        
        try:
            # Setup WebDriver
            self.setup_driver()
            
            # Login
            if not self.login():
                logger.error("Login failed. Aborting.")
                return self.stats
            
            # Get work week days
            days = self.get_work_week_days()
            
            # Process each day
            for day in days:
                self.stats["days_checked"] += 1
                
                # Navigate to day view
                if not self.navigate_to_day(day):
                    logger.warning(f"Failed to navigate to day {day.strftime('%Y-%m-%d')}. Skipping.")
                    continue
                
                # Scrape journal entries
                self.scrape_journal_entries(day)
                
                # Small delay to avoid overloading the server
                time.sleep(1)
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self.stats
            
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
            
            # Print summary
            self._print_summary()
    
    def _print_summary(self) -> None:
        """Print a summary of the scraping process."""
        logger.info("Summary:")
        logger.info(f"Checked {self.stats['days_checked']} days between {self.config.day_from} and {self.config.day_to}")
        logger.info(f"Visited {self.stats['journal_entries']} journal entries")
        logger.info(f"Found {self.stats['gallery_images']} images in galleries and {self.stats['attachments']} files in attachments")
        logger.info(f"Successfully downloaded {self.stats['download_success']} files")
        if self.stats['download_failed'] > 0:
            logger.warning(f"Failed to download {self.stats['download_failed']} files")
