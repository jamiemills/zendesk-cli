"""Tests for domain models."""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError


class TestTicketModel:
    """Test Ticket model validation and behavior."""
    
    def test_ticket_creation_with_valid_data(self, sample_ticket_data: Dict[str, Any]) -> None:
        """Test creating ticket with valid data."""
        from zendesk_cli.models.ticket import Ticket
        
        ticket = Ticket(**sample_ticket_data)
        assert ticket.id == 12345
        assert ticket.subject == "Test ticket"
        assert ticket.status == "open"
        assert ticket.assignee_id == 123
        assert ticket.group_id == 456
    
    def test_ticket_creation_with_minimal_data(self, sample_ticket_data_minimal: Dict[str, Any]) -> None:
        """Test creating ticket with minimal valid data."""
        from zendesk_cli.models.ticket import Ticket
        
        ticket = Ticket(**sample_ticket_data_minimal)
        assert ticket.id == 1
        assert ticket.subject == "Test"
        assert ticket.assignee_id is None
        assert ticket.group_id is None
    
    def test_ticket_validation_fails_with_invalid_status(self) -> None:
        """Test ticket validation fails with invalid status."""
        from zendesk_cli.models.ticket import Ticket
        
        with pytest.raises(ValidationError) as exc_info:
            Ticket(
                id=1,
                subject="Test",
                description="Test description",
                status="invalid_status",  # Invalid status
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                url="https://example.com"
            )
        assert "status" in str(exc_info.value)
    
    def test_ticket_validation_fails_with_empty_subject(self) -> None:
        """Test ticket validation fails with empty subject."""
        from zendesk_cli.models.ticket import Ticket
        
        with pytest.raises(ValidationError) as exc_info:
            Ticket(
                id=1,
                subject="",  # Empty subject
                description="Test description",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                url="https://example.com"
            )
        assert "subject" in str(exc_info.value)
    
    def test_ticket_validation_fails_when_updated_before_created(self) -> None:
        """Test ticket validation fails when updated_at is before created_at."""
        from zendesk_cli.models.ticket import Ticket
        
        with pytest.raises(ValidationError) as exc_info:
            Ticket(
                id=1,
                subject="Test",
                description="Test description",
                status="open",
                created_at="2024-01-02T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",  # Before created_at
                url="https://example.com"
            )
        assert "updated_at must be after created_at" in str(exc_info.value)
    
    @pytest.mark.parametrize("description,expected", [
        ("Short description", "Short description"),
        ("This is a very long description that should be truncated because it exceeds fifty characters", 
         "This is a very long description that should be t..."),
        ("Exactly fifty characters long description test!", "Exactly fifty characters long description test!"),
    ])
    def test_short_description_property(self, description: str, expected: str) -> None:
        """Test short_description property truncation."""
        from zendesk_cli.models.ticket import Ticket
        
        ticket = Ticket(
            id=1,
            subject="Test",
            description=description,
            status="open",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
            url="https://example.com"
        )
        assert ticket.short_description == expected
    
    def test_days_since_created_property(self) -> None:
        """Test days_since_created property calculation."""
        from zendesk_cli.models.ticket import Ticket
        from freezegun import freeze_time
        
        with freeze_time("2024-01-05T10:00:00Z"):
            ticket = Ticket(
                id=1,
                subject="Test",
                description="Test description",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                url="https://example.com"
            )
            assert ticket.days_since_created == 4
    
    def test_days_since_updated_property(self) -> None:
        """Test days_since_updated property calculation."""
        from zendesk_cli.models.ticket import Ticket
        from freezegun import freeze_time
        
        with freeze_time("2024-01-05T10:00:00Z"):
            ticket = Ticket(
                id=1,
                subject="Test",
                description="Test description",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-03T10:00:00Z",
                url="https://example.com"
            )
            assert ticket.days_since_updated == 2


class TestExceptionModels:
    """Test custom exception classes."""
    
    def test_zendesk_cli_error_with_suggestions(self) -> None:
        """Test ZendeskCliError with suggestions."""
        from zendesk_cli.models.exceptions import ZendeskCliError
        
        error = ZendeskCliError(
            "Something went wrong",
            details={"code": 500},
            suggestions=["Check your network", "Try again later"]
        )
        
        assert "Something went wrong" in str(error)
        assert "Check your network" in str(error)
        assert "Try again later" in str(error)
    
    def test_authentication_error_has_default_suggestions(self) -> None:
        """Test AuthenticationError includes helpful suggestions."""
        from zendesk_cli.models.exceptions import AuthenticationError
        
        error = AuthenticationError("Invalid credentials")
        
        assert "Invalid credentials" in str(error)
        assert "Check your API token" in str(error)
        assert "zendesk configure" in str(error)
    
    def test_api_error_with_status_code(self) -> None:
        """Test APIError with status code context."""
        from zendesk_cli.models.exceptions import APIError
        
        error = APIError("Unauthorized", status_code=401)
        
        assert error.status_code == 401
        assert "Check your authentication" in str(error)