"""Tests for TicketService business logic."""

import pytest
from unittest.mock import Mock, patch
from typing import List

from zendesk_cli.models.ticket import Ticket
from zendesk_cli.models.exceptions import APIError


class TestTicketService:
    """Test TicketService business logic."""
    
    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create a mock ZendeskClient."""
        client = Mock()
        return client
    
    @pytest.fixture
    def sample_tickets(self) -> List[Ticket]:
        """Create sample tickets for testing."""
        return [
            Ticket(
                id=1,
                subject="Bug in login system",
                description="Users cannot log in",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                assignee_id=123,
                group_id=456,
                url="https://example.zendesk.com/tickets/1"
            ),
            Ticket(
                id=2,
                subject="Feature request: Dark mode",
                description="Please add dark mode support",
                status="pending",
                created_at="2024-01-02T10:00:00Z",
                updated_at="2024-01-02T15:00:00Z",
                assignee_id=124,
                group_id=456,
                url="https://example.zendesk.com/tickets/2"
            ),
            Ticket(
                id=3,
                subject="Performance issue",
                description="App is running slowly",
                status="open",
                created_at="2024-01-03T10:00:00Z",
                updated_at="2024-01-03T10:00:00Z",
                assignee_id=123,
                group_id=789,
                url="https://example.zendesk.com/tickets/3"
            )
        ]
    
    def test_ticket_service_initialization(self, mock_client: Mock) -> None:
        """Test TicketService initialization."""
        from zendesk_cli.services.ticket_service import TicketService
        
        service = TicketService(client=mock_client)
        assert service.client == mock_client
    
    def test_get_all_open_tickets(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test getting all open tickets."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_client.get_tickets.return_value = sample_tickets
        service = TicketService(client=mock_client)
        
        tickets = service.get_all_open_tickets()
        
        assert len(tickets) == 3
        mock_client.get_tickets.assert_called_once_with(status="open")
    
    def test_get_user_tickets(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test getting tickets assigned to specific user."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_client.get_tickets.return_value = sample_tickets
        service = TicketService(client=mock_client)
        
        tickets = service.get_user_tickets(user_id=123)
        
        assert len(tickets) == 3  # All tickets returned by mock
        mock_client.get_tickets.assert_called_once_with(assignee_id=123, status="open")
    
    def test_get_group_tickets(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test getting tickets assigned to specific group."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_client.get_tickets.return_value = sample_tickets
        service = TicketService(client=mock_client)
        
        tickets = service.get_group_tickets(group_id=456)
        
        assert len(tickets) == 3
        mock_client.get_tickets.assert_called_once_with(group_id=456, status="open")
    
    def test_get_current_user_info(self, mock_client: Mock) -> None:
        """Test getting current user information."""
        from zendesk_cli.services.ticket_service import TicketService
        
        user_data = {
            "id": 123,
            "name": "Test User",
            "email": "test@example.com",
            "organization_id": 456
        }
        mock_client.get_current_user.return_value = user_data
        service = TicketService(client=mock_client)
        
        result = service.get_current_user_info()
        
        assert result == user_data
        mock_client.get_current_user.assert_called_once()
    
    def test_filter_tickets_by_status(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test filtering tickets by status."""
        from zendesk_cli.services.ticket_service import TicketService
        
        service = TicketService(client=mock_client)
        
        open_tickets = service.filter_tickets_by_status(sample_tickets, "open")
        pending_tickets = service.filter_tickets_by_status(sample_tickets, "pending")
        
        assert len(open_tickets) == 2
        assert len(pending_tickets) == 1
        assert all(t.status == "open" for t in open_tickets)
        assert all(t.status == "pending" for t in pending_tickets)
    
    def test_sort_tickets_by_created_date(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test sorting tickets by creation date."""
        from zendesk_cli.services.ticket_service import TicketService
        
        service = TicketService(client=mock_client)
        
        # Sort newest first
        sorted_tickets = service.sort_tickets_by_created_date(sample_tickets, newest_first=True)
        assert sorted_tickets[0].id == 3  # Created 2024-01-03
        assert sorted_tickets[-1].id == 1  # Created 2024-01-01
        
        # Sort oldest first
        sorted_tickets = service.sort_tickets_by_created_date(sample_tickets, newest_first=False)
        assert sorted_tickets[0].id == 1  # Created 2024-01-01
        assert sorted_tickets[-1].id == 3  # Created 2024-01-03
    
    def test_api_error_handling(self, mock_client: Mock) -> None:
        """Test handling of API errors."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_client.get_tickets.side_effect = APIError("Server error", status_code=500)
        service = TicketService(client=mock_client)
        
        with pytest.raises(APIError) as exc_info:
            service.get_all_open_tickets()
        
        assert exc_info.value.status_code == 500
    
    def test_get_tickets_summary(self, mock_client: Mock, sample_tickets: List[Ticket]) -> None:
        """Test getting summary statistics of tickets."""
        from zendesk_cli.services.ticket_service import TicketService
        
        service = TicketService(client=mock_client)
        
        summary = service.get_tickets_summary(sample_tickets)
        
        expected_summary = {
            "total": 3,
            "by_status": {"open": 2, "pending": 1},
            "by_assignee": {123: 2, 124: 1},
            "by_group": {456: 2, 789: 1}
        }
        
        assert summary == expected_summary