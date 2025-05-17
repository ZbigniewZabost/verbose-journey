"""Configuration handling for the Kita Scraper."""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ScraperConfig:
    """Configuration for the Kita Scraper.

    Attributes:
        email: Email for login.
        password: Password for login.
        base_url: Base URL of the kita site.
        group_id: Group ID of the kid.
        day_from: Start date for scraping (YYYY-MM-DD).
        day_to: End date for scraping (YYYY-MM-DD).
        output_dir: Directory to save downloaded files.
    """

    email: str
    password: str
    base_url: str
    group_id: str
    day_from: Optional[str] = None
    day_to: Optional[str] = None
    output_dir: str = "/data"

    @classmethod
    def from_env(cls, env=None) -> "ScraperConfig":
        """Create a configuration from environment variables.

        Args:
            env: Optional dictionary to use instead of os.environ.
                 This is primarily used for testing.

        Returns:
            ScraperConfig: Configuration object with values from environment.

        Raises:
            ValueError: If required environment variables are missing.
        """
        if env is None:
            env = os.environ
        
        email = env.get("EMAIL")
        password = env.get("PASSWORD")
        base_url = env.get("BASE_URL")
        group_id = env.get("GROUP_ID")
        day_from = env.get("DAY_FROM")
        day_to = env.get("DAY_TO")
        output_dir = env.get("OUTPUT_DIR", "/data")

        # Validate required fields
        missing = []
        if not email:
            missing.append("EMAIL")
        if not password:
            missing.append("PASSWORD")
        if not base_url:
            missing.append("BASE_URL")
        if not group_id:
            missing.append("GROUP_ID")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            email=email,
            password=password,
            base_url=base_url,
            group_id=group_id,
            day_from=day_from,
            day_to=day_to,
            output_dir=output_dir,
        )

    def validate_and_set_defaults(self) -> None:
        """Validate configuration and set default values if needed."""
        # Set default dates if not provided
        if not self.day_to:
            self.day_to = datetime.now().strftime("%Y-%m-%d")
        if not self.day_from:
            self.day_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
