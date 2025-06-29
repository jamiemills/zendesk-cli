"""Test TicketQ adapter registry functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ticketq.core.registry import AdapterRegistry, get_registry
from src.ticketq.core.interfaces.adapter import BaseAdapter
from src.ticketq.models.exceptions import PluginError


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""
    
    @property
    def name(self) -> str:
        return "mock"
    
    @property
    def display_name(self) -> str:
        return "Mock Adapter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def supported_features(self) -> list[str]:
        return ["tickets", "users"]
    
    def get_auth_class(self):
        return Mock
    
    def get_client_class(self):
        return Mock
    
    def create_auth(self, config):
        return Mock()
    
    def create_client(self, auth):
        return Mock()
    
    def validate_config(self, config):
        return True
    
    def get_config_schema(self):
        return {"type": "object", "properties": {}}
    
    def get_default_config(self):
        return {}
    
    def normalize_status(self, status):
        return status
    
    def denormalize_status(self, status):
        return status


class TestAdapterRegistry:
    """Test AdapterRegistry functionality."""

    def test_registry_singleton(self):
        """Test that registry follows singleton pattern."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    @patch('src.ticketq.core.registry.entry_points')
    def test_discover_adapters_success(self, mock_entry_points):
        """Test successful adapter discovery."""
        # Mock entry points
        mock_ep = Mock()
        mock_ep.name = "mock"
        mock_ep.load.return_value = MockAdapter
        
        mock_entry_points.return_value.select.return_value = [mock_ep]
        
        registry = AdapterRegistry()
        registry.discover_adapters()
        
        adapters = registry.get_available_adapters()
        assert "mock" in adapters
        assert adapters["mock"] is MockAdapter

    @patch('src.ticketq.core.registry.entry_points')
    def test_discover_adapters_load_failure(self, mock_entry_points):
        """Test adapter discovery with load failure."""
        # Mock entry point that fails to load
        mock_ep = Mock()
        mock_ep.name = "broken"
        mock_ep.load.side_effect = ImportError("Module not found")
        
        mock_entry_points.return_value.select.return_value = [mock_ep]
        
        registry = AdapterRegistry()
        registry.discover_adapters()
        
        # Should not contain the broken adapter
        adapters = registry.get_available_adapters()
        assert "broken" not in adapters

    @patch('src.ticketq.core.registry.entry_points')
    def test_discover_adapters_invalid_adapter(self, mock_entry_points):
        """Test discovery with invalid adapter class."""
        # Mock entry point that loads non-adapter class
        mock_ep = Mock()
        mock_ep.name = "invalid"
        mock_ep.load.return_value = str  # Not an adapter class
        
        mock_entry_points.return_value.select.return_value = [mock_ep]
        
        registry = AdapterRegistry()
        registry.discover_adapters()
        
        # Should not contain the invalid adapter
        adapters = registry.get_available_adapters()
        assert "invalid" not in adapters

    def test_register_adapter(self):
        """Test manual adapter registration."""
        registry = AdapterRegistry()
        registry._adapters.clear()  # Clear any discovered adapters
        
        registry.register_adapter("test", MockAdapter)
        
        adapters = registry.get_available_adapters()
        assert "test" in adapters
        assert adapters["test"] is MockAdapter

    def test_register_duplicate_adapter(self):
        """Test registering duplicate adapter name."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        
        registry.register_adapter("test", MockAdapter)
        
        # Should not raise error when registering duplicate
        registry.register_adapter("test", MockAdapter)
        
        adapters = registry.get_available_adapters()
        assert len(adapters) == 1

    def test_get_adapter_exists(self):
        """Test getting existing adapter."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        registry.register_adapter("test", MockAdapter)
        
        adapter_class = registry.get_adapter_class("test")
        assert adapter_class is MockAdapter

    def test_get_adapter_not_exists(self):
        """Test getting non-existent adapter."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        
        adapter_class = registry.get_adapter_class("nonexistent")
        assert adapter_class is None

    def test_is_adapter_available(self):
        """Test checking adapter availability."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        registry.register_adapter("test", MockAdapter)
        
        assert registry.is_adapter_available("test") is True
        assert registry.is_adapter_available("nonexistent") is False

    def test_list_adapters_empty(self):
        """Test listing adapters when none are available."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        
        adapters = registry.list_adapters()
        assert adapters == []

    def test_list_adapters_with_adapters(self):
        """Test listing adapters when some are available."""
        registry = AdapterRegistry()
        registry._adapters.clear()
        registry.register_adapter("test", MockAdapter)
        
        adapters = registry.list_adapters()
        assert adapters == ["test"]

    @patch('src.ticketq.core.registry.entry_points')
    def test_discovery_caching(self, mock_entry_points):
        """Test that adapter discovery is cached."""
        mock_ep = Mock()
        mock_ep.name = "mock"
        mock_ep.load.return_value = MockAdapter
        
        mock_entry_points.return_value.select.return_value = [mock_ep]
        
        registry = AdapterRegistry()
        
        # First call should discover
        adapters1 = registry.list_adapters()
        
        # Second call should use cache
        adapters2 = registry.list_adapters()
        
        # Should only call entry_points once
        assert mock_entry_points.call_count == 1
        assert adapters1 == adapters2

    def test_clear_adapters(self):
        """Test clearing registered adapters."""
        registry = AdapterRegistry()
        registry.register_adapter("test", MockAdapter)
        
        assert "test" in registry.list_adapters()
        
        registry._adapters.clear()
        
        assert registry.list_adapters() == []


def test_get_registry_function():
    """Test the get_registry function."""
    from src.ticketq.core.registry import get_registry
    
    registry1 = get_registry()
    registry2 = get_registry()
    
    assert registry1 is registry2
    assert isinstance(registry1, AdapterRegistry)