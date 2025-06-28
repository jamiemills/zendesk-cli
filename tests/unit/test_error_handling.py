"""Tests for comprehensive error handling."""

import pytest
import time
from unittest.mock import Mock, patch
import requests
import keyring

from zendesk_cli.models.exceptions import (
    ZendeskCliError,
    AuthenticationError,
    APIError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    KeyringError,
    ConfigurationError,
    ValidationError
)
from zendesk_cli.services.zendesk_client import ZendeskClient
from zendesk_cli.utils.config import ZendeskConfig


class TestExceptionHierarchy:
    """Test the custom exception hierarchy."""
    
    def test_base_exception_with_suggestions(self) -> None:
        """Test base exception with suggestions."""
        error = ZendeskCliError(
            "Something went wrong",
            details={"code": 500},
            suggestions=["Try again later", "Check your connection"]
        )
        
        error_str = str(error)
        assert "Something went wrong" in error_str
        assert "Try again later" in error_str
        assert "Check your connection" in error_str
        assert "Suggestions:" in error_str
    
    def test_authentication_error_has_default_suggestions(self) -> None:
        """Test that AuthenticationError has helpful default suggestions."""
        error = AuthenticationError("Invalid API token")
        
        error_str = str(error)
        assert "Invalid API token" in error_str
        assert "Check your API token" in error_str
        assert "zendesk configure" in error_str
    
    def test_api_error_with_status_code_suggestions(self) -> None:
        """Test APIError provides status-specific suggestions."""
        # Test 401 error
        error_401 = APIError("Unauthorized", status_code=401)
        assert error_401.status_code == 401
        assert "authentication credentials" in str(error_401)
        
        # Test 403 error
        error_403 = APIError("Forbidden", status_code=403)
        assert "permission" in str(error_403)
        
        # Test 429 error
        error_429 = APIError("Rate limited", status_code=429)
        assert "Rate limit exceeded" in str(error_429)
    
    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test RateLimitError with retry timing."""
        error = RateLimitError("Too many requests", retry_after=30)
        
        assert error.retry_after == 30
        assert error.status_code == 429
        assert "Wait 30 seconds" in str(error)
    
    def test_timeout_error_with_duration(self) -> None:
        """Test TimeoutError includes timeout duration."""
        error = TimeoutError("Request timed out", timeout_duration=30.0)
        
        assert error.details["timeout_duration"] == 30.0
        assert "connection speed" in str(error)
    
    def test_keyring_error_suggestions(self) -> None:
        """Test KeyringError provides platform-specific suggestions."""
        error = KeyringError("Keyring service unavailable")
        
        error_str = str(error)
        assert "keyring service" in error_str
        assert "python3-keyring" in error_str
    
    def test_network_error_with_retry_suggestions(self) -> None:
        """Test NetworkError provides retry suggestions."""
        error = NetworkError("Connection failed", retry_after=60)
        
        assert error.details["retry_after"] == 60
        assert "internet connection" in str(error)
        assert "Wait 60 seconds" in str(error)


class TestZendeskClientErrorHandling:
    """Test error handling in ZendeskClient."""
    
    @pytest.fixture
    def client(self) -> ZendeskClient:
        """Create test client."""
        return ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
    
    def test_client_initialization_validation(self) -> None:
        """Test client validates required parameters."""
        with pytest.raises(ValueError):
            ZendeskClient("", "test@example.com", "token")
        
        with pytest.raises(ValueError):
            ZendeskClient("domain.com", "", "token")
        
        with pytest.raises(ValueError):
            ZendeskClient("domain.com", "test@example.com", "")
    
    def test_authentication_error_handling(self, client: ZendeskClient) -> None:
        """Test authentication error handling."""
        with patch.object(client._session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.reason = "Unauthorized"
            mock_request.return_value = mock_response
            
            with pytest.raises(AuthenticationError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert "Authentication failed" in str(exc_info.value)
    
    def test_rate_limit_error_with_retry(self, client: ZendeskClient) -> None:
        """Test rate limit handling with retry logic."""
        with patch.object(client._session, 'request') as mock_request, \
             patch('time.sleep') as mock_sleep:
            
            # First call: rate limited
            # Second call: still rate limited  
            # Third call: success
            responses = [
                Mock(status_code=429, headers={'Retry-After': '2'}),
                Mock(status_code=429, headers={'Retry-After': '2'}),
                Mock(status_code=200, json=lambda: {"tickets": []})
            ]
            mock_request.side_effect = responses
            
            result = client._make_request("GET", "tickets.json")
            
            # Should have retried and succeeded
            assert mock_request.call_count == 3
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)  # Retry-After header value
            assert result == {"tickets": []}
    
    def test_rate_limit_error_max_retries_exceeded(self, client: ZendeskClient) -> None:
        """Test rate limit error when max retries exceeded."""
        with patch.object(client._session, 'request') as mock_request, \
             patch('time.sleep'):
            
            # Always return rate limited
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '1'}
            mock_request.return_value = mock_response
            
            with pytest.raises(RateLimitError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert exc_info.value.retry_after == 1
            assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_timeout_error_handling(self, client: ZendeskClient) -> None:
        """Test timeout error handling."""
        with patch.object(client._session, 'request') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
            
            with pytest.raises(TimeoutError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert "timed out" in str(exc_info.value)
            assert exc_info.value.details["timeout_duration"] == client._timeout
    
    def test_connection_error_handling(self, client: ZendeskClient) -> None:
        """Test connection error handling."""
        with patch.object(client._session, 'request') as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            with pytest.raises(NetworkError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert "Failed to connect" in str(exc_info.value)
            assert client.domain in str(exc_info.value)
    
    def test_ssl_error_handling(self, client: ZendeskClient) -> None:
        """Test SSL error handling."""
        with patch.object(client._session, 'request') as mock_request:
            mock_request.side_effect = requests.exceptions.SSLError("SSL handshake failed")
            
            with pytest.raises(NetworkError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert "SSL/TLS error" in str(exc_info.value)
    
    def test_invalid_json_response_handling(self, client: ZendeskClient) -> None:
        """Test handling of invalid JSON responses."""
        with patch.object(client._session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.ok = True
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            assert "Invalid JSON response" in str(exc_info.value)
    
    def test_error_response_parsing(self, client: ZendeskClient) -> None:
        """Test parsing of error responses with details."""
        with patch.object(client._session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.reason = "Unprocessable Entity"
            mock_response.ok = False
            mock_response.json.return_value = {
                "error": "Invalid parameters",
                "message": "Validation failed",
                "details": {"field": "assignee_id", "issue": "not found"}
            }
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client._make_request("GET", "tickets.json")
            
            error_str = str(exc_info.value)
            assert "422 Unprocessable Entity" in error_str
            assert "Invalid parameters" in error_str
    
    def test_retry_after_header_parsing(self, client: ZendeskClient) -> None:
        """Test parsing of Retry-After header."""
        # Test valid integer
        mock_response = Mock()
        mock_response.headers = {'Retry-After': '30'}
        assert client._parse_retry_after(mock_response) == 30
        
        # Test invalid value
        mock_response.headers = {'Retry-After': 'invalid'}
        assert client._parse_retry_after(mock_response) is None
        
        # Test missing header
        mock_response.headers = {}
        assert client._parse_retry_after(mock_response) is None


class TestConfigurationErrorHandling:
    """Test error handling in configuration management."""
    
    def test_keyring_error_on_save(self) -> None:
        """Test keyring error when saving configuration."""
        config = ZendeskConfig(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        with patch('keyring.set_password', side_effect=Exception("Keyring unavailable")):
            with pytest.raises(KeyringError) as exc_info:
                config.save_to_file()
            
            assert "Failed to save API token" in str(exc_info.value)
            assert "keyring service" in str(exc_info.value)
    
    def test_keyring_error_on_load(self) -> None:
        """Test keyring error when loading configuration."""
        import tempfile
        import json
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "domain": "test.zendesk.com",
                "email": "test@example.com"
            }
            json.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            with patch('keyring.get_password', side_effect=Exception("Keyring unavailable")):
                with pytest.raises(KeyringError) as exc_info:
                    ZendeskConfig.from_file(config_path)
                
                assert "Failed to retrieve API token" in str(exc_info.value)
        finally:
            config_path.unlink()
    
    def test_file_permission_error_on_save(self) -> None:
        """Test file permission error when saving configuration."""
        config = ZendeskConfig(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        with patch('keyring.set_password'), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            
            with pytest.raises(ConfigurationError) as exc_info:
                config.save_to_file()
            
            assert "Failed to write configuration file" in str(exc_info.value)
    
    def test_email_validation_error(self) -> None:
        """Test email validation in configuration."""
        with pytest.raises(ValueError, match="Email must be a valid email address"):
            ZendeskConfig(
                domain="test.zendesk.com",
                email="invalid-email",
                api_token="test_token"
            )
    
    def test_api_token_validation_error(self) -> None:
        """Test API token validation in configuration."""
        with pytest.raises(ValueError, match="API token appears to be too short"):
            ZendeskConfig(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="short"
            )


class TestErrorRecoveryMechanisms:
    """Test error recovery and resilience mechanisms."""
    
    def test_group_lookup_fallback_on_api_error(self) -> None:
        """Test that group lookup gracefully falls back when API fails."""
        from zendesk_cli.services.ticket_service import TicketService
        
        # Create mock client that fails on groups.json
        mock_client = Mock()
        mock_client._make_request.side_effect = APIError("Server error", status_code=500)
        
        service = TicketService(mock_client)
        
        # Should not raise exception, should return empty dict
        groups_mapping = service._get_groups_mapping()
        assert groups_mapping == {}
        
        # Team name should use fallback
        team_name = service._get_team_name(123)
        assert team_name == "Group 123"
    
    def test_retry_mechanism_with_exponential_backoff(self) -> None:
        """Test retry mechanism respects exponential backoff."""
        client = ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        with patch.object(client._session, 'request') as mock_request, \
             patch('time.sleep') as mock_sleep:
            
            # Simulate transient failures followed by success
            responses = [
                Mock(status_code=429, headers={}),  # No Retry-After header
                Mock(status_code=429, headers={}),
                Mock(status_code=200, json=lambda: {"success": True})
            ]
            mock_request.side_effect = responses
            
            result = client._make_request("GET", "test.json")
            
            # Verify exponential backoff: 2^1=2, 2^2=4 seconds
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(2)  # First retry
            mock_sleep.assert_any_call(4)  # Second retry
            assert result == {"success": True}


class TestErrorContextAndDebugging:
    """Test error context preservation for debugging."""
    
    def test_exception_chaining_preserved(self) -> None:
        """Test that exception chaining is preserved for debugging."""
        client = ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        with patch.object(client._session, 'request') as mock_request:
            original_error = requests.exceptions.ConnectionError("DNS lookup failed")
            mock_request.side_effect = original_error
            
            with pytest.raises(NetworkError) as exc_info:
                client._make_request("GET", "test.json")
            
            # Verify exception chaining
            assert exc_info.value.__cause__ is original_error
    
    def test_detailed_error_context_in_api_errors(self) -> None:
        """Test that APIError includes detailed context."""
        client = ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="test_token"
        )
        
        with patch.object(client._session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.reason = "Unprocessable Entity"
            mock_response.ok = False
            mock_response.json.return_value = {
                "error": "Validation failed",
                "details": {"field": "assignee_id", "code": "not_found"}
            }
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client._make_request("GET", "test.json")
            
            error = exc_info.value
            assert error.status_code == 422
            assert "Validation failed" in str(error)
            assert error.details["response"]["details"]["field"] == "assignee_id"