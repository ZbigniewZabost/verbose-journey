"""Utility functions for the Kita Scraper."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.request import urlopen

from PIL import Image
import piexif
from pathvalidate import sanitize_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("kita_scraper")


def create_filename(day: datetime, title: str, counter: int, url: str) -> str:
    """Create a sanitized filename for the downloaded file.

    Args:
        day: The date of the journal entry.
        title: The title of the journal entry.
        counter: A counter to ensure unique filenames.
        url: The URL of the file to download.

    Returns:
        str: A sanitized filename.
    """
    original_file_name = url.rsplit("/", 1)[-1]
    extension = original_file_name.rsplit(".", 1)[-1] if "." in original_file_name else ""
    
    base_name = f"{day.strftime('%Y-%m-%d')}_{title}-{counter}"
    # Replace special characters manually to ensure consistent behavior in tests
    sanitized_base = base_name.replace(":", "").replace("/", "").replace("*", "").replace("&", "")
    sanitized_base = sanitize_filename(sanitized_base)
    
    if extension:
        return f"{sanitized_base}.{extension}"
    return sanitized_base


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from a URL and save it to the specified path.

    Args:
        url: The URL of the file to download.
        output_path: The path where the file should be saved.

    Returns:
        bool: True if the download was successful, False otherwise.
    """
    try:
        with urlopen(url) as response:
            content = response.read()
        
        with open(output_path, "wb") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return False


def add_date_to_exif(image_path: Path, day: datetime) -> bool:
    """Add the date to the EXIF data of an image.

    Args:
        image_path: The path to the image file.
        day: The date to add to the EXIF data.

    Returns:
        bool: True if the EXIF data was successfully added, False otherwise.
    """
    try:
        # Only process image files
        if not str(image_path).lower().endswith((".jpg", ".jpeg", ".png", ".tiff", ".tif")):
            logger.debug(f"Skipping EXIF for non-image file: {image_path}")
            return False

        image_file = Image.open(image_path)
        
        # Check if the image has EXIF data
        if "exif" not in image_file.info:
            logger.debug(f"No EXIF data found in {image_path}")
            return False
            
        exif_dict = piexif.load(image_file.info["exif"])
        exif_dict["0th"][piexif.ImageIFD.DateTime] = day.strftime("%Y:%m:%d %H:%M:%S")
        exif_bytes = piexif.dump(exif_dict)
        image_file.save(image_path, exif=exif_bytes)
        return True
    except Exception as e:
        logger.warning(f"Error adding EXIF data to {image_path}: {str(e)}")
        return False


def download_media_files(
    day: datetime, 
    title: str, 
    urls: List[str], 
    output_dir: str
) -> tuple:
    """Download media files from a list of URLs.

    Args:
        day: The date of the journal entry.
        title: The title of the journal entry.
        urls: A list of URLs to download.
        output_dir: The directory where files should be saved.

    Returns:
        tuple: A tuple containing (successful_downloads, failed_downloads).
    """
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        filename = create_filename(day, title, i, url)
        output_path = Path(output_dir) / filename
        
        logger.info(f"Downloading {i}/{len(urls)} - {filename}")
        
        if download_file(url, output_path):
            successful += 1
            # Try to add EXIF data for image files
            add_date_to_exif(output_path, day)
        else:
            failed += 1
    
    return successful, failed
