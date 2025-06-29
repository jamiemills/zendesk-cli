"""Test helper utilities for creating robust mocks."""

from unittest.mock import Mock
from typing import List, Optional


def create_mock_adapter(name="zendesk", features=None):
    """Create a properly configured mock adapter for testing."""
    if features is None:
        features = ["tickets", "users", "groups", "authentication"]
    
    from ticketq.core.interfaces.adapter import BaseAdapter
    
    mock_adapter = Mock(spec=BaseAdapter)
    mock_adapter.name = name
    mock_adapter.display_name = name.title()
    mock_adapter.version = "0.1.0"
    mock_adapter.supported_features = features
    
    # Create mock client with realistic return values
    mock_client = create_mock_client()
    mock_auth = create_mock_auth()
    
    # Add properties that TicketQLibrary expects
    mock_adapter.auth = mock_auth
    mock_adapter.client = mock_client
    mock_adapter._auth = mock_auth  # Backward compatibility
    mock_adapter._client = mock_client  # Backward compatibility
    
    return mock_adapter


def create_mock_client():
    """Create a mock client with realistic return values."""
    mock_client = Mock()
    
    # Mock client methods return lists/objects, not Mocks
    mock_client.get_tickets.return_value = []
    mock_client.get_ticket.return_value = None
    mock_client.get_current_user.return_value = None
    mock_client.get_user.return_value = None
    mock_client.get_groups.return_value = []
    mock_client.get_group.return_value = None
    mock_client.search_tickets.return_value = []
    
    return mock_client


def create_mock_auth():
    """Create a mock auth with proper authentication behavior."""
    mock_auth = Mock()
    mock_auth.authenticate.return_value = True
    mock_auth.get_auth_headers.return_value = {"Authorization": "Bearer test"}
    return mock_auth


def create_sample_tickets(count=1):
    """Create sample ticket objects for testing."""
    from ticketq.models.ticket import Ticket
    from datetime import datetime
    
    tickets = []
    for i in range(count):
        ticket = Ticket(
            id=str(123 + i),
            title=f"Test ticket {i+1}",
            description=f"Test description {i+1}",
            status="open",
            assignee_id="user@example.com",
            group_id="456",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            url=f"https://test.zendesk.com/tickets/{123+i}",
            adapter_name="zendesk"
        )
        tickets.append(ticket)
    
    return tickets if count > 1 else tickets[0]


def create_sample_users(count=1):
    """Create sample user objects for testing."""
    from ticketq.models.user import User
    
    users = []
    for i in range(count):
        user = User(
            id=str(789 + i),
            name=f"Test User {i+1}",
            email=f"test{i+1}@example.com",
            group_ids=["456"],
            adapter_name="zendesk"
        )
        users.append(user)
    
    return users if count > 1 else users[0]


def create_sample_groups(count=1):
    """Create sample group objects for testing."""
    from ticketq.models.group import Group
    
    groups = []
    for i in range(count):
        group = Group(
            id=str(456 + i),
            name=f"Support Team {i+1}",
            description=f"Main support team {i+1}",
            adapter_name="zendesk"
        )
        groups.append(group)
    
    return groups if count > 1 else groups[0]