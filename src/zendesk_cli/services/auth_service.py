"""Authentication and configuration service."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union

from ..utils.config import ZendeskConfig
from .zendesk_client import ZendeskClient

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and configuration management."""
    
    def __init__(self) -> None:
        """Initialize the authentication service."""
        pass
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> ZendeskConfig:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file. If None, uses default.
            
        Returns:
            ZendeskConfig instance
        """
        logger.info(f"Loading configuration from {config_path or 'default location'}")
        return ZendeskConfig.from_file(config_path)
    
    def save_config(self, config: ZendeskConfig, config_path: Optional[Union[str, Path]] = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save
            config_path: Path to save config. If None, uses default.
        """
        logger.info(f"Saving configuration to {config_path or 'default location'}")
        config.save_to_file(config_path)
    
    def create_client_from_config(self, config: ZendeskConfig) -> ZendeskClient:
        """Create a ZendeskClient from configuration.
        
        Args:
            config: Configuration to use
            
        Returns:
            Configured ZendeskClient instance
        """
        if not config.api_token:
            raise ValueError("API token is required to create client")
            
        return ZendeskClient(
            domain=config.domain,
            email=config.email,
            api_token=config.api_token
        )
    
    def validate_config(self, config: ZendeskConfig) -> bool:
        """Validate that configuration is complete and usable.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required fields
        if not config.domain or not config.email:
            return False
            
        # Check API token is present
        if not config.api_token:
            return False
            
        return True
    
    def get_default_config_path(self) -> Path:
        """Get the default configuration file path.
        
        Returns:
            Path to default config file
        """
        return ZendeskConfig.get_default_config_path()