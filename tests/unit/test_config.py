"""Tests for configuration management."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock

from zendesk_cli.models.exceptions import ConfigurationError


class TestZendeskConfig:
    """Test ZendeskConfig configuration management."""
    
    def test_config_creation_with_valid_data(self) -> None:
        """Test creating config with valid data."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="example.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        assert config.domain == "example.zendesk.com"
        assert config.email == "test@example.com"
        assert config.api_token == "test_token"
    
    def test_domain_validation_adds_zendesk_suffix(self) -> None:
        """Test domain validation adds .zendesk.com suffix."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="example",
            email="test@example.com",
            api_token="test_token"
        )
        
        assert config.domain == "example.zendesk.com"
    
    def test_domain_validation_preserves_full_domain(self) -> None:
        """Test domain validation preserves full domain."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="EXAMPLE.ZENDESK.COM",
            email="test@example.com",
            api_token="test_token"
        )
        
        assert config.domain == "example.zendesk.com"  # Lowercased
    
    def test_config_validation_requires_email(self) -> None:
        """Test config validation requires email."""
        from zendesk_cli.utils.config import ZendeskConfig
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ZendeskConfig(
                domain="example.zendesk.com",
                email="",  # Empty email
                api_token="test_token"
            )
    
    def test_save_to_file(self) -> None:
        """Test saving configuration to file."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            config = ZendeskConfig(
                domain="example.zendesk.com",
                email="test@example.com",
                api_token="secret_token"
            )
            
            with patch('keyring.set_password') as mock_keyring:
                config.save_to_file(config_path)
                
                # Verify API token was stored in keyring
                mock_keyring.assert_called_once_with(
                    "zendesk-cli", 
                    "test@example.com", 
                    "secret_token"
                )
                
                # Verify config file was created without sensitive data
                assert config_path.exists()
                with open(config_path) as f:
                    saved_data = json.load(f)
                
                assert saved_data["domain"] == "example.zendesk.com"
                assert saved_data["email"] == "test@example.com"
                assert "api_token" not in saved_data  # Should not be in file
    
    def test_load_from_file(self) -> None:
        """Test loading configuration from file."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create test config file
            config_data = {
                "domain": "example.zendesk.com",
                "email": "test@example.com"
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            with patch('keyring.get_password', return_value="secret_token"):
                config = ZendeskConfig.from_file(config_path)
                
                assert config.domain == "example.zendesk.com"
                assert config.email == "test@example.com"
                assert config.api_token == "secret_token"
    
    def test_load_from_file_missing_file(self) -> None:
        """Test loading from non-existent file raises error."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        with pytest.raises(ConfigurationError):
            ZendeskConfig.from_file(Path("/non/existent/config.json"))
    
    def test_load_from_file_missing_token_in_keyring(self) -> None:
        """Test loading when token is missing from keyring."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            config_data = {
                "domain": "example.zendesk.com",
                "email": "test@example.com"
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            with patch('keyring.get_password', return_value=None):
                config = ZendeskConfig.from_file(config_path)
                
                assert config.api_token is None
    
    def test_default_config_path(self) -> None:
        """Test default configuration path calculation."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        default_path = ZendeskConfig.get_default_config_path()
        
        assert "zendesk-cli" in str(default_path)
        assert "config.json" in str(default_path)
    
    def test_config_path_respects_os(self) -> None:
        """Test config path differs by operating system."""
        from zendesk_cli.utils.config import ZendeskConfig
        
        # Test Unix-like path
        with patch('os.name', 'posix'):
            unix_path = ZendeskConfig.get_default_config_path()
            assert ".config" in str(unix_path)
        
        # Test Windows path
        with patch('os.name', 'nt'), \
             patch.dict('os.environ', {'APPDATA': '/fake/appdata'}):
            windows_path = ZendeskConfig.get_default_config_path()
            assert "appdata" in str(windows_path).lower()


class TestAuthService:
    """Test AuthService functionality."""
    
    def test_auth_service_initialization(self) -> None:
        """Test AuthService initialization."""
        from zendesk_cli.services.auth_service import AuthService
        
        service = AuthService()
        assert service is not None
    
    def test_load_config_from_file(self) -> None:
        """Test loading configuration from file."""
        from zendesk_cli.services.auth_service import AuthService
        from zendesk_cli.utils.config import ZendeskConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            # Create and save a config
            config = ZendeskConfig(
                domain="example.zendesk.com",
                email="test@example.com",
                api_token="test_token"
            )
            
            with patch('keyring.set_password'):
                config.save_to_file(config_path)
            
            # Load it back via AuthService
            service = AuthService()
            
            with patch('keyring.get_password', return_value="test_token"):
                loaded_config = service.load_config(config_path)
                
                assert loaded_config.domain == "example.zendesk.com"
                assert loaded_config.email == "test@example.com"
                assert loaded_config.api_token == "test_token"
    
    def test_save_config(self) -> None:
        """Test saving configuration."""
        from zendesk_cli.services.auth_service import AuthService
        from zendesk_cli.utils.config import ZendeskConfig
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            config = ZendeskConfig(
                domain="example.zendesk.com",
                email="test@example.com",
                api_token="test_token"
            )
            
            service = AuthService()
            
            with patch('keyring.set_password') as mock_keyring:
                service.save_config(config, config_path)
                
                mock_keyring.assert_called_once()
                assert config_path.exists()
    
    def test_create_client_from_config(self) -> None:
        """Test creating ZendeskClient from config."""
        from zendesk_cli.services.auth_service import AuthService
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="example.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        service = AuthService()
        client = service.create_client_from_config(config)
        
        assert client.domain == "example.zendesk.com"
        assert client.email == "test@example.com"
    
    def test_validate_config_valid(self) -> None:
        """Test validating a valid configuration."""
        from zendesk_cli.services.auth_service import AuthService
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="example.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        service = AuthService()
        is_valid = service.validate_config(config)
        
        assert is_valid is True
    
    def test_validate_config_missing_token(self) -> None:
        """Test validating config with missing token."""
        from zendesk_cli.services.auth_service import AuthService
        from zendesk_cli.utils.config import ZendeskConfig
        
        config = ZendeskConfig(
            domain="example.zendesk.com",
            email="test@example.com",
            api_token=None
        )
        
        service = AuthService()
        is_valid = service.validate_config(config)
        
        assert is_valid is False