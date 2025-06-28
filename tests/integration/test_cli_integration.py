"""Integration tests for CLI functionality."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner


class TestCLIIntegration:
    """Integration tests for complete CLI workflows."""
    
    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_full_configure_and_tickets_workflow(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test complete workflow: configure -> tickets."""
        from zendesk_cli.cli.main import main
        
        config_path = temp_config_dir / "config.json"
        
        # Step 1: Configure the CLI
        with patch('keyring.set_password'):
            configure_result = runner.invoke(main, [
                'configure',
                '--domain', 'example.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token',
                '--config-path', str(config_path)
            ])
        
        assert configure_result.exit_code == 0
        assert "Configuration saved" in configure_result.output
        assert config_path.exists()
        
        # Step 2: Use the configuration to list tickets
        sample_tickets_response = {
            "tickets": [
                {
                    "id": 1,
                    "subject": "Test ticket",
                    "description": "Integration test ticket",
                    "status": "open",
                    "created_at": "2024-01-01T10:00:00Z",
                    "updated_at": "2024-01-01T10:00:00Z",
                    "assignee_id": 123,
                    "group_id": 456,
                    "url": "https://example.zendesk.com/tickets/1"
                }
            ]
        }
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.request') as mock_request:
            
            # Mock successful API responses
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = sample_tickets_response
            mock_request.return_value = mock_response
            
            tickets_result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert tickets_result.exit_code == 0
        assert "Test ticket" in tickets_result.output
        assert "Integration test ticket" in tickets_result.output
    
    def test_tickets_command_with_missing_config(self, runner: CliRunner) -> None:
        """Test tickets command when configuration is missing."""
        from zendesk_cli.cli.main import main
        
        # Try to run tickets without any configuration
        result = runner.invoke(main, ['tickets'])
        
        assert result.exit_code != 0
        assert "configuration" in result.output.lower()
    
    def test_configure_with_test_connection(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test configure command with connection testing."""
        from zendesk_cli.cli.main import main
        
        config_path = temp_config_dir / "config.json"
        
        with patch('keyring.set_password'), \
             patch('requests.request') as mock_request:
            
            # Mock successful authentication
            mock_response = Mock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user": {
                    "id": 123,
                    "name": "Test User",
                    "email": "test@example.com"
                }
            }
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'configure',
                '--domain', 'example.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token',
                '--config-path', str(config_path),
                '--test'
            ])
        
        assert result.exit_code == 0
        assert "Connection successful" in result.output
        assert "Test User" in result.output
    
    def test_tickets_assignee_only_integration(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test full workflow with --assignee-only flag."""
        from zendesk_cli.cli.main import main
        
        config_path = temp_config_dir / "config.json"
        
        # Create config file
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.request') as mock_request:
            
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'users/me.json' in url:
                    mock_response.json.return_value = {
                        "user": {"id": 123, "name": "Test User", "email": "test@example.com"}
                    }
                else:  # tickets endpoint
                    mock_response.json.return_value = {
                        "tickets": [
                            {
                                "id": 1,
                                "subject": "My ticket",
                                "description": "Assigned to me",
                                "status": "open",
                                "created_at": "2024-01-01T10:00:00Z",
                                "updated_at": "2024-01-01T10:00:00Z",
                                "assignee_id": 123,
                                "group_id": 456,
                                "url": "https://example.zendesk.com/tickets/1"
                            }
                        ]
                    }
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            result = runner.invoke(main, [
                'tickets',
                '--assignee-only',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code == 0
        assert "My ticket" in result.output
        
        # Verify the correct API calls were made
        assert mock_request.call_count == 2  # users/me + tickets with assignee filter
        
        # Check that assignee_id was passed in the tickets call
        tickets_call = [call for call in mock_request.call_args_list if 'tickets.json' in str(call)]
        assert len(tickets_call) == 1
        assert 'assignee_id=123' in str(tickets_call[0])
    
    def test_error_handling_integration(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test error handling in integrated workflows."""
        from zendesk_cli.cli.main import main
        
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='bad_token'), \
             patch('requests.request') as mock_request:
            
            # Mock authentication failure
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": "Unauthorized"}
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "Error" in result.output
    
    def test_help_integration(self, runner: CliRunner) -> None:
        """Test help command integration."""
        from zendesk_cli.cli.main import main
        
        # Test main help
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "tickets" in result.output
        assert "configure" in result.output
        
        # Test tickets help
        result = runner.invoke(main, ['tickets', '--help'])
        assert result.exit_code == 0
        assert "assignee-only" in result.output
        
        # Test configure help
        result = runner.invoke(main, ['configure', '--help'])
        assert result.exit_code == 0
        assert "domain" in result.output