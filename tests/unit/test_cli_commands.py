"""Tests for CLI command functionality."""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from typing import List

from zendesk_cli.models.ticket import Ticket


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