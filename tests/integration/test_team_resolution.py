"""Integration tests for team name resolution functionality."""

import pytest
from unittest.mock import patch, Mock
from typing import Dict, Any, List

from zendesk_cli.services.zendesk_client import ZendeskClient
from zendesk_cli.services.ticket_service import TicketService


class TestTeamNameResolution:
    """Integration tests for resolving group IDs to team names."""
    
    @pytest.fixture
    def client(self) -> ZendeskClient:
        """Create a test client."""
        return ZendeskClient(
            domain="test.zendesk.com",
            email="test@example.com", 
            api_token="test_token"
        )
    
    @pytest.fixture
    def service(self, client: ZendeskClient) -> TicketService:
        """Create a ticket service."""
        return TicketService(client)
    
    @pytest.fixture
    def sample_groups_response(self) -> Dict[str, Any]:
        """Sample groups API response."""
        return {
            "groups": [
                {
                    "id": 456,
                    "name": "Support Team",
                    "description": "Customer support group"
                },
                {
                    "id": 457,
                    "name": "Engineering Team",
                    "description": "Development and engineering"
                },
                {
                    "id": 458,
                    "name": "Product Team",
                    "description": "Product management"
                }
            ]
        }
    
    @pytest.fixture
    def sample_tickets_with_groups(self) -> Dict[str, Any]:
        """Sample tickets with group assignments."""
        return {
            "tickets": [
                {
                    "id": 1,
                    "subject": "Login issue",
                    "description": "User cannot log in",
                    "status": "open",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "assignee_id": 123,
                    "group_id": 456,  # Support Team
                    "url": "https://test.zendesk.com/api/v2/tickets/1.json"
                },
                {
                    "id": 2,
                    "subject": "Performance bug",
                    "description": "Application is slow",
                    "status": "open",
                    "created_at": "2024-01-01T11:00:00Z",
                    "updated_at": "2024-01-01T11:00:00Z",
                    "assignee_id": 124,
                    "group_id": 457,  # Engineering Team
                    "url": "https://test.zendesk.com/api/v2/tickets/2.json"
                },
                {
                    "id": 3,
                    "subject": "Feature request",
                    "description": "Need new dashboard",
                    "status": "new",
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                    "assignee_id": None,
                    "group_id": 458,  # Product Team
                    "url": "https://test.zendesk.com/api/v2/tickets/3.json"
                },
                {
                    "id": 4,
                    "subject": "Unassigned ticket",
                    "description": "No group assigned",
                    "status": "new",
                    "created_at": "2024-01-01T13:00:00Z",
                    "updated_at": "2024-01-01T13:00:00Z",
                    "assignee_id": None,
                    "group_id": None,  # No group
                    "url": "https://test.zendesk.com/api/v2/tickets/4.json"
                }
            ]
        }
    
    def test_group_id_to_name_resolution(
        self, 
        service: TicketService, 
        sample_groups_response: Dict[str, Any],
        sample_tickets_with_groups: Dict[str, Any]
    ) -> None:
        """Test resolving group IDs to team names."""
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = sample_groups_response
                elif 'tickets.json' in url:
                    mock_response.json.return_value = sample_tickets_with_groups
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            # Get tickets with team names
            enriched_tickets = service.get_tickets_with_team_names()
            
            assert len(enriched_tickets) == 4
            
            # Verify team name resolution
            assert enriched_tickets[0]["team_name"] == "Support Team"
            assert enriched_tickets[1]["team_name"] == "Engineering Team"
            assert enriched_tickets[2]["team_name"] == "Product Team"
            assert enriched_tickets[3]["team_name"] == "Unassigned"  # No group
            
            # Verify original ticket data is preserved
            assert enriched_tickets[0]["ticket"].subject == "Login issue"
            assert enriched_tickets[1]["ticket"].subject == "Performance bug"
            assert enriched_tickets[2]["ticket"].subject == "Feature request"
            assert enriched_tickets[3]["ticket"].subject == "Unassigned ticket"
    
    def test_group_caching(
        self,
        service: TicketService,
        sample_groups_response: Dict[str, Any],
        sample_tickets_with_groups: Dict[str, Any]
    ) -> None:
        """Test that group data is cached to avoid multiple API calls."""
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = sample_groups_response
                elif 'tickets.json' in url:
                    mock_response.json.return_value = sample_tickets_with_groups
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            # First call
            enriched_tickets1 = service.get_tickets_with_team_names()
            # Second call 
            enriched_tickets2 = service.get_tickets_with_team_names()
            
            # Verify groups API was only called once (cached)
            groups_calls = [call for call in mock_request.call_args_list if 'groups.json' in str(call)]
            assert len(groups_calls) == 1
            
            # Results should be identical
            assert len(enriched_tickets1) == len(enriched_tickets2)
            assert enriched_tickets1[0]["team_name"] == enriched_tickets2[0]["team_name"]
    
    def test_unknown_group_handling(
        self,
        service: TicketService,
        sample_groups_response: Dict[str, Any]
    ) -> None:
        """Test handling of tickets with unknown group IDs."""
        tickets_with_unknown_group = {
            "tickets": [
                {
                    "id": 1,
                    "subject": "Mystery ticket",
                    "description": "Has unknown group ID",
                    "status": "open",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "assignee_id": 123,
                    "group_id": 999,  # Unknown group ID
                    "url": "https://test.zendesk.com/api/v2/tickets/1.json"
                }
            ]
        }
        
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = sample_groups_response
                elif 'tickets.json' in url:
                    mock_response.json.return_value = tickets_with_unknown_group
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            enriched_tickets = service.get_tickets_with_team_names()
            
            assert len(enriched_tickets) == 1
            assert enriched_tickets[0]["team_name"] == "Unknown Group (999)"
    
    def test_group_api_error_handling(
        self,
        service: TicketService,
        sample_tickets_with_groups: Dict[str, Any]
    ) -> None:
        """Test handling when groups API fails."""
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                
                if 'groups.json' in url:
                    # Groups API fails
                    mock_response.ok = False
                    mock_response.status_code = 500
                    mock_response.reason = "Internal Server Error"
                elif 'tickets.json' in url:
                    # Tickets API succeeds
                    mock_response.ok = True
                    mock_response.status_code = 200
                    mock_response.json.return_value = sample_tickets_with_groups
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            enriched_tickets = service.get_tickets_with_team_names()
            
            # Should still return tickets, but with fallback group names
            assert len(enriched_tickets) == 4
            assert enriched_tickets[0]["team_name"] == "Group 456"
            assert enriched_tickets[1]["team_name"] == "Group 457"
            assert enriched_tickets[2]["team_name"] == "Group 458"
            assert enriched_tickets[3]["team_name"] == "Unassigned"
    
    def test_filter_by_group_name(
        self,
        service: TicketService,
        sample_groups_response: Dict[str, Any],
        sample_tickets_with_groups: Dict[str, Any]
    ) -> None:
        """Test filtering tickets by group name instead of ID."""
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = sample_groups_response
                elif 'search.json' in url:
                    # Filter for Engineering Team (group_id 457)
                    filtered_tickets = {
                        "results": [ticket for ticket in sample_tickets_with_groups["tickets"] 
                                   if ticket["group_id"] == 457]
                    }
                    mock_response.json.return_value = filtered_tickets
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            # Filter by team name
            enriched_tickets = service.get_tickets_for_group_name("Engineering Team")
            
            assert len(enriched_tickets) == 1
            assert enriched_tickets[0]["team_name"] == "Engineering Team"
            assert enriched_tickets[0]["ticket"].subject == "Performance bug"
            
            # Verify search was called with correct group ID
            search_calls = [call for call in mock_request.call_args_list if 'search.json' in str(call)]
            assert len(search_calls) == 1
            search_params = search_calls[0][1]['params']
            assert 'group:457' in search_params['query']
    
    def test_invalid_group_name_filter(
        self,
        service: TicketService,
        sample_groups_response: Dict[str, Any]
    ) -> None:
        """Test filtering with invalid group name."""
        with patch('requests.request') as mock_request:
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = sample_groups_response
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            # Try to filter by non-existent team name
            enriched_tickets = service.get_tickets_for_group_name("Non-existent Team")
            
            # Should return empty list
            assert len(enriched_tickets) == 0