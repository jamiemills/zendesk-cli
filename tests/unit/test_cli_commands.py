"""Tests for CLI command functionality."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from typing import List, Dict, Any

from zendesk_cli.models.ticket import Ticket
from zendesk_cli.cli.commands.tickets import parse_statuses, parse_groups, sort_tickets_with_teams, export_tickets_to_csv


class TestTicketsCommand:
    """Test the tickets CLI command."""
    
    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def sample_tickets(self) -> List[Ticket]:
        """Sample tickets for testing."""
        return [
            Ticket(
                id=1,
                subject="Login issue",
                description="Users cannot authenticate",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                assignee_id=123,
                group_id=456,
                url="https://example.zendesk.com/tickets/1"
            ),
            Ticket(
                id=2,
                subject="Feature request",
                description="Add dark mode support",
                status="pending",
                created_at="2024-01-02T10:00:00Z",
                updated_at="2024-01-02T15:00:00Z",
                assignee_id=124,
                group_id=456,
                url="https://example.zendesk.com/tickets/2"
            )
        ]
    
    @patch('zendesk_cli.cli.commands.tickets.AuthService')
    @patch('zendesk_cli.cli.commands.tickets.TicketService')
    def test_tickets_command_success(
        self, 
        mock_ticket_service_class: Mock,
        mock_auth_service_class: Mock,
        runner: CliRunner,
        sample_tickets: List[Ticket]
    ) -> None:
        """Test successful tickets command execution."""
        from zendesk_cli.cli.commands.tickets import tickets
        
        # Setup mocks
        mock_auth_service = Mock()
        mock_ticket_service = Mock()
        mock_config = Mock()
        
        mock_auth_service_class.return_value = mock_auth_service
        mock_ticket_service_class.return_value = mock_ticket_service
        
        mock_auth_service.load_config.return_value = mock_config
        mock_auth_service.validate_config.return_value = True
        mock_auth_service.create_client_from_config.return_value = Mock()
        
        mock_ticket_service.get_all_open_tickets.return_value = sample_tickets
        
        # Run command
        result = runner.invoke(tickets)
        
        # Verify success
        assert result.exit_code == 0
        assert "Login issue" in result.output
        assert "Feature request" in result.output
        mock_ticket_service.get_all_open_tickets.assert_called_once()
    
    @patch('zendesk_cli.cli.commands.tickets.AuthService')
    def test_tickets_command_no_config(
        self, 
        mock_auth_service_class: Mock,
        runner: CliRunner
    ) -> None:
        """Test tickets command when no configuration exists."""
        from zendesk_cli.cli.commands.tickets import tickets
        from zendesk_cli.models.exceptions import ConfigurationError
        
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        mock_auth_service.load_config.side_effect = ConfigurationError("No config found")
        
        result = runner.invoke(tickets)
        
        assert result.exit_code != 0
        assert "configuration" in result.output.lower()
    
    @patch('zendesk_cli.cli.commands.tickets.AuthService')
    @patch('zendesk_cli.cli.commands.tickets.TicketService')
    def test_tickets_command_assignee_only_flag(
        self,
        mock_ticket_service_class: Mock,
        mock_auth_service_class: Mock,
        runner: CliRunner,
        sample_tickets: List[Ticket]
    ) -> None:
        """Test tickets command with --assignee-only flag."""
        from zendesk_cli.cli.commands.tickets import tickets
        
        # Setup mocks
        mock_auth_service = Mock()
        mock_ticket_service = Mock()
        mock_config = Mock()
        
        mock_auth_service_class.return_value = mock_auth_service
        mock_ticket_service_class.return_value = mock_ticket_service
        
        mock_auth_service.load_config.return_value = mock_config
        mock_auth_service.validate_config.return_value = True
        mock_auth_service.create_client_from_config.return_value = Mock()
        
        mock_ticket_service.get_current_user_info.return_value = {"id": 123}
        mock_ticket_service.get_user_tickets.return_value = sample_tickets
        
        # Run command with flag
        result = runner.invoke(tickets, ['--assignee-only'])
        
        # Verify
        assert result.exit_code == 0
        mock_ticket_service.get_user_tickets.assert_called_once_with(user_id=123)
    
    @patch('zendesk_cli.cli.commands.tickets.AuthService')
    @patch('zendesk_cli.cli.commands.tickets.TicketService')
    def test_tickets_command_group_filter(
        self,
        mock_ticket_service_class: Mock,
        mock_auth_service_class: Mock,
        runner: CliRunner,
        sample_tickets: List[Ticket]
    ) -> None:
        """Test tickets command with --group filter."""
        from zendesk_cli.cli.commands.tickets import tickets
        
        # Setup mocks
        mock_auth_service = Mock()
        mock_ticket_service = Mock()
        mock_config = Mock()
        
        mock_auth_service_class.return_value = mock_auth_service
        mock_ticket_service_class.return_value = mock_ticket_service
        
        mock_auth_service.load_config.return_value = mock_config
        mock_auth_service.validate_config.return_value = True
        mock_auth_service.create_client_from_config.return_value = Mock()
        
        mock_ticket_service.get_group_tickets.return_value = sample_tickets
        
        # Run command with group filter
        result = runner.invoke(tickets, ['--group', '456'])
        
        # Verify
        assert result.exit_code == 0
        mock_ticket_service.get_group_tickets.assert_called_once_with(group_id=456)


class TestConfigureCommand:
    """Test the configure CLI command."""
    
    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()
    
    @patch('zendesk_cli.cli.commands.configure.AuthService')
    def test_configure_command_interactive(
        self,
        mock_auth_service_class: Mock,
        runner: CliRunner
    ) -> None:
        """Test interactive configure command."""
        from zendesk_cli.cli.commands.configure import configure
        
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        
        # Simulate user input
        user_input = "example.zendesk.com\ntest@example.com\ntest_token\n"
        
        result = runner.invoke(configure, input=user_input)
        
        assert result.exit_code == 0
        mock_auth_service.save_config.assert_called_once()
    
    @patch('zendesk_cli.cli.commands.configure.AuthService')
    def test_configure_command_with_flags(
        self,
        mock_auth_service_class: Mock,
        runner: CliRunner
    ) -> None:
        """Test configure command with command line flags."""
        from zendesk_cli.cli.commands.configure import configure
        
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        
        result = runner.invoke(configure, [
            '--domain', 'example.zendesk.com',
            '--email', 'test@example.com',
            '--api-token', 'test_token'
        ])
        
        assert result.exit_code == 0
        mock_auth_service.save_config.assert_called_once()
    
    @patch('zendesk_cli.cli.commands.configure.AuthService')
    def test_configure_command_test_connection(
        self,
        mock_auth_service_class: Mock,
        runner: CliRunner
    ) -> None:
        """Test configure command with connection testing."""
        from zendesk_cli.cli.commands.configure import configure
        
        mock_auth_service = Mock()
        mock_auth_service_class.return_value = mock_auth_service
        
        mock_client = Mock()
        mock_auth_service.create_client_from_config.return_value = mock_client
        mock_client.get_current_user.return_value = {"name": "Test User"}
        
        result = runner.invoke(configure, [
            '--domain', 'example.zendesk.com',
            '--email', 'test@example.com',
            '--api-token', 'test_token',
            '--test'
        ])
        
        assert result.exit_code == 0
        assert "Test User" in result.output
        mock_client.get_current_user.assert_called_once()


class TestParsingFunctions:
    """Test parsing utility functions for CLI commands."""
    
    def test_parse_statuses_single_status(self) -> None:
        """Test parsing a single status."""
        result = parse_statuses("open")
        assert result == ["open"]
    
    def test_parse_statuses_multiple_statuses(self) -> None:
        """Test parsing multiple comma-separated statuses."""
        result = parse_statuses("open,pending,hold")
        assert result == ["open", "pending", "hold"]
    
    def test_parse_statuses_with_spaces(self) -> None:
        """Test parsing statuses with spaces around commas."""
        result = parse_statuses("open, pending , hold")
        assert result == ["open", "pending", "hold"]
    
    def test_parse_statuses_case_insensitive(self) -> None:
        """Test parsing statuses is case insensitive."""
        result = parse_statuses("OPEN,Pending,HOLD")
        assert result == ["open", "pending", "hold"]
    
    def test_parse_statuses_default_when_empty(self) -> None:
        """Test parsing returns default when input is empty."""
        result = parse_statuses("")
        assert result == ["open"]
        
        result = parse_statuses(None)
        assert result == ["open"]
    
    def test_parse_statuses_invalid_status_raises_error(self) -> None:
        """Test parsing raises ValueError for invalid statuses."""
        with pytest.raises(ValueError, match="Invalid status\\(es\\): invalid"):
            parse_statuses("open,invalid,pending")
    
    def test_parse_statuses_all_valid_statuses(self) -> None:
        """Test parsing accepts all valid status values."""
        valid_statuses = "new,open,pending,hold,solved,closed"
        result = parse_statuses(valid_statuses)
        assert result == ["new", "open", "pending", "hold", "solved", "closed"]
    
    def test_parse_groups_single_group_id(self) -> None:
        """Test parsing a single group ID."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_service = Mock(spec=TicketService)
        mock_service._get_groups_mapping.return_value = {123: "Support Team"}
        
        result = parse_groups("123", mock_service)
        assert result == [123]
    
    def test_parse_groups_multiple_group_ids(self) -> None:
        """Test parsing multiple comma-separated group IDs."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_service = Mock(spec=TicketService)
        mock_service._get_groups_mapping.return_value = {123: "Support", 456: "Engineering"}
        
        result = parse_groups("123,456", mock_service)
        assert result == [123, 456]
    
    def test_parse_groups_by_name(self) -> None:
        """Test parsing groups by name."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_service = Mock(spec=TicketService)
        mock_service._get_groups_mapping.return_value = {123: "Support Team", 456: "Engineering"}
        
        result = parse_groups("Support Team", mock_service)
        assert result == [123]
    
    def test_parse_groups_mixed_ids_and_names(self) -> None:
        """Test parsing mixed group IDs and names."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_service = Mock(spec=TicketService)
        mock_service._get_groups_mapping.return_value = {123: "Support Team", 456: "Engineering"}
        
        result = parse_groups("123,Engineering", mock_service)
        assert result == [123, 456]
    
    def test_parse_groups_unknown_name_raises_error(self) -> None:
        """Test parsing raises ValueError for unknown group name."""
        from zendesk_cli.services.ticket_service import TicketService
        
        mock_service = Mock(spec=TicketService)
        mock_service._get_groups_mapping.return_value = {123: "Support Team"}
        
        with pytest.raises(ValueError, match="Group 'Unknown' not found"):
            parse_groups("Unknown", mock_service)


class TestSortingAndCSVExport:
    """Test sorting and CSV export functionality."""
    
    @pytest.fixture
    def sample_tickets_with_teams(self) -> List[Dict[str, Any]]:
        """Sample tickets with team names for testing."""
        from datetime import datetime
        
        return [
            {
                "ticket": Ticket(
                    id=1,
                    subject="First ticket",
                    description="First description",
                    status="open", 
                    created_at=datetime(2024, 1, 1, 10, 0, 0),
                    updated_at=datetime(2024, 1, 1, 11, 0, 0),
                    assignee_id=100,
                    group_id=200,
                    url="https://example.zendesk.com/tickets/1"
                ),
                "team_name": "Support"
            },
            {
                "ticket": Ticket(
                    id=2,
                    subject="Second ticket", 
                    description="Second description",
                    status="pending",
                    created_at=datetime(2024, 1, 2, 10, 0, 0),
                    updated_at=datetime(2024, 1, 2, 11, 0, 0),
                    assignee_id=101,
                    group_id=201,
                    url="https://example.zendesk.com/tickets/2"
                ),
                "team_name": "Engineering"
            },
            {
                "ticket": Ticket(
                    id=3,
                    subject="Third ticket",
                    description="Third description", 
                    status="closed",
                    created_at=datetime(2024, 1, 3, 10, 0, 0),
                    updated_at=datetime(2024, 1, 3, 11, 0, 0),
                    assignee_id=102,
                    group_id=200,
                    url="https://example.zendesk.com/tickets/3"
                ),
                "team_name": "Support"
            }
        ]
    
    def test_sort_by_ticket_id(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test sorting by ticket ID."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, "ticket")
        
        ticket_ids = [item["ticket"].id for item in sorted_tickets]
        assert ticket_ids == [1, 2, 3]
    
    def test_sort_by_status(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test sorting by status."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, "status")
        
        statuses = [item["ticket"].status for item in sorted_tickets]
        assert statuses == ["closed", "open", "pending"]  # Alphabetical order
    
    def test_sort_by_team(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test sorting by team name."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, "team")
        
        team_names = [item["team_name"] for item in sorted_tickets]
        assert team_names == ["Engineering", "Support", "Support"]  # Alphabetical order
    
    def test_sort_by_opened_date(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test sorting by opened date (default behavior - newest first)."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, "opened")
        
        ticket_ids = [item["ticket"].id for item in sorted_tickets]
        assert ticket_ids == [3, 2, 1]  # Newest first
    
    def test_sort_default_behavior(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test default sorting behavior (newest first by created date)."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, None)
        
        ticket_ids = [item["ticket"].id for item in sorted_tickets]
        assert ticket_ids == [3, 2, 1]  # Newest first
    
    def test_sort_invalid_column(self, sample_tickets_with_teams: List[Dict[str, Any]]) -> None:
        """Test sorting with invalid column falls back to default."""
        sorted_tickets = sort_tickets_with_teams(sample_tickets_with_teams, "invalid")
        
        ticket_ids = [item["ticket"].id for item in sorted_tickets]
        assert ticket_ids == [3, 2, 1]  # Falls back to newest first
    
    def test_csv_export(self, sample_tickets_with_teams: List[Dict[str, Any]], tmp_path) -> None:
        """Test CSV export functionality."""
        import csv
        
        csv_file = tmp_path / "test_tickets.csv"
        export_tickets_to_csv(sample_tickets_with_teams, str(csv_file))
        
        # Verify CSV was created
        assert csv_file.exists()
        
        # Read and verify CSV content
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Check header
        expected_header = [
            "Ticket #", "Status", "Team Name", "Description", 
            "Opened", "Days Since Opened", "Updated", "Days Since Updated", "Link"
        ]
        assert rows[0] == expected_header
        
        # Check data rows
        assert len(rows) == 4  # Header + 3 data rows
        assert rows[1][0] == "#1"  # Ticket ID
        assert rows[1][1] == "Open"  # Status (capitalized)
        assert rows[1][2] == "Support"  # Team name
        assert rows[1][3] == "First description"  # Full description (not truncated)
        
    def test_csv_export_escapes_commas(self, tmp_path) -> None:
        """Test that CSV export properly escapes commas in descriptions."""
        import csv
        from datetime import datetime
        
        tickets_with_commas = [
            {
                "ticket": Ticket(
                    id=1,
                    subject="Test ticket",
                    description="Description with, commas, in it",
                    status="open",
                    created_at=datetime(2024, 1, 1, 10, 0, 0),
                    updated_at=datetime(2024, 1, 1, 11, 0, 0),
                    url="https://example.zendesk.com/tickets/1"
                ),
                "team_name": "Team, with, commas"
            }
        ]
        
        csv_file = tmp_path / "test_commas.csv"
        export_tickets_to_csv(tickets_with_commas, str(csv_file))
        
        # Read CSV and verify commas are properly escaped
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # The description and team name should be read correctly despite having commas
        assert rows[1][2] == "Team, with, commas"
        assert rows[1][3] == "Description with, commas, in it"