"""Tests for ZendeskClient HTTP operations."""

import pytest
import responses
from typing import Dict, Any
from unittest.mock import Mock

from zendesk_cli.models.exceptions import APIError, AuthenticationError


class TestZendeskClient:
    """Test ZendeskClient HTTP operations with mocked responses."""
    
    @pytest.fixture
    def client_config(self) -> Dict[str, str]:
        """Sample client configuration."""
        return {
            "domain": "example.zendesk.com",
            "email": "test@example.com",
            "api_token": "test_token"
        }
    
    @pytest.fixture
    def sample_tickets_response(self) -> Dict[str, Any]:
        """Sample tickets API response."""
        return {
            "tickets": [
                {
                    "id": 1,
                    "subject": "Test ticket 1",
                    "description": "First test ticket",
                    "status": "open",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "assignee_id": 123,
                    "group_id": 456,
                    "url": "https://example.zendesk.com/tickets/1"
                },
                {
                    "id": 2,
                    "subject": "Test ticket 2",
                    "description": "Second test ticket",
                    "status": "pending",
                    "created_at": "2024-01-02T10:00:00Z",
                    "updated_at": "2024-01-02T15:00:00Z",
                    "assignee_id": 124,
                    "group_id": 456,
                    "url": "https://example.zendesk.com/tickets/2"
                }
            ],
            "next_page": None,
            "previous_page": None,
            "count": 2
        }
    
    def test_client_initialization(self, client_config: Dict[str, str]) -> None:
        """Test ZendeskClient initialization with valid config."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        client = ZendeskClient(**client_config)
        
        assert client.domain == "example.zendesk.com"
        assert client.email == "test@example.com"
    
    def test_client_base_url_property(self, client_config: Dict[str, str]) -> None:
        """Test base_url property formatting."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        client = ZendeskClient(**client_config)
        
        assert client.base_url == "https://example.zendesk.com/api/v2"
    
    @responses.activate
    def test_get_tickets_success(
        self, 
        client_config: Dict[str, str], 
        sample_tickets_response: Dict[str, Any]
    ) -> None:
        """Test successful tickets retrieval."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            json=sample_tickets_response,
            status=200
        )
        
        client = ZendeskClient(**client_config)
        tickets = client.get_tickets()
        
        assert len(tickets) == 2
        assert tickets[0].id == 1
        assert tickets[0].subject == "Test ticket 1"
        assert tickets[1].id == 2
        assert tickets[1].status == "pending"
    
    @responses.activate
    def test_get_tickets_with_filters(
        self, 
        client_config: Dict[str, str], 
        sample_tickets_response: Dict[str, Any]
    ) -> None:
        """Test tickets retrieval with query parameters."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            json=sample_tickets_response,
            status=200
        )
        
        client = ZendeskClient(**client_config)
        tickets = client.get_tickets(assignee_id=123, status="open")
        
        # Verify the request was made with correct parameters
        assert len(responses.calls) == 1
        request = responses.calls[0].request
        assert "assignee_id=123" in request.url
        assert "status=open" in request.url
    
    @responses.activate
    def test_authentication_error_401(self, client_config: Dict[str, str]) -> None:
        """Test handling of 401 authentication errors."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            json={"error": "Unauthorized"},
            status=401
        )
        
        client = ZendeskClient(**client_config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.get_tickets()
        
        assert "authentication failed" in str(exc_info.value).lower()
    
    @responses.activate
    def test_api_error_500(self, client_config: Dict[str, str]) -> None:
        """Test handling of 500 server errors."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            json={"error": "Internal server error"},
            status=500
        )
        
        client = ZendeskClient(**client_config)
        
        with pytest.raises(APIError) as exc_info:
            client.get_tickets()
        
        assert exc_info.value.status_code == 500
    
    @responses.activate
    def test_api_error_429_rate_limit(self, client_config: Dict[str, str]) -> None:
        """Test handling of 429 rate limit errors."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            json={"error": "Rate limit exceeded"},
            status=429
        )
        
        client = ZendeskClient(**client_config)
        
        with pytest.raises(APIError) as exc_info:
            client.get_tickets()
        
        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value).lower()
    
    @responses.activate
    def test_get_current_user_success(self, client_config: Dict[str, str]) -> None:
        """Test successful current user retrieval."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        
        user_response = {
            "user": {
                "id": 123,
                "name": "Test User",
                "email": "test@example.com",
                "organization_id": 456
            }
        }
        
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/users/me.json",
            json=user_response,
            status=200
        )
        
        client = ZendeskClient(**client_config)
        user_data = client.get_current_user()
        
        assert user_data["id"] == 123
        assert user_data["name"] == "Test User"
        assert user_data["email"] == "test@example.com"
    
    def test_authentication_header_format(self, client_config: Dict[str, str]) -> None:
        """Test that authentication header is correctly formatted."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        import base64
        
        client = ZendeskClient(**client_config)
        auth_headers = client._get_auth_headers()
        
        # Verify Authorization header exists
        assert "Authorization" in auth_headers
        
        # Verify it's Basic auth
        auth_value = auth_headers["Authorization"]
        assert auth_value.startswith("Basic ")
        
        # Verify the encoded credentials
        encoded_creds = auth_value[6:]  # Remove "Basic "
        decoded_creds = base64.b64decode(encoded_creds).decode('utf-8')
        expected_creds = f"{client_config['email']}/token:{client_config['api_token']}"
        assert decoded_creds == expected_creds
    
    def test_request_timeout_configuration(self, client_config: Dict[str, str]) -> None:
        """Test that requests have appropriate timeout configuration."""
        from zendesk_cli.services.zendesk_client import ZendeskClient
        from unittest.mock import patch
        
        client = ZendeskClient(**client_config)
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"tickets": []}
            
            client.get_tickets()
            
            # Verify timeout was set
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] > 0