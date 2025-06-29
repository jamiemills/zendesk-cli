"""Shared pytest fixtures for TicketQ tests."""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock

# Import our models for fixtures
from src.ticketq.models import Ticket, User, Group
from src.ticketq.lib.models import LibraryTicket, LibraryUser, LibraryGroup


@pytest.fixture
def sample_ticket_data() -> Dict[str, Any]:
    """Sample ticket data for testing."""
    return {
        "id": 12345,
        "subject": "Test ticket",
        "description": "This is a test ticket for our CLI",
        "status": "open",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-02T15:30:00Z",
        "assignee_id": 123,
        "group_id": 456,
        "url": "https://example.zendesk.com/tickets/12345",
        "priority": "normal",
        "type": "question",
        "tags": ["test", "cli"]
    }


@pytest.fixture
def sample_ticket_data_minimal() -> Dict[str, Any]:
    """Minimal valid ticket data."""
    return {
        "id": 1,
        "subject": "Test",
        "description": "Test description",
        "status": "open",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
        "url": "https://example.com"
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        "id": 123,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "group_ids": [456, 789],
        "active": True,
        "role": "agent"
    }


@pytest.fixture
def sample_group_data() -> Dict[str, Any]:
    """Sample group data for testing."""
    return {
        "id": 456,
        "name": "Support Team",
        "description": "Main support team",
        "default": False,
        "deleted": False
    }


@pytest.fixture
def sample_ticket(sample_ticket_data) -> Ticket:
    """Create a sample Ticket model."""
    return Ticket(
        id=str(sample_ticket_data["id"]),
        title=sample_ticket_data["subject"],
        description=sample_ticket_data["description"],
        status=sample_ticket_data["status"],
        created_at=datetime.fromisoformat(sample_ticket_data["created_at"].replace('Z', '')),
        updated_at=datetime.fromisoformat(sample_ticket_data["updated_at"].replace('Z', '')),
        assignee_id=str(sample_ticket_data["assignee_id"]) if sample_ticket_data.get("assignee_id") else None,
        group_id=str(sample_ticket_data["group_id"]) if sample_ticket_data.get("group_id") else None,
        url=sample_ticket_data["url"],
        adapter_name="test",
        adapter_specific_data={
            "priority": sample_ticket_data.get("priority"),
            "type": sample_ticket_data.get("type"),
            "tags": sample_ticket_data.get("tags", [])
        }
    )


@pytest.fixture
def sample_user(sample_user_data) -> User:
    """Create a sample User model."""
    return User(
        id=str(sample_user_data["id"]),
        name=sample_user_data["name"],
        email=sample_user_data["email"],
        group_ids=[str(gid) for gid in sample_user_data["group_ids"]],
        adapter_name="test",
        adapter_specific_data={
            "active": sample_user_data.get("active"),
            "role": sample_user_data.get("role")
        }
    )


@pytest.fixture
def sample_group(sample_group_data) -> Group:
    """Create a sample Group model."""
    return Group(
        id=str(sample_group_data["id"]),
        name=sample_group_data["name"],
        description=sample_group_data["description"],
        adapter_name="test",
        adapter_specific_data={
            "default": sample_group_data.get("default"),
            "deleted": sample_group_data.get("deleted")
        }
    )


@pytest.fixture
def sample_library_ticket(sample_ticket) -> LibraryTicket:
    """Create a sample LibraryTicket."""
    return LibraryTicket.from_ticket(sample_ticket, team_name="Support Team")


@pytest.fixture
def sample_library_user(sample_user) -> LibraryUser:
    """Create a sample LibraryUser."""
    return LibraryUser.from_user(sample_user)


@pytest.fixture
def sample_library_group(sample_group) -> LibraryGroup:
    """Create a sample LibraryGroup."""
    return LibraryGroup.from_group(sample_group)


@pytest.fixture
def mock_adapter():
    """Create a mock adapter for testing."""
    adapter = Mock()
    adapter.name = "test"
    adapter.display_name = "Test Adapter"
    adapter.version = "1.0.0"
    adapter.supported_features = ["tickets", "users", "groups"]
    
    # Mock client and auth
    adapter._client = Mock()
    adapter._auth = Mock()
    
    # Also provide client and auth properties for new library interface
    adapter.client = adapter._client
    adapter.auth = adapter._auth
    
    return adapter


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Mock configuration data."""
    return {
        "domain": "test.example.com",
        "email": "test@example.com",
        "api_token": "test_token_123"
    }


@pytest.fixture
def zendesk_adapter_config() -> Dict[str, Any]:
    """Zendesk adapter configuration for testing."""
    return {
        "domain": "company.zendesk.com",
        "email": "user@company.com",
        "api_token": "zendesk_token_abc123"
    }


@pytest.fixture
def multiple_tickets(sample_ticket_data) -> list[Dict[str, Any]]:
    """Create multiple ticket data samples for testing."""
    tickets = []
    statuses = ["new", "open", "pending", "hold", "solved", "closed"]
    
    for i, status in enumerate(statuses, 1):
        ticket_data = sample_ticket_data.copy()
        ticket_data["id"] = 12340 + i
        ticket_data["subject"] = f"Test ticket {i}"
        ticket_data["status"] = status
        ticket_data["group_id"] = 456 + (i % 3)  # Vary group IDs
        tickets.append(ticket_data)
    
    return tickets


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response."""
    response = Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.json.return_value = {"success": True}
    return response


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "ticketq_test_config"
    config_dir.mkdir()
    return config_dir