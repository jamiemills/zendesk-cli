"""Unit tests for the library API."""

import csv
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from zendesk_cli import ZendeskLibrary, LibraryTicket, ConfigurationError, ZendeskCliError
from zendesk_cli.models.ticket import Ticket


class TestLibraryTicket:
    """Test the LibraryTicket model."""
    
    def test_from_ticket(self):
        """Test creating LibraryTicket from Ticket."""
        ticket = Ticket(
            id=12345,
            subject="Test ticket",
            description="Test description",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 20, 15, 45),
            assignee_id=123,
            group_id=456,
            url="https://company.zendesk.com/agent/tickets/12345"
        )
        
        lib_ticket = LibraryTicket.from_ticket(ticket, team_name="Support Team")
        
        assert lib_ticket.id == 12345
        assert lib_ticket.subject == "Test ticket"
        assert lib_ticket.description == "Test description"
        assert lib_ticket.status == "open"
        assert lib_ticket.team_name == "Support Team"
        assert lib_ticket.assignee_id == 123
        assert lib_ticket.group_id == 456
    
    def test_to_ticket(self):
        """Test converting LibraryTicket back to Ticket."""
        lib_ticket = LibraryTicket(
            id=12345,
            subject="Test ticket",
            description="Test description",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 20, 15, 45),
            assignee_id=123,
            group_id=456,
            url="https://company.zendesk.com/agent/tickets/12345",
            team_name="Support Team"
        )
        
        ticket = lib_ticket.to_ticket()
        
        assert isinstance(ticket, Ticket)
        assert ticket.id == 12345
        assert ticket.subject == "Test ticket"
        assert ticket.status == "open"
        # Note: team_name is not preserved in Ticket model
    
    def test_short_description(self):
        """Test short description property."""
        # Short description
        lib_ticket = LibraryTicket(
            id=1,
            subject="Test",
            description="Short desc",
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            assignee_id=None,
            group_id=None,
            url="https://test.com"
        )
        assert lib_ticket.short_description == "Short desc"
        
        # Long description
        long_desc = "This is a very long description that exceeds fifty characters"
        lib_ticket = LibraryTicket(
            id=1,
            subject="Test",
            description=long_desc,
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            assignee_id=None,
            group_id=None,
            url="https://test.com"
        )
        assert lib_ticket.short_description == "This is a very long description that exceeds f..."
    
    def test_dict_serialization(self):
        """Test dictionary serialization."""
        lib_ticket = LibraryTicket(
            id=12345,
            subject="Test ticket",
            description="Test description",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 20, 15, 45),
            assignee_id=123,
            group_id=456,
            url="https://company.zendesk.com/agent/tickets/12345",
            team_name="Support Team"
        )
        
        data = lib_ticket.dict()
        
        assert data["id"] == 12345
        assert data["subject"] == "Test ticket"
        assert data["status"] == "open"
        assert data["team_name"] == "Support Team"
        assert data["created_at"] == "2024-01-15T10:30:00"
        assert "days_since_created" in data
        assert "days_since_updated" in data
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        lib_ticket = LibraryTicket(
            id=12345,
            subject="Test ticket",
            description="Test description",
            status="open",
            created_at=datetime(2024, 1, 15, 10, 30),
            updated_at=datetime(2024, 1, 20, 15, 45),
            assignee_id=123,
            group_id=456,
            url="https://company.zendesk.com/agent/tickets/12345",
            team_name="Support Team"
        )
        
        json_str = lib_ticket.json()
        data = json.loads(json_str)
        
        assert data["id"] == 12345
        assert data["team_name"] == "Support Team"


class TestZendeskLibrary:
    """Test the main ZendeskLibrary class."""
    
    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        with patch('zendesk_cli.lib.client.ZendeskClient') as mock_client, \
             patch('zendesk_cli.lib.client.TicketService') as mock_service:
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            assert lib.domain == "test.zendesk.com"
            assert lib.email == "test@example.com"
            assert lib._api_token == "token123"
            mock_client.assert_called_once_with(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
    
    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with pytest.raises(ConfigurationError, match="Domain, email, and API token are required"):
            ZendeskLibrary(domain="", email="test@example.com", api_token="token")
    
    def test_from_credentials(self):
        """Test class method constructor with credentials."""
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService'):
            
            lib = ZendeskLibrary.from_credentials(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            assert lib.domain == "test.zendesk.com"
            assert lib.email == "test@example.com"
    
    @patch('zendesk_cli.lib.client.AuthService')
    def test_from_config(self, mock_auth_service):
        """Test class method constructor with config file."""
        # Mock configuration
        mock_config = Mock()
        mock_config.domain = "test.zendesk.com"
        mock_config.email = "test@example.com"
        mock_config.api_token = "token123"
        
        mock_auth_instance = Mock()
        mock_auth_instance.load_config.return_value = mock_config
        mock_auth_instance.validate_config.return_value = True
        mock_auth_service.return_value = mock_auth_instance
        
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService'):
            
            lib = ZendeskLibrary.from_config()
            
            assert lib.domain == "test.zendesk.com"
            assert lib.email == "test@example.com"
            mock_auth_instance.load_config.assert_called_once()
            mock_auth_instance.validate_config.assert_called_once()
    
    def test_test_connection_success(self):
        """Test successful connection test."""
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService') as mock_service_class:
            
            # Mock the ticket service instance
            mock_service = Mock()
            mock_service.get_current_user_info.return_value = {"name": "Test User"}
            mock_service_class.return_value = mock_service
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            result = lib.test_connection()
            
            assert result is True
            mock_service.get_current_user_info.assert_called_once()
    
    def test_get_tickets_basic(self):
        """Test basic ticket retrieval."""
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService') as mock_service_class:
            
            # Mock ticket data
            mock_ticket = Ticket(
                id=12345,
                subject="Test ticket",
                description="Test description",
                status="open",
                created_at=datetime(2024, 1, 15),
                updated_at=datetime(2024, 1, 20),
                assignee_id=123,
                group_id=456,
                url="https://test.zendesk.com/tickets/12345"
            )
            
            mock_service = Mock()
            mock_service.get_all_tickets.return_value = [mock_ticket]
            mock_service._get_team_name.return_value = "Support Team"
            mock_service_class.return_value = mock_service
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            tickets = lib.get_tickets(status="open")
            
            assert len(tickets) == 1
            assert isinstance(tickets[0], LibraryTicket)
            assert tickets[0].id == 12345
            assert tickets[0].subject == "Test ticket"
            assert tickets[0].team_name == "Support Team"
            mock_service.get_all_tickets.assert_called_once_with("open")
    
    def test_get_tickets_assignee_only(self):
        """Test ticket retrieval for assignee only."""
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService') as mock_service_class:
            
            mock_service = Mock()
            mock_service.get_current_user_info.return_value = {"id": 123, "name": "Test User"}
            mock_service.get_user_tickets.return_value = []
            mock_service_class.return_value = mock_service
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            tickets = lib.get_tickets(assignee_only=True)
            
            mock_service.get_user_tickets.assert_called_once_with(123, "open")
    
    def test_export_to_csv(self):
        """Test CSV export functionality."""
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService'):
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123"
            )
            
            # Create test tickets
            tickets = [
                LibraryTicket(
                    id=12345,
                    subject="Test ticket",
                    description="Test description with, comma",
                    status="open",
                    created_at=datetime(2024, 1, 15),
                    updated_at=datetime(2024, 1, 20),
                    assignee_id=123,
                    group_id=456,
                    url="https://test.zendesk.com/tickets/12345",
                    team_name="Support Team"
                )
            ]
            
            # Mock file operations
            mock_file_content = []
            
            def mock_write(content):
                mock_file_content.append(content)
            
            mock_file = Mock()
            mock_file.write = mock_write
            
            with patch('builtins.open', mock_open()) as mock_open_func, \
                 patch('csv.writer') as mock_csv_writer:
                
                mock_writer = Mock()
                mock_csv_writer.return_value = mock_writer
                
                lib.export_to_csv(tickets, "test.csv")
                
                # Verify CSV writer was called correctly
                mock_csv_writer.assert_called_once()
                mock_writer.writerow.assert_called()
                
                # Check that headers were written
                calls = mock_writer.writerow.call_args_list
                headers = calls[0][0][0]  # First call, first argument
                assert "Ticket #" in headers
                assert "Status" in headers
                assert "Team Name" in headers
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
        
        with patch('zendesk_cli.lib.client.ZendeskClient'), \
             patch('zendesk_cli.lib.client.TicketService') as mock_service_class:
            
            mock_service = Mock()
            mock_service.get_all_tickets.return_value = []
            mock_service_class.return_value = mock_service
            
            lib = ZendeskLibrary(
                domain="test.zendesk.com",
                email="test@example.com",
                api_token="token123",
                progress_callback=progress_callback
            )
            
            lib.get_tickets()
            
            assert len(progress_messages) > 0
            assert any("Fetching tickets" in msg for msg in progress_messages)


class TestLibraryIntegration:
    """Integration tests for library functionality."""
    
    def test_import_from_main_package(self):
        """Test that library can be imported from main package."""
        # This should work without errors
        from zendesk_cli import ZendeskLibrary, LibraryTicket
        
        assert ZendeskLibrary is not None
        assert LibraryTicket is not None
    
    def test_library_exceptions_available(self):
        """Test that all exceptions are available for import."""
        from zendesk_cli import (
            ZendeskCliError,
            AuthenticationError,
            APIError,
            ConfigurationError
        )
        
        assert ZendeskCliError is not None
        assert AuthenticationError is not None
        assert APIError is not None
        assert ConfigurationError is not None