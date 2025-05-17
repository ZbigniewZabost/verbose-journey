"""Tests for the configuration module."""

import os
import tempfile
from unittest import mock

import pytest

from src.kita_scraper.config import ScraperConfig


class TestScraperConfig:
    """Tests for the ScraperConfig class."""

    def test_init_with_required_fields(self):
        """Test initializing with required fields."""
        config = ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
        )
        
        assert config.email == "test@example.com"
        assert config.password == "password"
        assert config.base_url == "https://example.com"
        assert config.group_id == "123"
        assert config.day_from is None
        assert config.day_to is None
        assert config.output_dir == "/data"
    
    def test_init_with_all_fields(self):
        """Test initializing with all fields."""
        config = ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
            day_from="2023-01-01",
            day_to="2023-01-31",
            output_dir="/custom/data",
        )
        
        assert config.email == "test@example.com"
        assert config.password == "password"
        assert config.base_url == "https://example.com"
        assert config.group_id == "123"
        assert config.day_from == "2023-01-01"
        assert config.day_to == "2023-01-31"
        assert config.output_dir == "/custom/data"
    
    def test_from_env_with_required_fields(self):
        """Test creating from environment with required fields."""
        env = {
            "EMAIL": "test@example.com",
            "PASSWORD": "password",
            "BASE_URL": "https://example.com",
            "GROUP_ID": "123",
        }
        config = ScraperConfig.from_env(env)
        
        assert config.email == "test@example.com"
        assert config.password == "password"
        assert config.base_url == "https://example.com"
        assert config.group_id == "123"
        assert config.day_from is None
        assert config.day_to is None
        assert config.output_dir == "/data"
    
    def test_from_env_with_all_fields(self):
        """Test creating from environment with all fields."""
        env = {
            "EMAIL": "test@example.com",
            "PASSWORD": "password",
            "BASE_URL": "https://example.com",
            "GROUP_ID": "123",
            "DAY_FROM": "2023-01-01",
            "DAY_TO": "2023-01-31",
            "OUTPUT_DIR": "/custom/data",
        }
        config = ScraperConfig.from_env(env)
        
        assert config.email == "test@example.com"
        assert config.password == "password"
        assert config.base_url == "https://example.com"
        assert config.group_id == "123"
        assert config.day_from == "2023-01-01"
        assert config.day_to == "2023-01-31"
        assert config.output_dir == "/custom/data"
    
    def test_from_env_missing_required_fields(self):
        """Test creating from environment with missing required fields."""
        env = {}
        with pytest.raises(ValueError) as excinfo:
            ScraperConfig.from_env(env)
        
        # Check that the error message mentions all missing fields
        error_message = str(excinfo.value)
        assert "EMAIL" in error_message
        assert "PASSWORD" in error_message
        assert "BASE_URL" in error_message
        assert "GROUP_ID" in error_message
    
    def test_from_env_missing_some_required_fields(self):
        """Test creating from environment with some missing required fields."""
        env = {
            "EMAIL": "test@example.com",
            "PASSWORD": "password",
            "BASE_URL": "https://example.com",
        }
        with pytest.raises(ValueError) as excinfo:
            ScraperConfig.from_env(env)
        
        # Check that the error message mentions only the missing fields
        error_message = str(excinfo.value)
        assert "EMAIL" not in error_message
        assert "PASSWORD" not in error_message
        assert "BASE_URL" not in error_message
        assert "GROUP_ID" in error_message
    
    def test_validate_and_set_defaults(self):
        """Test validating and setting defaults."""
        # Create a config with minimal fields
        config = ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
        )
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set the output directory to the temporary directory
            config.output_dir = temp_dir
            
            # Validate and set defaults
            config.validate_and_set_defaults()
            
            # Check that defaults were set
            assert config.day_from is not None
            assert config.day_to is not None
            
            # Check that the output directory exists
            assert os.path.exists(temp_dir)
    
    def test_validate_and_set_defaults_with_existing_values(self):
        """Test validating and setting defaults with existing values."""
        # Create a config with all fields
        config = ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
            day_from="2023-01-01",
            day_to="2023-01-31",
        )
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set the output directory to the temporary directory
            config.output_dir = temp_dir
            
            # Validate and set defaults
            config.validate_and_set_defaults()
            
            # Check that values were not changed
            assert config.day_from == "2023-01-01"
            assert config.day_to == "2023-01-31"
            
            # Check that the output directory exists
            assert os.path.exists(temp_dir)
    
    def test_validate_and_set_defaults_creates_output_dir(self):
        """Test that validate_and_set_defaults creates the output directory if it doesn't exist."""
        # Create a config with minimal fields
        config = ScraperConfig(
            email="test@example.com",
            password="password",
            base_url="https://example.com",
            group_id="123",
        )
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set the output directory to a subdirectory that doesn't exist
            output_dir = os.path.join(temp_dir, "output")
            config.output_dir = output_dir
            
            # Validate and set defaults
            config.validate_and_set_defaults()
            
            # Check that the output directory was created
            assert os.path.exists(output_dir)
