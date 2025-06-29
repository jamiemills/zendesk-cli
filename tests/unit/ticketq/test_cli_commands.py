"""Test TicketQ CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.ticketq.cli.commands.tickets import tickets
from src.ticketq.cli.commands.configure import configure
from src.ticketq.cli.commands.adapters import adapters


class TestTicketsCommand:
    """Test tickets CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_basic(self, mock_library_class):
        """Test basic tickets command."""
        # Mock library instance
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {
            "name": "test",
            "display_name": "Test Adapter"
        }
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, [])
        
        assert result.exit_code == 0
        assert "No open tickets found" in result.output
        mock_library.get_tickets.assert_called_once()

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_with_status_filter(self, mock_library_class):
        """Test tickets command with status filter."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {"name": "test", "display_name": "Test"}
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, ['--status', 'open,pending'])
        
        assert result.exit_code == 0
        mock_library.get_tickets.assert_called_once_with(
            status=['open', 'pending'],
            assignee_only=False,
            groups=None,
            sort_by=None,
            include_team_names=True
        )

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_assignee_only(self, mock_library_class):
        """Test tickets command with assignee-only filter."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {"name": "test", "display_name": "Test"}
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, ['--assignee-only'])
        
        assert result.exit_code == 0
        mock_library.get_tickets.assert_called_once_with(
            status=['open'],
            assignee_only=True,
            groups=None,
            sort_by=None,
            include_team_names=True
        )

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_with_groups(self, mock_library_class):
        """Test tickets command with group filter."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {"name": "test", "display_name": "Test"}
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, ['--group', 'Support Team,Engineering'])
        
        assert result.exit_code == 0
        mock_library.get_tickets.assert_called_once_with(
            status=['open'],
            assignee_only=False,
            groups=['Support Team', 'Engineering'],
            sort_by=None,
            include_team_names=True
        )

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_with_sorting(self, mock_library_class):
        """Test tickets command with sorting."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {"name": "test", "display_name": "Test"}
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, ['--sort-by', 'days_updated'])
        
        assert result.exit_code == 0
        mock_library.get_tickets.assert_called_once_with(
            status=['open'],
            assignee_only=False,
            groups=None,
            sort_by='days_updated',
            include_team_names=True
        )

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_with_csv_export(self, mock_library_class, tmp_path):
        """Test tickets command with CSV export."""
        from src.ticketq.lib.models import LibraryTicket
        
        # Create a mock ticket to export
        from datetime import datetime
        mock_ticket = LibraryTicket(
            id="123",
            title="Test ticket",
            description="Test description",
            status="open",
            assignee_id="test@example.com",
            group_id="123",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            url="https://test.com/123",
            team_name="Test Team",
            adapter_name="test"
        )
        
        mock_library = Mock()
        mock_library.get_tickets.return_value = [mock_ticket]
        mock_library.get_adapter_info.return_value = {"name": "test", "display_name": "Test"}
        mock_library_class.from_config.return_value = mock_library
        
        csv_file = tmp_path / "test.csv"
        result = self.runner.invoke(tickets, ['--csv', str(csv_file)])
        
        assert result.exit_code == 0
        mock_library.export_to_csv.assert_called_once_with([mock_ticket], str(csv_file))

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_configuration_error(self, mock_library_class):
        """Test tickets command with configuration error."""
        from src.ticketq.models.exceptions import ConfigurationError
        
        mock_library_class.from_config.side_effect = ConfigurationError(
            "No configuration found",
            suggestions=["Run 'tq configure' first"]
        )
        
        result = self.runner.invoke(tickets, [])
        
        assert result.exit_code == 1
        assert "Configuration error" in result.output
        assert "Run 'tq configure' first" in result.output

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_invalid_status(self, mock_library_class):
        """Test tickets command with invalid status."""
        result = self.runner.invoke(tickets, ['--status', 'invalid,open'])
        
        assert result.exit_code == 1
        assert "Invalid status" in result.output

    @patch('src.ticketq.cli.commands.tickets.TicketQLibrary')
    def test_tickets_adapter_override(self, mock_library_class):
        """Test tickets command with adapter override."""
        mock_library = Mock()
        mock_library.get_tickets.return_value = []
        mock_library.get_adapter_info.return_value = {"name": "zendesk", "display_name": "Zendesk"}
        mock_library_class.from_config.return_value = mock_library
        
        result = self.runner.invoke(tickets, ['--adapter', 'zendesk'])
        
        assert result.exit_code == 0
        from unittest.mock import ANY
        mock_library_class.from_config.assert_called_once_with(
            adapter_name='zendesk',
            config_path=None,
            progress_callback=ANY
        )


class TestConfigureCommand:
    """Test configure CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch('src.ticketq.cli.commands.configure.get_registry')
    def test_configure_list_adapters(self, mock_get_registry):
        """Test configure command with list-adapters flag."""
        mock_registry = Mock()
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.display_name = "Test Adapter"
        mock_adapter_instance.version = "1.0.0"
        mock_adapter_instance.supported_features = ["tickets", "users"]
        mock_adapter_class.return_value = mock_adapter_instance
        
        mock_registry.get_available_adapters.return_value = {"test": mock_adapter_class}
        mock_get_registry.return_value = mock_registry
        
        result = self.runner.invoke(configure, ['--list-adapters'])
        
        assert result.exit_code == 0
        assert "Available adapters" in result.output
        assert "test: Test Adapter v1.0.0" in result.output

    @patch('src.ticketq.cli.commands.configure.get_registry')
    def test_configure_no_adapters(self, mock_get_registry):
        """Test configure command when no adapters are available."""
        mock_registry = Mock()
        mock_registry.get_available_adapters.return_value = {}
        mock_get_registry.return_value = mock_registry
        
        result = self.runner.invoke(configure, [])
        
        assert result.exit_code == 1
        assert "No adapters available" in result.output

    @patch('src.ticketq.cli.commands.configure.get_registry')
    @patch('src.ticketq.cli.commands.configure.ConfigManager')
    @patch('src.ticketq.cli.commands.configure.prompt_for_config')
    def test_configure_single_adapter(self, mock_prompt, mock_config_manager_class, mock_get_registry):
        """Test configure command with single available adapter."""
        # Mock registry
        mock_registry = Mock()
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.get_config_schema.return_value = {"type": "object", "properties": {}}
        mock_adapter_instance.get_default_config.return_value = {}
        mock_adapter_instance.validate_config.return_value = True
        mock_adapter_class.return_value = mock_adapter_instance
        
        mock_registry.get_available_adapters.return_value = {"test": mock_adapter_class}
        mock_get_registry.return_value = mock_registry
        
        # Mock config manager
        from src.ticketq.models.exceptions import ConfigurationError
        mock_config_manager = Mock()
        mock_config_manager.get_adapter_config.side_effect = ConfigurationError("Not found")
        mock_config_manager_class.return_value = mock_config_manager
        
        # Mock prompt
        mock_prompt.return_value = {"domain": "test.com", "email": "test@test.com"}
        
        result = self.runner.invoke(configure, [])
        
        assert result.exit_code == 0
        assert "Using test adapter" in result.output
        mock_config_manager.save_adapter_config.assert_called_once()

    @patch('src.ticketq.cli.commands.configure.get_registry')
    @patch('src.ticketq.cli.commands.configure.test_adapter_connection')
    def test_configure_with_test(self, mock_test_connection, mock_get_registry):
        """Test configure command with connection test."""
        # Mock registry and adapter
        mock_registry = Mock()
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.get_config_schema.return_value = {"type": "object", "properties": {}}
        mock_adapter_instance.get_default_config.return_value = {}
        mock_adapter_instance.validate_config.return_value = True
        mock_adapter_class.return_value = mock_adapter_instance
        
        mock_registry.get_available_adapters.return_value = {"test": mock_adapter_class}
        mock_get_registry.return_value = mock_registry
        
        # Mock test connection
        mock_test_connection.return_value = True
        
        with patch('src.ticketq.cli.commands.configure.ConfigManager') as mock_config_manager_class, \
             patch('src.ticketq.cli.commands.configure.prompt_for_config') as mock_prompt:
            
            from src.ticketq.models.exceptions import ConfigurationError
            mock_config_manager = Mock()
            mock_config_manager.get_adapter_config.side_effect = ConfigurationError("Not found")
            mock_config_manager_class.return_value = mock_config_manager
            
            mock_prompt.return_value = {"domain": "test.com"}
            
            result = self.runner.invoke(configure, ['--test'])
            
            assert result.exit_code == 0
            assert "Configuration test successful" in result.output


class TestAdaptersCommand:
    """Test adapters CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_adapters_install_guide(self):
        """Test adapters command with install guide."""
        result = self.runner.invoke(adapters, ['--install-guide'])
        
        assert result.exit_code == 0
        assert "TicketQ Adapter Installation Guide" in result.output
        assert "pip install ticketq-zendesk" in result.output

    @patch('src.ticketq.cli.commands.adapters.get_registry')
    @patch('src.ticketq.cli.commands.adapters.ConfigManager')
    def test_adapters_no_adapters_installed(self, mock_config_manager_class, mock_get_registry):
        """Test adapters command when no adapters are installed."""
        mock_registry = Mock()
        mock_registry.get_available_adapters.return_value = {}
        mock_get_registry.return_value = mock_registry
        
        mock_config_manager = Mock()
        mock_config_manager_class.return_value = mock_config_manager
        
        result = self.runner.invoke(adapters, [])
        
        assert result.exit_code == 0
        assert "No adapters installed" in result.output
        assert "pip install ticketq-zendesk" in result.output

    @patch('src.ticketq.cli.commands.adapters.get_registry')
    @patch('src.ticketq.cli.commands.adapters.ConfigManager')
    def test_adapters_list_available(self, mock_config_manager_class, mock_get_registry):
        """Test adapters command listing available adapters."""
        # Mock registry
        mock_registry = Mock()
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.display_name = "Test Adapter"
        mock_adapter_instance.version = "1.0.0"
        mock_adapter_instance.supported_features = ["tickets", "users", "groups"]
        mock_adapter_instance.validate_config.return_value = True
        mock_adapter_class.return_value = mock_adapter_instance
        
        mock_registry.get_available_adapters.return_value = {"test": mock_adapter_class}
        mock_get_registry.return_value = mock_registry
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.get_adapter_config.return_value = {"domain": "test.com"}
        mock_config_manager_class.return_value = mock_config_manager
        
        result = self.runner.invoke(adapters, [])
        
        assert result.exit_code == 0
        assert "Available Adapters" in result.output
        assert "test" in result.output
        assert "Test Adapter" in result.output
        assert "✅ Configured" in result.output

    @patch('src.ticketq.cli.commands.adapters.get_registry')
    @patch('src.ticketq.cli.commands.adapters.ConfigManager')
    @patch('src.ticketq.cli.commands.adapters.get_factory')
    def test_adapters_with_test(self, mock_get_factory, mock_config_manager_class, mock_get_registry):
        """Test adapters command with connection test."""
        # Mock registry and adapter
        mock_registry = Mock()
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.display_name = "Test Adapter"
        mock_adapter_instance.version = "1.0.0"
        mock_adapter_instance.supported_features = ["tickets"]
        mock_adapter_instance.validate_config.return_value = True
        mock_adapter_class.return_value = mock_adapter_instance
        
        mock_registry.get_available_adapters.return_value = {"test": mock_adapter_class}
        mock_get_registry.return_value = mock_registry
        
        # Mock config manager
        mock_config_manager = Mock()
        mock_config_manager.get_adapter_config.return_value = {"domain": "test.com"}
        mock_config_manager_class.return_value = mock_config_manager
        
        # Mock factory and adapter with working connection
        mock_factory = Mock()
        mock_adapter = Mock()
        mock_adapter._client.test_connection.return_value = True
        mock_factory.create_adapter.return_value = mock_adapter
        mock_get_factory.return_value = mock_factory
        
        result = self.runner.invoke(adapters, ['--test'])
        
        assert result.exit_code == 0
        assert "✅ Working" in result.output