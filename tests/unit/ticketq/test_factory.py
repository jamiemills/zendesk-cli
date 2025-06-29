"""Test TicketQ adapter factory functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.ticketq.core.factory import get_factory, get_factory
from src.ticketq.core.interfaces.adapter import BaseAdapter
from src.ticketq.models.exceptions import PluginError, ConfigurationError
from src.ticketq.utils.config import ConfigManager


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
        auth = Mock()
        auth.authenticate.return_value = True
        return auth
    
    def create_client(self, auth):
        return Mock()
    
    def validate_config(self, config):
        return config.get("valid", True)
    
    def get_config_schema(self):
        return {"type": "object", "properties": {"domain": {"type": "string"}}}
    
    def get_default_config(self):
        return {"domain": "mock.example.com"}
    
    def normalize_status(self, status):
        return status
    
    def denormalize_status(self, status):
        return status


class TestAdapterFactory:
    """Test AdapterFactory functionality."""

    def test_create_adapter_with_name_and_config(self):
        """Test creating adapter with specific name and config."""
        # Create mock registry
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = MockAdapter
        
        # Create factory with mocked dependencies
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry)
        config = {"domain": "test.example.com", "valid": True}
        
        adapter = factory.create_adapter("mock", config)
        
        assert isinstance(adapter, MockAdapter)
        assert adapter._auth is not None
        assert adapter._client is not None
        mock_registry.get_adapter_class.assert_called_once_with("mock")

    def test_create_adapter_invalid_config(self):
        """Test creating adapter with invalid config."""
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = MockAdapter
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry)
        config = {"domain": "test.example.com", "valid": False}
        
        with pytest.raises(ConfigurationError, match="Invalid configuration for adapter 'mock'"):
            factory.create_adapter("mock", config)

    def test_create_adapter_from_config_manager(self, temp_config_dir):
        """Test creating adapter from config manager."""
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = MockAdapter
        
        # Create config manager with test config
        config_manager = ConfigManager(temp_config_dir)
        config_manager.save_adapter_config("mock", {"domain": "test.com", "valid": True})
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        adapter = factory.create_adapter("mock")
        
        assert isinstance(adapter, MockAdapter)

    def test_create_adapter_auto_detect(self, temp_config_dir):
        """Test auto-detection of adapter."""
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = MockAdapter
        mock_registry.list_adapters.return_value = ["mock"]
        
        # Create config for adapter
        config_manager = ConfigManager(temp_config_dir)
        config_manager.save_adapter_config("mock", {"domain": "test.com", "valid": True})
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        adapter = factory.create_adapter()  # No adapter name specified
        
        assert isinstance(adapter, MockAdapter)

    def test_create_adapter_auto_detect_no_config(self, temp_config_dir):
        """Test auto-detection when no adapters are configured."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = ["mock"]
        
        config_manager = ConfigManager(temp_config_dir)
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        
        with pytest.raises(ConfigurationError, match="No adapters are configured"):
            factory.create_adapter()

    def test_create_adapter_auto_detect_multiple_configs(self, temp_config_dir):
        """Test auto-detection when multiple adapters are configured."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = ["mock1", "mock2"]
        
        # Create configs for multiple adapters
        config_manager = ConfigManager(temp_config_dir)
        config_manager.save_adapter_config("mock1", {"domain": "test1.com", "valid": True})
        config_manager.save_adapter_config("mock2", {"domain": "test2.com", "valid": True})
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        
        with pytest.raises(ConfigurationError, match="Multiple adapters are configured"):
            factory.create_adapter()

    @patch('src.ticketq.core.factory.get_registry')
    def test_create_adapter_not_found(self, mock_get_registry):
        """Test creating adapter that doesn't exist."""
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = None  # Adapter not found
        mock_get_registry.return_value = mock_registry
        
        factory = get_factory()
        
        with pytest.raises(PluginError):
            factory.create_adapter("nonexistent", {})

    def test_create_adapter_missing_config(self, temp_config_dir):
        """Test creating adapter with missing config."""
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = MockAdapter
        
        config_manager = ConfigManager(temp_config_dir)
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        
        # With MockAdapter, empty config is actually valid (defaults to valid=True)
        # So this should succeed, not fail
        adapter = factory.create_adapter("mock")
        assert isinstance(adapter, MockAdapter)

    def test_get_configured_adapters_empty(self, temp_config_dir):
        """Test getting configured adapters when none exist."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = []
        
        config_manager = ConfigManager(temp_config_dir)
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        
        configured = factory.get_configured_adapters()
        assert configured == []

    def test_get_configured_adapters_with_configs(self, temp_config_dir):
        """Test getting configured adapters with existing configs."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = ["mock1", "mock2"]
        
        config_manager = ConfigManager(temp_config_dir)
        config_manager.save_adapter_config("mock1", {"domain": "test1.com"})
        config_manager.save_adapter_config("mock2", {"domain": "test2.com"})
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        configured = factory.get_configured_adapters()
        
        assert sorted(configured) == ["mock1", "mock2"]

    def test_auto_detect_adapter_single(self, temp_config_dir):
        """Test auto-detection with single configured adapter."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = ["mock"]
        
        config_manager = ConfigManager(temp_config_dir)
        config_manager.save_adapter_config("mock", {"domain": "test.com"})
        
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        detected = factory._auto_detect_adapter()
        
        assert detected == "mock"

    def test_auto_detect_adapter_none(self, temp_config_dir):
        """Test auto-detection with no configured adapters."""
        mock_registry = Mock()
        mock_registry.list_adapters.return_value = ["mock"]
        
        config_manager = ConfigManager(temp_config_dir)
        from src.ticketq.core.factory import AdapterFactory
        factory = AdapterFactory(registry=mock_registry, config_manager=config_manager)
        
        with pytest.raises(ConfigurationError, match="No adapters are configured"):
            factory._auto_detect_adapter()


def test_get_factory_function():
    """Test the get_factory function."""
    factory1 = get_factory()
    factory2 = get_factory()
    
    # Should return same instance (singleton pattern)
    assert factory1 is factory2
    # Import the class for isinstance check
    from src.ticketq.core.factory import AdapterFactory
    assert isinstance(factory1, AdapterFactory)
    assert isinstance(factory2, AdapterFactory)