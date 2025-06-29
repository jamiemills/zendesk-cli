"""Test Zendesk adapter functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ticketq_zendesk.adapter import ZendeskAdapter
from src.ticketq_zendesk.auth import ZendeskAuth
from src.ticketq_zendesk.client import ZendeskClient


class TestZendeskAdapter:
    """Test ZendeskAdapter functionality."""

    def test_adapter_properties(self):
        """Test adapter basic properties."""
        adapter = ZendeskAdapter()
        
        assert adapter.name == "zendesk"
        assert adapter.display_name == "Zendesk"
        assert adapter.version == "0.1.0"
        assert "tickets" in adapter.supported_features
        assert "users" in adapter.supported_features
        assert "groups" in adapter.supported_features

    def test_get_auth_class(self):
        """Test getting authentication class."""
        adapter = ZendeskAdapter()
        auth_class = adapter.get_auth_class()
        
        assert auth_class is ZendeskAuth

    def test_get_client_class(self):
        """Test getting client class."""
        adapter = ZendeskAdapter()
        client_class = adapter.get_client_class()
        
        assert client_class is ZendeskClient

    def test_create_auth(self):
        """Test creating authentication instance."""
        adapter = ZendeskAdapter()
        config = {
            "domain": "test.zendesk.com",
            "email": "test@example.com",
            "api_token": "token123"
        }
        
        auth = adapter.create_auth(config)
        
        assert isinstance(auth, ZendeskAuth)

    def test_create_client(self):
        """Test creating client instance."""
        adapter = ZendeskAdapter()
        mock_auth = Mock()
        mock_auth.get_auth_headers.return_value = {
            'Authorization': 'Basic dGVzdEB0ZXN0LmNvbS90b2tlbjp0ZXN0X3Rva2Vu'
        }
        
        client = adapter.create_client(mock_auth)
        
        assert isinstance(client, ZendeskClient)
        assert client.auth is mock_auth

    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        adapter = ZendeskAdapter()
        config = {
            "domain": "company.zendesk.com",
            "email": "user@company.com",
            "api_token": "valid_token_123"
        }
        
        assert adapter.validate_config(config) is True

    def test_validate_config_missing_fields(self):
        """Test config validation with missing fields."""
        adapter = ZendeskAdapter()
        
        # Missing domain
        config = {
            "email": "user@company.com",
            "api_token": "token123"
        }
        assert adapter.validate_config(config) is False
        
        # Missing email
        config = {
            "domain": "company.zendesk.com",
            "api_token": "token123"
        }
        assert adapter.validate_config(config) is False
        
        # Missing api_token
        config = {
            "domain": "company.zendesk.com",
            "email": "user@company.com"
        }
        assert adapter.validate_config(config) is False

    def test_validate_config_invalid_domain(self):
        """Test config validation with invalid domain."""
        adapter = ZendeskAdapter()
        config = {
            "domain": "invalid-domain.com",  # Should end with .zendesk.com
            "email": "user@company.com",
            "api_token": "token123"
        }
        
        assert adapter.validate_config(config) is False

    def test_validate_config_invalid_email(self):
        """Test config validation with invalid email."""
        adapter = ZendeskAdapter()
        config = {
            "domain": "company.zendesk.com",
            "email": "invalid-email",  # Missing @ symbol
            "api_token": "token123"
        }
        
        assert adapter.validate_config(config) is False

    def test_validate_config_short_token(self):
        """Test config validation with too short API token."""
        adapter = ZendeskAdapter()
        config = {
            "domain": "company.zendesk.com",
            "email": "user@company.com",
            "api_token": "short"  # Too short
        }
        
        assert adapter.validate_config(config) is False

    def test_get_config_schema(self):
        """Test getting configuration schema."""
        adapter = ZendeskAdapter()
        schema = adapter.get_config_schema()
        
        assert schema["type"] == "object"
        assert "domain" in schema["properties"]
        assert "email" in schema["properties"]
        assert "api_token" in schema["properties"]
        assert schema["required"] == ["domain", "email", "api_token"]

    def test_get_default_config(self):
        """Test getting default configuration."""
        adapter = ZendeskAdapter()
        config = adapter.get_default_config()
        
        assert "domain" in config
        assert "email" in config
        assert "api_token" in config
        assert config["domain"] == "your-company.zendesk.com"

    def test_normalize_status(self):
        """Test status normalization."""
        adapter = ZendeskAdapter()
        
        # Zendesk statuses map directly
        assert adapter.normalize_status("new") == "new"
        assert adapter.normalize_status("open") == "open"
        assert adapter.normalize_status("pending") == "pending"
        assert adapter.normalize_status("hold") == "hold"
        assert adapter.normalize_status("solved") == "solved"
        assert adapter.normalize_status("closed") == "closed"
        
        # Case insensitive
        assert adapter.normalize_status("NEW") == "new"
        assert adapter.normalize_status("Open") == "open"

    def test_denormalize_status(self):
        """Test status denormalization."""
        adapter = ZendeskAdapter()
        
        # Common statuses map directly to Zendesk
        assert adapter.denormalize_status("new") == "new"
        assert adapter.denormalize_status("open") == "open"
        assert adapter.denormalize_status("pending") == "pending"
        assert adapter.denormalize_status("hold") == "hold"
        assert adapter.denormalize_status("solved") == "solved"
        assert adapter.denormalize_status("closed") == "closed"

    def test_get_adapter_specific_operations(self):
        """Test getting adapter-specific operations."""
        adapter = ZendeskAdapter()
        operations = adapter.get_adapter_specific_operations()
        
        assert "get_satisfaction_ratings" in operations
        assert "get_ticket_metrics" in operations
        assert "get_organizations" in operations
        assert "search_advanced" in operations
        
        # Test that operations are callable
        assert callable(operations["get_satisfaction_ratings"])
        assert callable(operations["get_ticket_metrics"])

    def test_get_satisfaction_ratings(self):
        """Test getting satisfaction ratings."""
        adapter = ZendeskAdapter()
        mock_client = Mock()
        mock_client._make_request.return_value = {
            "satisfaction_rating": {"score": "good", "comment": "Great service"}
        }
        
        result = adapter._get_satisfaction_ratings(mock_client, "12345")
        
        assert result["score"] == "good"
        assert result["comment"] == "Great service"
        mock_client._make_request.assert_called_once_with("GET", "tickets/12345/satisfaction_rating.json")

    def test_get_satisfaction_ratings_error(self):
        """Test getting satisfaction ratings with error."""
        adapter = ZendeskAdapter()
        mock_client = Mock()
        mock_client._make_request.side_effect = Exception("API Error")
        
        result = adapter._get_satisfaction_ratings(mock_client, "12345")
        
        assert result == {}

    def test_get_ticket_metrics(self):
        """Test getting ticket metrics."""
        adapter = ZendeskAdapter()
        mock_client = Mock()
        mock_client._make_request.return_value = {
            "ticket_metric": {"reply_time_in_minutes": {"business": 120}}
        }
        
        result = adapter._get_ticket_metrics(mock_client, "12345")
        
        assert "reply_time_in_minutes" in result
        mock_client._make_request.assert_called_once_with("GET", "tickets/12345/metrics.json")

    def test_get_organizations(self):
        """Test getting organizations."""
        adapter = ZendeskAdapter()
        mock_client = Mock()
        mock_client._make_request.return_value = {
            "organizations": [{"id": 123, "name": "Test Org"}]
        }
        
        result = adapter._get_organizations(mock_client)
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Org"
        mock_client._make_request.assert_called_once_with("GET", "organizations.json")

    def test_search_advanced(self):
        """Test advanced search functionality."""
        adapter = ZendeskAdapter()
        mock_client = Mock()
        mock_client._make_request.return_value = {
            "results": [{"id": 123, "subject": "Test ticket"}]
        }
        
        result = adapter._search_advanced(mock_client, "test query", "created_at", "desc")
        
        assert len(result) == 1
        assert result[0]["subject"] == "Test ticket"
        mock_client._make_request.assert_called_once_with(
            "GET", 
            "search.json", 
            params={"query": "test query", "sort_by": "created_at", "sort_order": "desc"}
        )