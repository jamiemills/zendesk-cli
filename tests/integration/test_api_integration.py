"""Integration tests for API client with comprehensive error scenarios."""

import pytest
from unittest.mock import patch, Mock
import requests
from typing import Dict, Any

from zendesk_cli.services.zendesk_client import ZendeskClient
from zendesk_cli.models.exceptions import APIError, AuthenticationError


class TestZendeskClientIntegration:
    """Integration tests for ZendeskClient with various API scenarios."""
    
    @pytest.fixture
    def client(self) -> ZendeskClient:
        """Create a test client."""
        return ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com", 
            api_token="test_token"
        )
    
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
                    "url": "https://test.zendesk.com/api/v2/tickets/1.json"
                },
                {
                    "id": 2,
                    "subject": "Test ticket 2",
                    "description": "Second test ticket",
                    "status": "pending",
                    "created_at": "2024-01-02T10:00:00Z",
                    "updated_at": "2024-01-02T10:00:00Z",
                    "assignee_id": 124,
                    "group_id": 457,
                    "url": "https://test.zendesk.com/api/v2/tickets/2.json"
                }
            ]
        }
    
    @pytest.fixture
    def sample_search_response(self) -> Dict[str, Any]:
        """Sample search API response."""
        return {
            "results": [
                {
                    "id": 1,
                    "subject": "Search result ticket",
                    "description": "Found via search",
                    "status": "open",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "assignee_id": 123,
                    "group_id": 456,
                    "url": "https://test.zendesk.com/api/v2/tickets/1.json"
                }
            ]
        }
    
    def test_successful_ticket_retrieval(self, client: ZendeskClient, sample_tickets_response: Dict[str, Any]) -> None:
        """Test successful ticket retrieval."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = sample_tickets_response
            mock_request.return_value = mock_response
            
            tickets = client.get_tickets()
            
            assert len(tickets) == 2
            assert tickets[0].subject == "Test ticket 1"
            assert tickets[1].subject == "Test ticket 2"
            # Verify URL conversion to human-readable format
            assert tickets[0].url == "https://test.zendesk.com/agent/tickets/1"
            assert tickets[1].url == "https://test.zendesk.com/agent/tickets/2"
    
    def test_ticket_search_with_filters(self, client: ZendeskClient, sample_search_response: Dict[str, Any]) -> None:
        """Test ticket search with various filters."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = sample_search_response
            mock_request.return_value = mock_response
            
            # Test search with assignee filter
            tickets = client.get_tickets(assignee_id=123)
            
            assert len(tickets) == 1
            assert tickets[0].subject == "Search result ticket"
            
            # Verify search endpoint was called
            mock_request.assert_called_with(
                method="GET",
                url="https://test.zendesk.com/api/v2/search.json",
                headers=client._get_auth_headers(),
                params={"query": "type:ticket assignee:123"},
                timeout=30.0
            )
    
    def test_search_with_multiple_filters(self, client: ZendeskClient, sample_search_response: Dict[str, Any]) -> None:
        """Test search with multiple filters."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = sample_search_response
            mock_request.return_value = mock_response
            
            tickets = client.get_tickets(assignee_id=123, group_id=456, status="open")
            
            # Verify complex search query
            expected_query = "type:ticket status:open assignee:123 group:456"
            mock_request.assert_called_with(
                method="GET",
                url="https://test.zendesk.com/api/v2/search.json",
                headers=client._get_auth_headers(),
                params={"query": expected_query},
                timeout=30.0
            )
    
    def test_authentication_error_handling(self, client: ZendeskClient) -> None:
        """Test authentication error handling."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.reason = "Unauthorized"
            mock_request.return_value = mock_response
            
            with pytest.raises(AuthenticationError) as exc_info:
                client.get_tickets()
            
            assert "Authentication failed" in str(exc_info.value)
            assert "Check your API token" in str(exc_info.value)
    
    def test_api_error_handling_with_json_response(self, client: ZendeskClient) -> None:
        """Test API error handling with JSON error response."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 422
            mock_response.reason = "Unprocessable Entity"
            mock_response.json.return_value = {
                "error": "Invalid query parameters",
                "details": {"field": "assignee_id"}
            }
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets(assignee_id="invalid")
            
            assert exc_info.value.status_code == 422
            assert "API request failed: 422" in str(exc_info.value)
            assert "Invalid query parameters" in exc_info.value.details["response"]["error"]
    
    def test_api_error_handling_without_json_response(self, client: ZendeskClient) -> None:
        """Test API error handling when response is not JSON."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 500
            mock_response.reason = "Internal Server Error"
            mock_response.json.side_effect = ValueError("Not JSON")
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets()
            
            assert exc_info.value.status_code == 500
            assert "API request failed: 500" in str(exc_info.value)
    
    def test_network_error_handling(self, client: ZendeskClient) -> None:
        """Test network error handling."""
        with patch('requests.request') as mock_request:
            mock_request.side_effect = requests.ConnectionError("Network error")
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets()
            
            assert "Network error" in str(exc_info.value)
    
    def test_timeout_error_handling(self, client: ZendeskClient) -> None:
        """Test timeout error handling."""
        with patch('requests.request') as mock_request:
            mock_request.side_effect = requests.Timeout("Request timeout")
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets()
            
            assert "Request timeout" in str(exc_info.value)
    
    def test_get_current_user_success(self, client: ZendeskClient) -> None:
        """Test successful current user retrieval."""
        user_response = {
            "user": {
                "id": 123,
                "name": "Test User",
                "email": "test@example.com",
                "role": "agent"
            }
        }
        
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = user_response
            mock_request.return_value = mock_response
            
            user = client.get_current_user()
            
            assert user["id"] == 123
            assert user["name"] == "Test User"
            assert user["email"] == "test@example.com"
            
            # Verify correct endpoint was called
            mock_request.assert_called_with(
                method="GET",
                url="https://test.zendesk.com/api/v2/users/me.json",
                headers=client._get_auth_headers(),
                params=None,
                timeout=30.0
            )
    
    def test_auth_headers_generation(self, client: ZendeskClient) -> None:
        """Test authentication headers are properly generated."""
        headers = client._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        
        # Verify credentials encoding
        import base64
        expected_creds = base64.b64encode(
            "test@example.com/token:test_token".encode()
        ).decode()
        assert headers["Authorization"] == f"Basic {expected_creds}"
    
    def test_rate_limit_error_handling(self, client: ZendeskClient) -> None:
        """Test rate limit error handling."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 429
            mock_response.reason = "Too Many Requests"
            mock_response.json.return_value = {"error": "Rate limit exceeded"}
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets()
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value)
    
    def test_forbidden_error_handling(self, client: ZendeskClient) -> None:
        """Test forbidden access error handling."""
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 403
            mock_response.reason = "Forbidden"
            mock_response.json.return_value = {"error": "Access denied"}
            mock_request.return_value = mock_response
            
            with pytest.raises(APIError) as exc_info:
                client.get_tickets()
            
            assert exc_info.value.status_code == 403
            assert "You may not have permission" in str(exc_info.value)