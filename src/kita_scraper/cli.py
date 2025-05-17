#!/usr/bin/env python3
"""Command-line interface for the Kita Scraper."""

import argparse
import logging
import sys
from typing import Dict, Any

from src.kita_scraper.config import ScraperConfig
from src.kita_scraper.scraper import KitaScraper
from src.kita_scraper.utils import logger


def parse_arguments() -> Dict[str, Any]:
    """Parse command line arguments.

    Returns:
        Dict[str, Any]: A dictionary of parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Scrape pictures from your kita site and save them locally."
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save downloaded files (default: /data)",
        default=None,
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors",
    )
    
    return vars(parser.parse_args())


def configure_logging(args: Dict[str, Any]) -> None:
    """Configure logging based on command line arguments.

    Args:
        args: Command line arguments.
    """
    if args["verbose"]:
        logger.setLevel(logging.DEBUG)
    elif args["quiet"]:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)


def main() -> int:
    """Main entry point for the application.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging
    configure_logging(args)
    
    try:
        # Load configuration from environment variables
        config = ScraperConfig.from_env()
        
        # Override output directory if specified on command line
        if args["output_dir"]:
            config.output_dir = args["output_dir"]
        
        # Create and run the scraper
        scraper = KitaScraper(config)
        stats = scraper.run()
        
        # Check if there were any failures
        if stats["download_failed"] > 0:
            logger.warning(f"Failed to download {stats['download_failed']} files")
            return 1
        
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
