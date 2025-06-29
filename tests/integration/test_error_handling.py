"""Integration tests for error handling edge cases."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ticketq import TicketQLibrary
from ticketq.core.factory import get_factory
from ticketq.core.registry import get_registry
from ticketq.utils.config import ConfigManager
from ticketq.models.exceptions import (
    TicketQError,
    ConfigurationError,
    AuthenticationError,
    NetworkError,
    APIError,
    RateLimitError,
    PluginError,
    ValidationError
)

# Import test helpers
from tests.helpers import create_mock_adapter, create_mock_auth, create_mock_client


class TestErrorHandlingIntegration:
    """Test error handling across the system."""

    def test_configuration_error_scenarios(self):
        """Test various configuration error scenarios."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            
            # Test missing configuration directory
            non_existent_dir = Path(tmp_dir) / "nonexistent"
            config_manager = ConfigManager(non_existent_dir)
            
            # Should create directory automatically
            config = config_manager.get_main_config()
            assert isinstance(config, dict)
            
            # Test invalid JSON in config file
            config_file = config_dir / "zendesk.json"
            config_file.write_text("invalid json content")
            
            config_manager = ConfigManager(config_dir)
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.get_adapter_config("zendesk")
            
            assert "Invalid JSON" in str(exc_info.value)
            assert exc_info.value.suggestions
            assert any("JSON syntax" in suggestion for suggestion in exc_info.value.suggestions)

    def test_plugin_error_scenarios(self):
        """Test plugin-related error scenarios."""
        # Test non-existent adapter
        with pytest.raises(PluginError) as exc_info:
            mock_registry = Mock()
            mock_registry.get_adapter_class.return_value = None
            mock_registry.list_adapters.return_value = ["zendesk"]
            
            from ticketq.core.factory import AdapterFactory
            test_factory = AdapterFactory(registry=mock_registry)
            test_factory.create_adapter("nonexistent", {})
        
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.suggestions
        assert exc_info.value.context.get("plugin_name") == "nonexistent"

    def test_authentication_error_scenarios(self):
        """Test authentication error scenarios."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["authentication"])
        
        # Test authentication failure
        mock_adapter.auth.authenticate.side_effect = AuthenticationError(
            adapter_name="zendesk",
            message="Invalid API token",
            suggestions=[
                "Check your API token in Zendesk settings",
                "Ensure token has proper permissions",
                "Try reconfiguring with: tq configure zendesk"
            ]
        )
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        with pytest.raises(AuthenticationError) as exc_info:
            library.test_connection()
        
        assert "Invalid API token" in str(exc_info.value)
        assert exc_info.value.suggestions
        assert any("API token" in suggestion for suggestion in exc_info.value.suggestions)

    def test_network_error_scenarios(self):
        """Test network-related error scenarios."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Test network timeout
        mock_adapter.client.get_tickets.side_effect = NetworkError(
            adapter_name="zendesk",
            message="Connection timeout",
            suggestions=[
                "Check your internet connection",
                "Verify Zendesk domain is accessible",
                "Try again later"
            ]
        )
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        with pytest.raises(NetworkError) as exc_info:
            library.get_tickets()
        
        assert "Connection timeout" in str(exc_info.value)
        assert exc_info.value.suggestions

    def test_api_error_scenarios(self):
        """Test API-related error scenarios."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Test API error with status code
        mock_adapter.client.get_tickets.side_effect = APIError(
            adapter_name="zendesk",
            message="HTTP 404: Not Found",
            status_code=404,
            suggestions=[
                "Check the ticket ID exists",
                "Verify your permissions",
                "Contact administrator if issue persists"
            ]
        )
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        with pytest.raises(APIError) as exc_info:
            library.get_tickets()
        
        assert "404" in str(exc_info.value)
        assert exc_info.value.context["status_code"] == 404
        assert exc_info.value.suggestions

    def test_rate_limit_error_scenarios(self):
        """Test rate limiting error scenarios."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Test rate limit error
        mock_adapter.client.get_tickets.side_effect = RateLimitError(
            adapter_name="zendesk",
            message="Rate limit exceeded: 429 Too Many Requests",
            retry_after=60,
            suggestions=[
                "Wait 60 seconds before retrying",
                "Reduce request frequency",
                "Consider upgrading your Zendesk plan"
            ]
        )
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        with pytest.raises(RateLimitError) as exc_info:
            library.get_tickets()
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.context.get("retry_after") == 60
        assert exc_info.value.suggestions

    def test_validation_error_scenarios(self):
        """Test validation error scenarios."""
        registry = get_registry()
        adapter_class = registry.get_adapter_class("zendesk")
        adapter = adapter_class()
        
        # Test invalid configuration validation
        invalid_config = {
            "domain": "invalid-domain",  # Missing .zendesk.com
            "email": "not-an-email",     # Invalid email format
            "api_token": "short"         # Too short
        }
        
        result = adapter.validate_config(invalid_config)
        assert result is False

    def test_error_chaining_and_context(self):
        """Test that errors are properly chained and include context."""
        # Test configuration error with original exception
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            
            # Create invalid JSON file
            invalid_file = config_dir / "zendesk.json"
            invalid_file.write_text("{invalid json}")
            
            config_manager = ConfigManager(config_dir)
            
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.get_adapter_config("zendesk")
            
            # Check that original exception is preserved
            error = exc_info.value
            assert error.context.get("config_file") == str(invalid_file)
            assert error.original_error is not None

    def test_error_message_helpfulness(self):
        """Test that error messages provide helpful information."""
        factory = get_factory()
        
        # Test factory with no adapters
        mock_registry = Mock()
        mock_registry.get_adapter_class.return_value = None
        mock_registry.list_adapters.return_value = []
        
        from ticketq.core.factory import AdapterFactory
        test_factory = AdapterFactory(registry=mock_registry)
        
        with pytest.raises(PluginError) as exc_info:
            test_factory.create_adapter("missing", {})
        
        error = exc_info.value
        assert error.suggestions
        assert len(error.suggestions) >= 2  # Should provide multiple suggestions
        assert any("install" in suggestion.lower() for suggestion in error.suggestions)

    def test_error_context_preservation(self):
        """Test that error context is preserved through the stack."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Create an error at the client level
        original_error = ConnectionError("Network unreachable")
        mock_adapter.client.get_tickets.side_effect = NetworkError(
            adapter_name="zendesk",
            message="Failed to connect to Zendesk API",
            original_error=original_error,
            suggestions=["Check network connection"]
        )
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        with pytest.raises(NetworkError) as exc_info:
            library.get_tickets()
        
        # Verify error context is preserved
        error = exc_info.value
        assert error.original_error is original_error
        assert "Failed to connect to Zendesk API" in str(error)
        assert error.suggestions

    def test_graceful_degradation(self):
        """Test that system degrades gracefully when components fail."""
        # Test that factory continues to work even when some adapters fail to load
        mock_registry = Mock()
        
        # Mock a registry that has some working and some broken adapters
        def mock_get_adapter_class(name):
            if name == "zendesk":
                return get_registry().get_adapter_class("zendesk")
            elif name == "broken":
                raise ImportError("Broken adapter")
            else:
                return None
        
        mock_registry.get_adapter_class = mock_get_adapter_class
        mock_registry.list_adapters.return_value = ["zendesk"]
        
        from ticketq.core.factory import AdapterFactory
        test_factory = AdapterFactory(registry=mock_registry)
        
        # Should be able to work with working adapter
        available = test_factory.list_available_adapters()
        assert "zendesk" in available

    def test_user_friendly_error_formatting(self):
        """Test that errors are formatted in a user-friendly way."""
        error = ConfigurationError(
            "No adapters configured",
            suggestions=[
                "Configure an adapter with: tq configure zendesk",
                "Install an adapter with: pip install ticketq-zendesk",
                "Check available adapters with: tq adapters"
            ]
        )
        
        error_str = str(error)
        assert "No adapters configured" in error_str
        
        # Check that suggestions are accessible
        assert error.suggestions
        assert len(error.suggestions) == 3
        assert all(isinstance(suggestion, str) for suggestion in error.suggestions)

    def test_exception_hierarchy_inheritance(self):
        """Test that exception hierarchy is properly implemented."""
        # All TicketQ exceptions should inherit from TicketQError
        assert issubclass(ConfigurationError, TicketQError)
        assert issubclass(AuthenticationError, TicketQError)
        assert issubclass(NetworkError, TicketQError)
        assert issubclass(APIError, TicketQError)
        assert issubclass(RateLimitError, APIError)  # Rate limit is a type of API error
        assert issubclass(PluginError, TicketQError)
        assert issubclass(ValidationError, TicketQError)
        
        # Test that they can be caught by the base exception
        try:
            raise ConfigurationError("Test error")
        except TicketQError:
            pass  # Should catch it
        else:
            pytest.fail("ConfigurationError should be caught by TicketQError")