"""Test Zendesk model mappers."""

import pytest
from datetime import datetime

from src.ticketq_zendesk.models import (
    ZendeskTicketMapper,
    ZendeskUserMapper,
    ZendeskGroupMapper,
    parse_zendesk_datetime
)
from ticketq.models import Ticket, User, Group


class TestZendeskDateTimeParsing:
    """Test Zendesk datetime parsing utilities."""

    def test_parse_zendesk_datetime_with_z(self):
        """Test parsing datetime with Z suffix."""
        dt_str = "2024-01-01T10:00:00Z"
        result = parse_zendesk_datetime(dt_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 10

    def test_parse_zendesk_datetime_iso_format(self):
        """Test parsing standard ISO format."""
        dt_str = "2024-01-01T10:00:00+00:00"
        result = parse_zendesk_datetime(dt_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_zendesk_datetime_fallback(self):
        """Test parsing with fallback format."""
        dt_str = "2024-01-01T10:00:00"
        result = parse_zendesk_datetime(dt_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_zendesk_datetime_invalid(self):
        """Test parsing invalid datetime."""
        dt_str = "invalid-datetime"
        result = parse_zendesk_datetime(dt_str)
        
        # Should return current time as fallback
        assert isinstance(result, datetime)


class TestZendeskTicketMapper:
    """Test Zendesk ticket mapping functionality."""

    def test_to_generic_full_ticket(self):
        """Test mapping full Zendesk ticket data."""
        zendesk_data = {
            "id": 12345,
            "subject": "Test ticket",
            "description": "This is a test ticket",
            "status": "open",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-02T15:30:00Z",
            "assignee_id": 123,
            "group_id": 456,
            "url": "https://company.zendesk.com/tickets/12345",
            "priority": "normal",
            "type": "question",
            "tags": ["test", "cli"],
            "external_id": "ext123",
            "via": {"channel": "web"},
            "custom_fields": [{"id": 1, "value": "custom"}],
            "satisfaction_rating": {"score": "good"},
            "sharing_agreement_ids": [789],
            "followup_ids": [111],
            "forum_topic_id": 222,
            "problem_id": 333,
            "has_incidents": False,
            "due_at": "2024-01-10T10:00:00Z",
            "brand_id": 444,
            "allow_channelback": False,
            "allow_attachments": True
        }
        
        mapper = ZendeskTicketMapper()
        ticket = mapper.to_generic(zendesk_data)
        
        assert isinstance(ticket, Ticket)
        assert ticket.id == "12345"
        assert ticket.title == "Test ticket"
        assert ticket.description == "This is a test ticket"
        assert ticket.status == "open"
        assert ticket.assignee_id == "123"
        assert ticket.group_id == "456"
        assert ticket.url == "https://company.zendesk.com/tickets/12345"
        assert ticket.adapter_name == "zendesk"
        
        # Check adapter-specific data
        assert ticket.get_adapter_field("priority") == "normal"
        assert ticket.get_adapter_field("type") == "question"
        assert ticket.get_adapter_field("tags") == ["test", "cli"]
        assert ticket.get_adapter_field("external_id") == "ext123"
        assert ticket.get_adapter_field("has_incidents") is False

    def test_to_generic_minimal_ticket(self):
        """Test mapping minimal Zendesk ticket data."""
        zendesk_data = {
            "id": 1,
            "subject": "Minimal ticket",
            "description": "Minimal description",
            "status": "new",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "url": "https://company.zendesk.com/tickets/1"
        }
        
        mapper = ZendeskTicketMapper()
        ticket = mapper.to_generic(zendesk_data)
        
        assert isinstance(ticket, Ticket)
        assert ticket.id == "1"
        assert ticket.assignee_id is None
        assert ticket.group_id is None
        assert ticket.get_adapter_field("priority") is None

    def test_normalize_status(self):
        """Test status normalization."""
        mapper = ZendeskTicketMapper()
        
        assert mapper._normalize_status("new") == "new"
        assert mapper._normalize_status("open") == "open"
        assert mapper._normalize_status("pending") == "pending"
        assert mapper._normalize_status("hold") == "hold"
        assert mapper._normalize_status("solved") == "solved"
        assert mapper._normalize_status("closed") == "closed"
        
        # Case handling
        assert mapper._normalize_status("NEW") == "new"
        assert mapper._normalize_status("Open") == "open"
        
        # Unknown status
        assert mapper._normalize_status("unknown") == "unknown"


class TestZendeskUserMapper:
    """Test Zendesk user mapping functionality."""

    def test_to_generic_full_user(self):
        """Test mapping full Zendesk user data."""
        zendesk_data = {
            "id": 123,
            "name": "John Doe",
            "email": "john.doe@company.com",
            "group_ids": [456, 789],
            "active": True,
            "verified": True,
            "shared": False,
            "locale": "en-US",
            "locale_id": 1,
            "time_zone": "Pacific Time (US & Canada)",
            "last_login_at": "2024-01-01T10:00:00Z",
            "phone": "+1-555-1234",
            "shared_phone_number": False,
            "photo": {"url": "https://example.com/photo.jpg"},
            "role": "agent",
            "role_type": 1,
            "custom_role_id": 2,
            "moderator": False,
            "ticket_restriction": "assigned",
            "only_private_comments": False,
            "restricted_agent": True,
            "suspended": False,
            "chat_only": False,
            "shared_agent": False,
            "signature": "Best regards, John",
            "details": "Details about John",
            "notes": "Notes about John",
            "organization_id": 111,
            "default_group_id": 456,
            "alias": "jdoe",
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "url": "https://company.zendesk.com/users/123",
            "user_fields": {"custom_field": "value"}
        }
        
        mapper = ZendeskUserMapper()
        user = mapper.to_generic(zendesk_data)
        
        assert isinstance(user, User)
        assert user.id == "123"
        assert user.name == "John Doe"
        assert user.email == "john.doe@company.com"
        assert user.group_ids == ["456", "789"]
        assert user.adapter_name == "zendesk"
        
        # Check adapter-specific data
        assert user.get_adapter_field("active") is True
        assert user.get_adapter_field("role") == "agent"
        assert user.get_adapter_field("time_zone") == "Pacific Time (US & Canada)"
        assert user.get_adapter_field("phone") == "+1-555-1234"

    def test_to_generic_minimal_user(self):
        """Test mapping minimal Zendesk user data."""
        zendesk_data = {
            "id": 1,
            "name": "Jane Doe",
            "email": "jane@company.com",
            "group_ids": []
        }
        
        mapper = ZendeskUserMapper()
        user = mapper.to_generic(zendesk_data)
        
        assert isinstance(user, User)
        assert user.id == "1"
        assert user.name == "Jane Doe"
        assert user.email == "jane@company.com"
        assert user.group_ids == []

    def test_to_generic_null_group_ids(self):
        """Test mapping user with null group IDs."""
        zendesk_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@company.com",
            "group_ids": [None, 456, None, 789]  # Contains null values
        }
        
        mapper = ZendeskUserMapper()
        user = mapper.to_generic(zendesk_data)
        
        # Should filter out null values
        assert user.group_ids == ["456", "789"]


class TestZendeskGroupMapper:
    """Test Zendesk group mapping functionality."""

    def test_to_generic_full_group(self):
        """Test mapping full Zendesk group data."""
        zendesk_data = {
            "id": 456,
            "name": "Support Team",
            "description": "Main support team for customer inquiries",
            "default": False,
            "deleted": False,
            "created_at": "2023-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "url": "https://company.zendesk.com/groups/456"
        }
        
        mapper = ZendeskGroupMapper()
        group = mapper.to_generic(zendesk_data)
        
        assert isinstance(group, Group)
        assert group.id == "456"
        assert group.name == "Support Team"
        assert group.description == "Main support team for customer inquiries"
        assert group.adapter_name == "zendesk"
        
        # Check adapter-specific data
        assert group.get_adapter_field("default") is False
        assert group.get_adapter_field("deleted") is False
        assert group.get_adapter_field("url") == "https://company.zendesk.com/groups/456"

    def test_to_generic_minimal_group(self):
        """Test mapping minimal Zendesk group data."""
        zendesk_data = {
            "id": 1,
            "name": "Test Group",
            "description": None
        }
        
        mapper = ZendeskGroupMapper()
        group = mapper.to_generic(zendesk_data)
        
        assert isinstance(group, Group)
        assert group.id == "1"
        assert group.name == "Test Group"
        assert group.description is None

    def test_to_generic_empty_description(self):
        """Test mapping group with empty description."""
        zendesk_data = {
            "id": 1,
            "name": "Test Group",
            "description": ""
        }
        
        mapper = ZendeskGroupMapper()
        group = mapper.to_generic(zendesk_data)
        
        assert group.description == ""