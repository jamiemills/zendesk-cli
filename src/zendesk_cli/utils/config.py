"""Configuration management for zendesk-cli."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel, Field, validator

import keyring

from ..models.exceptions import ConfigurationError, KeyringError, ValidationError


class ZendeskConfig(BaseModel):
    """Zendesk CLI configuration."""
    
    domain: str = Field(..., description="Zendesk domain (e.g., company.zendesk.com)")
    email: str = Field(..., description="User email for authentication")
    api_token: Optional[str] = Field(None, description="API token (stored securely)")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        
    @validator('domain')
    def validate_domain(cls, v: str) -> str:
        """Ensure domain is properly formatted."""
        v = v.lower().strip()
        if not v.endswith('.zendesk.com'):
            if '.' not in v:
                v = f"{v}.zendesk.com"
        return v
    
    @validator('email')
    def validate_email(cls, v: str) -> str:
        """Ensure email is not empty and has basic format validation."""
        v = v.strip()
        if not v:
            raise ValueError("Email cannot be empty")
        if '@' not in v or '.' not in v:
            raise ValueError("Email must be a valid email address")
        return v
    
    @validator('api_token')
    def validate_api_token(cls, v: Optional[str]) -> Optional[str]:
        """Validate API token format if provided."""
        if v is not None:
            v = v.strip()
            if v and len(v) < 10:  # Basic length check
                raise ValueError("API token appears to be too short")
        return v
        
    @classmethod
    def from_file(cls, config_path: Optional[Union[str, Path]] = None) -> ZendeskConfig:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file. If None, uses default path.
            
        Returns:
            ZendeskConfig instance
            
        Raises:
            ConfigurationError: If config file not found or invalid
        """
        if config_path is None:
            config_path = cls.get_default_config_path()
        else:
            # Ensure it's a Path object, not a string
            config_path = Path(config_path)
            
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
            
        try:
            with open(config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(f"Error reading config file: {e}") from e
            
        # Load API token from keyring if not in file
        if 'api_token' not in data:
            try:
                api_token = keyring.get_password(
                    "zendesk-cli", 
                    data.get('email', '')
                )
                data['api_token'] = api_token
            except Exception as e:
                raise KeyringError(
                    f"Failed to retrieve API token from secure storage: {e}"
                ) from e
            
        return cls(**data)
        
    def save_to_file(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Save configuration to file (excluding sensitive data).
        
        Args:
            config_path: Path to save config. If None, uses default path.
        """
        if config_path is None:
            config_path = self.get_default_config_path()
        else:
            # Ensure it's a Path object, not a string
            config_path = Path(config_path)
            
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save API token to keyring
        if self.api_token:
            try:
                keyring.set_password("zendesk-cli", self.email, self.api_token)
            except Exception as e:
                raise KeyringError(
                    f"Failed to save API token to secure storage: {e}"
                ) from e
            
        # Save non-sensitive config to file
        config_data = {
            "domain": self.domain,
            "email": self.email,
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        except (IOError, PermissionError) as e:
            raise ConfigurationError(
                f"Failed to write configuration file to {config_path}: {e}"
            ) from e
            
    @staticmethod
    def get_default_config_path() -> Path:
        """Get default configuration file path.
        
        Returns:
            Path to default config file location
        """
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'zendesk-cli'
        else:  # Unix-like
            config_dir = Path.home() / '.config' / 'zendesk-cli'
        return config_dir / 'config.json'