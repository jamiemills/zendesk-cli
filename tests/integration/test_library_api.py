"""Integration tests for Library API."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ticketq import TicketQLibrary
from ticketq.lib.models import LibraryTicket, LibraryUser, LibraryGroup
from ticketq.utils.config import ConfigManager
from ticketq.models.exceptions import ConfigurationError, AuthenticationError

# Import test helpers
from tests.helpers import (
    create_mock_adapter, 
    create_mock_client, 
    create_mock_auth,
    create_sample_tickets,
    create_sample_users,
    create_sample_groups
)


class TestLibraryAPIIntegration:
    """Test Library API integration."""

    def test_library_initialization_patterns(self):
        """Test different library initialization patterns."""
        # Test from_config with adapter auto-detection
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            config_manager = ConfigManager(config_dir)
            config_manager.save_adapter_config("zendesk", {
                "domain": "test.zendesk.com",
                "email": "test@example.com",
                "api_token": "test_token_with_proper_length"
            })
            
            with patch('ticketq.lib.client.ConfigManager') as mock_config_class:
                mock_config_class.return_value = config_manager
                
                with patch('ticketq.lib.client.get_factory') as mock_get_factory:
                    mock_factory = Mock()
                    mock_adapter = Mock()
                    mock_adapter.name = "zendesk"
                    mock_adapter.display_name = "Zendesk"
                    mock_adapter.version = "0.1.0"
                    mock_adapter.supported_features = ["tickets"]
                    
                    mock_factory.create_adapter.return_value = mock_adapter
                    mock_get_factory.return_value = mock_factory
                    
                    # Test auto-detection
                    library = TicketQLibrary.from_config(config_path=tmp_dir)
                    assert library is not None
                    
                    # Test specific adapter
                    library = TicketQLibrary.from_config(adapter_name="zendesk", config_path=tmp_dir)
                    assert library is not None

    def test_library_from_adapter(self):
        """Test creating library from adapter instance."""
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        assert library is not None
        assert library.adapter is mock_adapter

    def test_library_progress_callback(self):
        """Test library with progress callback."""
        mock_adapter = create_mock_adapter("test", ["tickets"])
        
        progress_messages = []
        def progress_callback(message):
            progress_messages.append(message)
        
        library = TicketQLibrary.from_adapter(mock_adapter, progress_callback=progress_callback)
        
        # Trigger progress callback
        library._progress("Test message")
        assert "Test message" in progress_messages

    def test_library_get_tickets_functionality(self):
        """Test library get_tickets with various parameters."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Create sample ticket and user using helpers
        sample_ticket = create_sample_tickets(1)
        sample_user = create_sample_users(1)
        mock_adapter.client.get_tickets.return_value = [sample_ticket]
        mock_adapter.client.get_current_user.return_value = sample_user
        mock_adapter.client.get_groups.return_value = []
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        # Test basic get_tickets
        tickets = library.get_tickets()
        assert len(tickets) == 1
        assert isinstance(tickets[0], LibraryTicket)
        assert tickets[0].id == sample_ticket.id
        assert tickets[0].title == sample_ticket.title
        assert tickets[0].adapter_name == sample_ticket.adapter_name
        
        # Test with status filter
        tickets = library.get_tickets(status=["open", "pending"])
        mock_adapter.client.get_tickets.assert_called_with(
            status=["open", "pending"],
            assignee_only=False,
            groups=None
        )
        
        # Test with assignee_only
        library.get_tickets(assignee_only=True)
        mock_adapter.client.get_tickets.assert_called_with(
            status="open",
            assignee_id=sample_user.id,
            assignee_only=True,
            groups=None
        )
        
        # Test with groups (uses different internal logic)
        tickets = library.get_tickets(groups=["Support"])
        # Groups filtering goes through _get_tickets_for_groups method
        assert isinstance(tickets, list)

    def test_library_get_ticket_by_id(self):
        """Test library get_ticket method."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Create sample ticket using helper
        sample_ticket = create_sample_tickets(1)
        mock_adapter.client.get_ticket.return_value = sample_ticket
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        ticket = library.get_ticket("123")
        
        assert isinstance(ticket, LibraryTicket)
        assert ticket.id == sample_ticket.id
        mock_adapter.client.get_ticket.assert_called_once_with("123")

    def test_library_get_current_user(self):
        """Test library get_current_user method."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["users"])
        
        # Create sample user using helper
        sample_user = create_sample_users(1)
        mock_adapter.client.get_current_user.return_value = sample_user
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        user = library.get_current_user()
        
        assert isinstance(user, LibraryUser)
        assert user.id == sample_user.id
        assert user.name == sample_user.name
        mock_adapter.client.get_current_user.assert_called_once()

    def test_library_get_groups(self):
        """Test library get_groups method."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["groups"])
        
        # Create sample group using helper
        sample_group = create_sample_groups(1)
        mock_adapter.client.get_groups.return_value = [sample_group]
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        groups = library.get_groups()
        
        assert len(groups) == 1
        assert isinstance(groups[0], LibraryGroup)
        assert groups[0].id == sample_group.id
        assert groups[0].name == sample_group.name
        mock_adapter.client.get_groups.assert_called_once()

    def test_library_test_connection(self):
        """Test library test_connection method."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["authentication"])
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        # Test successful connection
        mock_adapter.auth.authenticate.return_value = True
        result = library.test_connection()
        assert result is True
        mock_adapter.auth.authenticate.assert_called()
        
        # Test failed connection
        mock_adapter.auth.authenticate.return_value = False
        result = library.test_connection()
        assert result is False

    def test_library_export_to_csv(self, tmp_path):
        """Test library CSV export functionality."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["export"])
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        # Create test tickets using LibraryTicket directly (since this is CSV export test)
        tickets = [
            LibraryTicket(
                id="123",
                title="Test ticket 1",
                description="First test ticket",
                status="open",
                assignee_id="user1@example.com",
                group_id="456",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                url="https://test.zendesk.com/tickets/123",
                adapter_name="zendesk",
                team_name="Support"
            ),
            LibraryTicket(
                id="124",
                title="Test ticket 2",
                description="Second test ticket",
                status="pending",
                assignee_id="user2@example.com",
                group_id="457",
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
                url="https://test.zendesk.com/tickets/124",
                adapter_name="zendesk",
                team_name="Engineering"
            )
        ]
        
        csv_file = tmp_path / "test_export.csv"
        library.export_to_csv(tickets, str(csv_file))
        
        # Verify file was created and contains expected content
        assert csv_file.exists()
        content = csv_file.read_text()
        assert "Test ticket 1" in content
        assert "Test ticket 2" in content
        assert "Support" in content
        assert "Engineering" in content

    def test_library_get_adapter_info(self):
        """Test library get_adapter_info method."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets", "users", "groups"])
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        info = library.get_adapter_info()
        
        assert info["name"] == "zendesk"
        assert info["display_name"] == "Zendesk"
        assert info["version"] == "0.1.0"
        assert "tickets" in info["supported_features"]

    def test_library_sorting_functionality(self):
        """Test library ticket sorting functionality."""
        # Create mock adapter with helper
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        
        # Create tickets with different dates using models
        from ticketq.models.ticket import Ticket
        tickets = [
            Ticket(
                id="1",
                title="Older ticket",
                description="Older",
                status="open",
                assignee_id="user@example.com",
                group_id="456",
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
                url="https://test.zendesk.com/tickets/1",
                adapter_name="zendesk"
            ),
            Ticket(
                id="2",
                title="Newer ticket",
                description="Newer",
                status="open",
                assignee_id="user@example.com",
                group_id="456",
                created_at=datetime(2024, 1, 10),
                updated_at=datetime(2024, 1, 10),
                url="https://test.zendesk.com/tickets/2",
                adapter_name="zendesk"
            )
        ]
        
        mock_adapter.client.get_tickets.return_value = tickets
        mock_adapter.client.get_groups.return_value = []
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        
        # Test sorting by creation date (newest first)
        sorted_tickets = library.get_tickets(sort_by="created_at")
        assert sorted_tickets[0].id == "2"  # Newer ticket first
        assert sorted_tickets[1].id == "1"  # Older ticket second
        
        # Test sorting by days since creation (fewer days first)
        sorted_tickets = library.get_tickets(sort_by="days_created")
        assert sorted_tickets[0].id == "2"  # Newer ticket first (fewer days)
        assert sorted_tickets[1].id == "1"  # Older ticket second (more days)

    def test_library_error_handling(self):
        """Test library error handling."""
        # Test configuration error propagation
        with patch('ticketq.lib.client.get_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_factory.create_adapter.side_effect = ConfigurationError("No config found")
            mock_get_factory.return_value = mock_factory
            
            with pytest.raises(ConfigurationError):
                TicketQLibrary.from_config(adapter_name="nonexistent")
        
        # Test authentication error propagation
        mock_adapter = create_mock_adapter("zendesk", ["tickets"])
        mock_adapter.auth.authenticate.side_effect = AuthenticationError("Invalid credentials")
        
        library = TicketQLibrary.from_adapter(mock_adapter)
        with pytest.raises(AuthenticationError):
            library.test_connection()