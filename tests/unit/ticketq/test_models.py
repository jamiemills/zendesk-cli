"""Test TicketQ core models."""

import pytest
from datetime import datetime
from freezegun import freeze_time

from src.ticketq.models import Ticket, User, Group


class TestTicket:
    """Test Ticket model functionality."""

    def test_ticket_creation(self, sample_ticket_data):
        """Test basic ticket creation."""
        ticket = Ticket(
            id=str(sample_ticket_data["id"]),
            title=sample_ticket_data["subject"],
            description=sample_ticket_data["description"],
            status=sample_ticket_data["status"],
            created_at=datetime.fromisoformat(sample_ticket_data["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(sample_ticket_data["updated_at"].replace('Z', '+00:00')),
            assignee_id=str(sample_ticket_data["assignee_id"]),
            group_id=str(sample_ticket_data["group_id"]),
            url=sample_ticket_data["url"],
            adapter_name="test"
        )
        
        assert ticket.id == "12345"
        assert ticket.title == "Test ticket"
        assert ticket.description == "This is a test ticket for our CLI"
        assert ticket.status == "open"
        assert ticket.adapter_name == "test"

    def test_ticket_creation_minimal(self, sample_ticket_data_minimal):
        """Test ticket creation with minimal required fields."""
        ticket = Ticket(
            id=str(sample_ticket_data_minimal["id"]),
            title=sample_ticket_data_minimal["subject"],
            description=sample_ticket_data_minimal["description"],
            status=sample_ticket_data_minimal["status"],
            created_at=datetime.fromisoformat(sample_ticket_data_minimal["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(sample_ticket_data_minimal["updated_at"].replace('Z', '+00:00')),
            url=sample_ticket_data_minimal["url"],
            adapter_name="test"
        )
        
        assert ticket.id == "1"
        assert ticket.assignee_id is None
        assert ticket.group_id is None

    @freeze_time("2024-01-10T00:00:00Z")
    def test_ticket_computed_properties(self, sample_ticket):
        """Test computed properties like days_since_created."""
        # Ticket created on 2024-01-01T10:00:00, frozen time is 2024-01-10T00:00:00
        assert sample_ticket.days_since_created == 8  # 8 days difference
        assert sample_ticket.days_since_updated == 7  # Updated on 2024-01-02T15:30:00

    def test_ticket_short_description(self):
        """Test short description property."""
        long_description = "A" * 100
        ticket = Ticket(
            id="1",
            title="Test",
            description=long_description,
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            url="https://example.com",
            adapter_name="test"
        )
        
        assert len(ticket.short_description) == 53  # 50 chars + "..."
        assert ticket.short_description.endswith("...")

    def test_ticket_adapter_specific_data(self, sample_ticket):
        """Test adapter-specific data handling."""
        sample_ticket.set_adapter_field("priority", "high")
        sample_ticket.set_adapter_field("custom_field", "value")
        
        assert sample_ticket.get_adapter_field("priority") == "high"
        assert sample_ticket.get_adapter_field("custom_field") == "value"
        assert sample_ticket.get_adapter_field("nonexistent") is None
        assert sample_ticket.get_adapter_field("nonexistent", "default") == "default"

    def test_ticket_with_empty_id(self):
        """Test ticket creation with empty ID."""
        # Currently no validation, so this should work
        ticket = Ticket(
            id="",  # Empty ID
            title="Test",
            description="Test",
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            url="https://example.com",
            adapter_name="test"
        )
        
        assert ticket.id == ""

    def test_ticket_dict_conversion(self, sample_ticket):
        """Test dictionary conversion."""
        ticket_dict = sample_ticket.to_dict()
        
        assert ticket_dict["id"] == sample_ticket.id
        assert ticket_dict["title"] == sample_ticket.title
        assert ticket_dict["adapter_name"] == sample_ticket.adapter_name
        assert "days_since_created" in ticket_dict
        assert "days_since_updated" in ticket_dict


class TestUser:
    """Test User model functionality."""

    def test_user_creation(self, sample_user_data):
        """Test basic user creation."""
        user = User(
            id=str(sample_user_data["id"]),
            name=sample_user_data["name"],
            email=sample_user_data["email"],
            group_ids=[str(gid) for gid in sample_user_data["group_ids"]],
            adapter_name="test"
        )
        
        assert user.id == "123"
        assert user.name == "John Doe"
        assert user.email == "john.doe@example.com"
        assert user.group_ids == ["456", "789"]

    def test_user_adapter_specific_data(self, sample_user):
        """Test user adapter-specific data."""
        sample_user.set_adapter_field("role", "admin")
        sample_user.set_adapter_field("permissions", ["read", "write"])
        
        assert sample_user.get_adapter_field("role") == "admin"
        assert sample_user.get_adapter_field("permissions") == ["read", "write"]

    def test_user_with_empty_name(self):
        """Test user creation with empty name."""
        # Currently no validation, so this should work
        user = User(
            id="123",
            name="",  # Empty name
            email="test@example.com",
            group_ids=[],
            adapter_name="test"
        )
        
        assert user.name == ""

    def test_user_dict_conversion(self, sample_user):
        """Test user dictionary conversion."""
        user_dict = sample_user.to_dict()
        
        assert user_dict["id"] == sample_user.id
        assert user_dict["name"] == sample_user.name
        assert user_dict["email"] == sample_user.email
        assert user_dict["group_ids"] == sample_user.group_ids


class TestGroup:
    """Test Group model functionality."""

    def test_group_creation(self, sample_group_data):
        """Test basic group creation."""
        group = Group(
            id=str(sample_group_data["id"]),
            name=sample_group_data["name"],
            description=sample_group_data["description"],
            adapter_name="test"
        )
        
        assert group.id == "456"
        assert group.name == "Support Team"
        assert group.description == "Main support team"

    def test_group_adapter_specific_data(self, sample_group):
        """Test group adapter-specific data."""
        sample_group.set_adapter_field("default", True)
        sample_group.set_adapter_field("sla_policy", "24h")
        
        assert sample_group.get_adapter_field("default") is True
        assert sample_group.get_adapter_field("sla_policy") == "24h"

    def test_group_with_empty_fields(self):
        """Test group creation with empty fields."""
        # Currently no validation, so this should work
        group = Group(
            id="",  # Empty ID
            name="",  # Empty name
            description="Test description",
            adapter_name="test"
        )
        
        assert group.id == ""
        assert group.name == ""

    def test_group_dict_conversion(self, sample_group):
        """Test group dictionary conversion."""
        group_dict = sample_group.to_dict()
        
        assert group_dict["id"] == sample_group.id
        assert group_dict["name"] == sample_group.name
        assert group_dict["description"] == sample_group.description