"""Integration tests for the plugin system."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from ticketq.core.registry import get_registry
from ticketq.core.factory import get_factory
from ticketq.models.exceptions import PluginError, ConfigurationError


class TestPluginSystemIntegration:
    """Test plugin system integration."""

    def test_plugin_discovery(self):
        """Test that plugins are discovered via entry points."""
        registry = get_registry()
        registry.discover_adapters()
        
        available = registry.get_available_adapters()
        assert "zendesk" in available
        
        zendesk_adapter = available["zendesk"]
        assert hasattr(zendesk_adapter, 'name')
        assert hasattr(zendesk_adapter, 'display_name')
        assert hasattr(zendesk_adapter, 'version')

    def test_plugin_instantiation(self):
        """Test that plugins can be instantiated."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        
        assert adapter_class is not None
        
        # Test instantiation
        adapter = adapter_class()
        assert adapter.name == "zendesk"
        assert adapter.display_name == "Zendesk"
        assert adapter.version == "0.1.0"
        assert "tickets" in adapter.supported_features

    def test_factory_integration(self):
        """Test factory integration with plugins."""
        factory = get_factory()
        
        # Test adapter listing
        available = factory.list_available_adapters()
        assert "zendesk" in available
        assert available["zendesk"]["name"] == "zendesk"

    def test_plugin_config_validation(self):
        """Test plugin configuration validation."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        # Test valid config
        valid_config = {
            "domain": "test.zendesk.com",
            "email": "test@example.com",
            "api_token": "test_token_with_proper_length"
        }
        assert adapter.validate_config(valid_config) is True
        
        # Test invalid config - missing fields
        invalid_config = {"domain": "test.zendesk.com"}
        assert adapter.validate_config(invalid_config) is False

    def test_plugin_interface_compliance(self):
        """Test that plugins implement required interface methods."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        # Test required properties
        assert hasattr(adapter, 'name')
        assert hasattr(adapter, 'display_name')
        assert hasattr(adapter, 'version')
        assert hasattr(adapter, 'supported_features')
        
        # Test required methods
        assert hasattr(adapter, 'create_auth')
        assert hasattr(adapter, 'create_client')
        assert hasattr(adapter, 'validate_config')
        assert hasattr(adapter, 'get_config_schema')
        assert hasattr(adapter, 'normalize_status')

    def test_plugin_auth_client_creation(self):
        """Test that plugins can create auth and client instances."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        config = {
            "domain": "test.zendesk.com",
            "email": "test@example.com",
            "api_token": "test_token_with_proper_length"
        }
        
        # Test auth creation
        auth = adapter.create_auth(config)
        assert auth is not None
        assert hasattr(auth, 'authenticate')
        assert hasattr(auth, 'get_auth_headers')
        
        # Test client creation
        client = adapter.create_client(auth)
        assert client is not None
        assert hasattr(client, 'get_tickets')
        assert hasattr(client, 'get_current_user')
        assert hasattr(client, 'get_groups')

    def test_plugin_status_normalization(self):
        """Test plugin status normalization."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        # Test Zendesk status mapping
        assert adapter.normalize_status("new") == "new"
        assert adapter.normalize_status("open") == "open"  
        assert adapter.normalize_status("pending") == "pending"
        assert adapter.normalize_status("solved") == "solved"
        assert adapter.normalize_status("closed") == "closed"
        
        # Test denormalization
        assert adapter.denormalize_status("open") == "open"
        assert adapter.denormalize_status("solved") == "solved"

    def test_plugin_config_schema(self):
        """Test plugin configuration schema."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        schema = adapter.get_config_schema()
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        
        # Check required Zendesk fields
        properties = schema["properties"]
        assert "domain" in properties
        assert "email" in properties
        assert "api_token" in properties

    def test_registry_singleton_behavior(self):
        """Test that registry maintains singleton behavior."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
        
        # Both should have same adapters
        adapters1 = registry1.get_available_adapters()
        adapters2 = registry2.get_available_adapters()
        assert adapters1.keys() == adapters2.keys()

    def test_factory_singleton_behavior(self):
        """Test that factory maintains singleton behavior."""
        factory1 = get_factory()
        factory2 = get_factory()
        
        assert factory1 is factory2
        
        # Both should list same adapters
        available1 = factory1.list_available_adapters()
        available2 = factory2.list_available_adapters()
        assert available1.keys() == available2.keys()