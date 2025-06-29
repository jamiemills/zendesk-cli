"""Integration tests for CLI workflow."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from ticketq.cli.main import main as cli
from ticketq.utils.config import ConfigManager
from ticketq.models.exceptions import ConfigurationError


class TestCLIWorkflowIntegration:
    """Test end-to-end CLI workflows."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    def test_adapters_command_lists_available(self):
        """Test that adapters command lists available adapters."""
        result = self.runner.invoke(cli, ['adapters'])
        
        assert result.exit_code == 0
        assert "zendesk" in result.output.lower()
        assert "Zendesk" in result.output

    def test_adapters_command_with_test(self):
        """Test adapters command with test flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            
            # Create mock config
            config_manager = ConfigManager(config_dir)
            config_manager.save_adapter_config("zendesk", {
                "domain": "test.zendesk.com",
                "email": "test@example.com",
                "api_token": "test_token_with_proper_length"
            })
            
            with patch('ticketq.cli.commands.adapters.ConfigManager') as mock_config_class:
                mock_config_class.return_value = config_manager
                
                with patch('ticketq.cli.commands.adapters.get_factory') as mock_get_factory:
                    # Mock factory and adapter
                    mock_factory = Mock()
                    mock_adapter = Mock()
                    mock_adapter._client.test_connection.return_value = True
                    mock_factory.create_adapter.return_value = mock_adapter
                    mock_get_factory.return_value = mock_factory
                    
                    result = self.runner.invoke(cli, ['adapters', '--test'])
                    assert result.exit_code == 0

    def test_configure_command_lists_adapters(self):
        """Test configure command with list-adapters flag."""
        result = self.runner.invoke(cli, ['configure', '--list-adapters'])
        
        assert result.exit_code == 0
        assert "zendesk" in result.output.lower()

    @patch('ticketq.cli.commands.configure.get_registry')
    @patch('ticketq.cli.commands.configure.ConfigManager')
    @patch('ticketq.cli.commands.configure.prompt_for_config')
    def test_configure_workflow(self, mock_prompt, mock_config_class, mock_registry):
        """Test complete configuration workflow."""
        # Mock registry
        mock_registry_instance = Mock()
        mock_adapter_class = Mock()
        mock_adapter = Mock()
        
        mock_adapter.get_config_schema.return_value = {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "email": {"type": "string"},
                "api_token": {"type": "string"}
            }
        }
        mock_adapter.get_default_config.return_value = {}
        mock_adapter.validate_config.return_value = True
        mock_adapter_class.return_value = mock_adapter
        
        mock_registry_instance.get_available_adapters.return_value = {"zendesk": mock_adapter_class}
        mock_registry.return_value = mock_registry_instance
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.get_adapter_config.side_effect = ConfigurationError("Not found")
        mock_config_class.return_value = mock_config_manager
        
        # Mock user input
        mock_prompt.return_value = {
            "domain": "test.zendesk.com",
            "email": "test@example.com",
            "api_token": "test_token_with_proper_length"
        }
        
        result = self.runner.invoke(cli, ['configure', '--adapter', 'zendesk'])
        assert result.exit_code == 0

    @patch('ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_command_basic(self, mock_library_class):
        """Test basic tickets command."""
        from ticketq.lib.models import LibraryTicket
        from datetime import datetime
        
        # Create mock ticket
        mock_ticket = LibraryTicket(
            id="123",
            title="Test ticket",
            description="Test description",
            status="open",
            assignee_id="test@example.com",
            group_id="456",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            url="https://test.zendesk.com/tickets/123",
            adapter_name="zendesk",
            team_name="Support"
        )
        
        mock_library = Mock()
        mock_library.get_tickets.return_value = [mock_ticket]
        mock_library.get_adapter_info.return_value = {
            "name": "zendesk",
            "display_name": "Zendesk"
        }
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(cli, ['tickets'])
        assert result.exit_code == 0
        assert "#123" in result.output
        assert "Test" in result.output  # Title gets truncated in table display

    @patch('ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_command_with_filters(self, mock_library_class):
        """Test tickets command with various filters."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {
            "name": "zendesk",
            "display_name": "Zendesk"
        }
        mock_library_class.from_config.return_value = mock_library
        
        # Test status filter
        result = self.runner.invoke(cli, ['tickets', '--status', 'open,pending'])
        assert result.exit_code == 0
        mock_library.get_tickets.assert_called_with(
            status=['open', 'pending'],
            assignee_only=False,
            groups=None,
            sort_by=None,
            include_team_names=True
        )
        
        # Test assignee-only filter
        result = self.runner.invoke(cli, ['tickets', '--assignee-only'])
        assert result.exit_code == 0
        
        # Test group filter
        result = self.runner.invoke(cli, ['tickets', '--group', 'Support Team'])
        assert result.exit_code == 0

    @patch('ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_command_with_csv_export(self, mock_library_class, tmp_path):
        """Test tickets command with CSV export."""
        from ticketq.lib.models import LibraryTicket
        from datetime import datetime
        
        mock_ticket = LibraryTicket(
            id="123",
            title="Test ticket",
            description="Test description",
            status="open",
            assignee_id="test@example.com",
            group_id="456",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            url="https://test.zendesk.com/tickets/123",
            adapter_name="zendesk",
            team_name="Support"
        )
        
        mock_library = Mock()
        mock_library.get_tickets.return_value = [mock_ticket]
        mock_library.get_adapter_info.return_value = {
            "name": "zendesk",
            "display_name": "Zendesk"
        }
        mock_library_class.from_config.return_value = mock_library
        
        csv_file = tmp_path / "test.csv"
        result = self.runner.invoke(cli, ['tickets', '--csv', str(csv_file)])
        
        assert result.exit_code == 0
        assert "Exported" in result.output
        mock_library.export_to_csv.assert_called_once()

    def test_tickets_command_invalid_status(self):
        """Test tickets command with invalid status."""
        result = self.runner.invoke(cli, ['tickets', '--status', 'invalid,open'])
        
        assert result.exit_code == 1
        assert "Invalid status" in result.output

    @patch('ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_command_configuration_error(self, mock_library_class):
        """Test tickets command with configuration error."""
        mock_library_class.from_config.side_effect = ConfigurationError(
            "No adapters configured",
            suggestions=["Configure an adapter with: tq configure"]
        )
        
        result = self.runner.invoke(cli, ['tickets'])
        
        assert result.exit_code == 1
        assert "Configuration error" in result.output
        assert "No adapters configured" in result.output
        assert "Configure an adapter" in result.output

    def test_help_commands(self):
        """Test that help commands work properly."""
        # Main help
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "TicketQ" in result.output
        
        # Subcommand help
        result = self.runner.invoke(cli, ['tickets', '--help'])
        assert result.exit_code == 0
        assert "tickets" in result.output.lower()
        
        result = self.runner.invoke(cli, ['configure', '--help'])
        assert result.exit_code == 0
        assert "configure" in result.output.lower()
        
        result = self.runner.invoke(cli, ['adapters', '--help'])
        assert result.exit_code == 0
        assert "adapters" in result.output.lower()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        # Should show version information