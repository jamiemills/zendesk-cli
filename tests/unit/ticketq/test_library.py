"""Test TicketQLibrary functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

from src.ticketq.lib.client import TicketQLibrary
from src.ticketq.lib.models import LibraryTicket, LibraryUser, LibraryGroup
from src.ticketq.models.exceptions import TicketQError, ConfigurationError, AuthenticationError


class TestTicketQLibrary:
    """Test TicketQLibrary functionality."""

    def test_init_with_adapter(self, mock_adapter):
        """Test initialization with adapter instance."""
        tq = TicketQLibrary(mock_adapter)
        
        assert tq.adapter is mock_adapter
        assert tq._progress_callback is None

    def test_init_with_progress_callback(self, mock_adapter):
        """Test initialization with progress callback."""
        callback = Mock()
        tq = TicketQLibrary(mock_adapter, progress_callback=callback)
        
        assert tq._progress_callback is callback

    @patch('src.ticketq.lib.client.get_factory')
    def test_from_config_with_adapter_name(self, mock_get_factory, mock_adapter):
        """Test creating library from config with specific adapter."""
        mock_factory = Mock()
        mock_factory.create_adapter.return_value = mock_adapter
        mock_get_factory.return_value = mock_factory
        
        tq = TicketQLibrary.from_config(adapter_name="test")
        
        assert tq.adapter is mock_adapter
        mock_factory.create_adapter.assert_called_once_with("test")

    @patch('src.ticketq.lib.client.get_factory')
    def test_from_config_auto_detect(self, mock_get_factory, mock_adapter):
        """Test creating library from config with auto-detection."""
        mock_factory = Mock()
        mock_factory.create_adapter.return_value = mock_adapter
        mock_get_factory.return_value = mock_factory
        
        tq = TicketQLibrary.from_config()
        
        assert tq.adapter is mock_adapter
        mock_factory.create_adapter.assert_called_once_with(None)

    @patch('src.ticketq.lib.client.get_factory')
    def test_from_config_with_custom_path(self, mock_get_factory, mock_adapter):
        """Test creating library with custom config path."""
        mock_factory = Mock()
        mock_factory.create_adapter.return_value = mock_adapter
        mock_get_factory.return_value = mock_factory
        
        custom_path = Path("/custom/config")
        tq = TicketQLibrary.from_config(config_path=custom_path)
        
        # Should override config manager in factory
        assert tq.adapter is mock_adapter

    @patch('src.ticketq.lib.client.get_factory')
    def test_from_adapter(self, mock_get_factory, mock_adapter):
        """Test creating library with specific adapter and config."""
        mock_factory = Mock()
        mock_factory.create_adapter.return_value = mock_adapter
        mock_get_factory.return_value = mock_factory
        
        config = {"domain": "test.com"}
        tq = TicketQLibrary.from_adapter("test", config)
        
        assert tq.adapter is mock_adapter
        mock_factory.create_adapter.assert_called_once_with("test", config)

    def test_test_connection_success(self, mock_adapter, sample_user):
        """Test successful connection test."""
        mock_adapter.auth.authenticate.return_value = True
        mock_adapter.client.get_current_user.return_value = sample_user
        
        tq = TicketQLibrary(mock_adapter)
        result = tq.test_connection()
        
        assert result is True
        mock_adapter.auth.authenticate.assert_called_once()

    def test_test_connection_failure(self, mock_adapter):
        """Test failed connection test."""
        mock_adapter.auth.authenticate.return_value = False
        
        tq = TicketQLibrary(mock_adapter)
        result = tq.test_connection()
        
        assert result is False

    def test_test_connection_exception(self, mock_adapter):
        """Test connection test with exception."""
        mock_adapter.auth.authenticate.side_effect = Exception("Connection failed")
        
        tq = TicketQLibrary(mock_adapter)
        
        with pytest.raises(TicketQError, match="Connection test failed"):
            tq.test_connection()

    def test_get_tickets_basic(self, mock_adapter, sample_ticket):
        """Test basic ticket retrieval."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        mock_adapter._client.get_group.return_value = None
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets()
        
        assert len(tickets) == 1
        assert isinstance(tickets[0], LibraryTicket)
        assert tickets[0].id == sample_ticket.id

    def test_get_tickets_assignee_only(self, mock_adapter, sample_ticket, sample_user):
        """Test getting tickets for current user only."""
        mock_adapter._client.get_current_user.return_value = sample_user
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(assignee_only=True)
        
        assert len(tickets) == 1
        mock_adapter._client.get_tickets.assert_called_once_with(
            status="open",
            assignee_id=sample_user.id,
            assignee_only=True,
            groups=None
        )

    def test_get_tickets_with_groups(self, mock_adapter, sample_ticket, sample_group):
        """Test getting tickets for specific groups."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        mock_adapter._client.get_groups.return_value = [sample_group]
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(groups=["Support Team"])
        
        assert len(tickets) == 1

    def test_get_tickets_with_team_names(self, mock_adapter, sample_ticket, sample_group):
        """Test getting tickets with team name resolution."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        mock_adapter._client.get_group.return_value = sample_group
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(include_team_names=True)
        
        assert len(tickets) == 1
        assert tickets[0].team_name == sample_group.name

    def test_get_tickets_without_team_names(self, mock_adapter, sample_ticket):
        """Test getting tickets without team name resolution."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(include_team_names=False)
        
        assert len(tickets) == 1
        assert tickets[0].team_name is None

    def test_get_tickets_with_sorting(self, mock_adapter, sample_ticket):
        """Test getting tickets with sorting."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket]
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(sort_by="created_at")
        
        assert len(tickets) == 1
        # Sorting should be applied

    def test_get_ticket_by_id(self, mock_adapter, sample_ticket, sample_group):
        """Test getting specific ticket by ID."""
        mock_adapter._client.get_ticket.return_value = sample_ticket
        mock_adapter._client.get_group.return_value = sample_group
        
        tq = TicketQLibrary(mock_adapter)
        ticket = tq.get_ticket("12345")
        
        assert ticket is not None
        assert isinstance(ticket, LibraryTicket)
        assert ticket.id == sample_ticket.id
        assert ticket.team_name == sample_group.name

    def test_get_ticket_not_found(self, mock_adapter):
        """Test getting non-existent ticket."""
        mock_adapter._client.get_ticket.return_value = None
        
        tq = TicketQLibrary(mock_adapter)
        ticket = tq.get_ticket("nonexistent")
        
        assert ticket is None

    def test_get_current_user(self, mock_adapter, sample_user):
        """Test getting current user."""
        mock_adapter._client.get_current_user.return_value = sample_user
        
        tq = TicketQLibrary(mock_adapter)
        user = tq.get_current_user()
        
        assert user is not None
        assert isinstance(user, LibraryUser)
        assert user.id == sample_user.id

    def test_get_groups(self, mock_adapter, sample_group):
        """Test getting all groups."""
        mock_adapter._client.get_groups.return_value = [sample_group]
        
        tq = TicketQLibrary(mock_adapter)
        groups = tq.get_groups()
        
        assert len(groups) == 1
        assert isinstance(groups[0], LibraryGroup)
        assert groups[0].id == sample_group.id

    def test_search_tickets(self, mock_adapter, sample_ticket, sample_group):
        """Test searching tickets."""
        mock_adapter._client.search_tickets.return_value = [sample_ticket]
        mock_adapter._client.get_group.return_value = sample_group
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.search_tickets("test query")
        
        assert len(tickets) == 1
        assert isinstance(tickets[0], LibraryTicket)
        mock_adapter._client.search_tickets.assert_called_once_with("test query")

    def test_export_to_csv(self, mock_adapter, sample_library_ticket):
        """Test CSV export functionality."""
        tq = TicketQLibrary(mock_adapter)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            tq.export_to_csv([sample_library_ticket], csv_path)
            
            # Read the file back to verify content
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "Ticket ID" in content  # Header
            assert sample_library_ticket.id in content
            assert sample_library_ticket.title in content
        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_export_to_csv_with_full_description(self, mock_adapter, sample_library_ticket):
        """Test CSV export with full descriptions."""
        tq = TicketQLibrary(mock_adapter)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            tq.export_to_csv([sample_library_ticket], csv_path, include_full_description=True)
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert sample_library_ticket.description in content
        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_export_to_csv_with_short_description(self, mock_adapter, sample_library_ticket):
        """Test CSV export with short descriptions."""
        tq = TicketQLibrary(mock_adapter)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            tq.export_to_csv([sample_library_ticket], csv_path, include_full_description=False)
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should contain short description
            assert content.count('"') > 0  # CSV should be quoted
        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_get_adapter_info(self, mock_adapter):
        """Test getting adapter information."""
        tq = TicketQLibrary(mock_adapter)
        info = tq.get_adapter_info()
        
        assert info["name"] == mock_adapter.name
        assert info["display_name"] == mock_adapter.display_name
        assert info["version"] == mock_adapter.version
        assert "supported_features" in info

    def test_progress_callback(self, mock_adapter):
        """Test progress callback functionality."""
        callback = Mock()
        tq = TicketQLibrary(mock_adapter, progress_callback=callback)
        
        # Call a method that triggers progress
        mock_adapter._client.get_tickets.return_value = []
        tq.get_tickets()
        
        # Should have called progress callback
        callback.assert_called()

    def test_error_propagation(self, mock_adapter):
        """Test that errors are properly propagated."""
        mock_adapter._client.get_tickets.side_effect = AuthenticationError("Auth failed")
        
        tq = TicketQLibrary(mock_adapter)
        
        with pytest.raises(AuthenticationError):
            tq.get_tickets()

    def test_team_name_caching(self, mock_adapter, sample_ticket, sample_group):
        """Test that team names are cached."""
        mock_adapter._client.get_tickets.return_value = [sample_ticket, sample_ticket]
        mock_adapter._client.get_group.return_value = sample_group
        
        tq = TicketQLibrary(mock_adapter)
        tickets = tq.get_tickets(include_team_names=True)
        
        assert len(tickets) == 2
        # Should only call get_group once due to caching
        assert mock_adapter._client.get_group.call_count == 1