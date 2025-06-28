"""Shared pytest fixtures for zendesk-cli tests."""

import pytest
from datetime import datetime
from typing import Dict, Any


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
        "url": "https://example.zendesk.com/tickets/12345"
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