"""Integration tests for CLI error handling."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner
import requests

from zendesk_cli.cli.main import main


class TestCLIErrorHandling:
    """Integration tests for CLI error handling across different scenarios."""
    
    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_missing_configuration_error(self, runner: CliRunner) -> None:
        """Test error handling when configuration is missing."""
        result = runner.invoke(main, ['tickets'])
        
        assert result.exit_code != 0
        assert "No configuration found" in result.output
        assert "zendesk configure" in result.output
    
    def test_network_error_handling_in_tickets(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test network error handling in tickets command."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            mock_request.side_effect = requests.exceptions.ConnectionError("Network unreachable")
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "🌐 Network error" in result.output
        assert "Check your internet connection" in result.output
        assert "Suggestions:" in result.output
    
    def test_timeout_error_handling_in_tickets(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test timeout error handling in tickets command."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "⏰ Request timed out" in result.output
        assert "connection speed" in result.output
    
    def test_rate_limit_error_handling_in_tickets(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test rate limit error handling in tickets command."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            # Mock consistent rate limiting (will exceed retry limit)
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_response.ok = False
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "⏳ Rate limited" in result.output
        assert "Please wait 60 seconds" in result.output
    
    def test_authentication_error_handling_in_tickets(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test authentication error handling in tickets command."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='invalid_token'), \
             patch('requests.Session.request') as mock_request:
            
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.reason = "Unauthorized"
            mock_response.ok = False
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "Authentication failed" in result.output
        assert "Check your API token" in result.output
        assert "zendesk configure" in result.output
    
    def test_keyring_error_handling_in_configure(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test keyring error handling in configure command."""
        with patch('keyring.set_password', side_effect=Exception("Keyring service unavailable")):
            result = runner.invoke(main, [
                'configure',
                '--domain', 'test.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token',
                '--config-path', str(temp_config_dir / "config.json")
            ])
        
        assert result.exit_code != 0
        assert "🔐 Credential storage error" in result.output
        assert "keyring service" in result.output
        assert "python3-keyring" in result.output
    
    def test_network_error_in_configure_test(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test network error during configure --test."""
        with patch('keyring.set_password'), \
             patch('requests.Session.request') as mock_request:
            
            mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            result = runner.invoke(main, [
                'configure',
                '--domain', 'test.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token',
                '--config-path', str(temp_config_dir / "config.json"),
                '--test'
            ])
        
        assert result.exit_code != 0
        assert "🌐 Connection test failed - Network error" in result.output
        assert "internet connection" in result.output
    
    def test_invalid_group_id_format_error(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test error handling for invalid group ID format."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        result = runner.invoke(main, [
            'tickets',
            '--group', 'invalid,not-a-number,123',
            '--config-path', str(config_path)
        ])
        
        assert result.exit_code != 0
        assert "Invalid group ID format" in result.output
        assert "comma-separated integers" in result.output
    
    def test_server_error_handling(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test handling of server errors (5xx)."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.reason = "Service Unavailable"
            mock_response.ok = False
            mock_response.json.return_value = {"error": "Service temporarily unavailable"}
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "Server error" in result.output
        assert "Service temporarily unavailable" in result.output
    
    def test_permission_error_handling(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test handling of permission errors (403)."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.reason = "Forbidden"
            mock_response.ok = False
            mock_response.json.return_value = {"error": "Insufficient permissions"}
            mock_request.return_value = mock_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "Access forbidden" in result.output
        assert "permission" in result.output
    
    def test_unexpected_error_handling(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test handling of unexpected errors."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('zendesk_cli.services.auth_service.AuthService.create_client_from_config') as mock_create:
            
            mock_create.side_effect = RuntimeError("Unexpected system error")
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code != 0
        assert "Unexpected error" in result.output
        assert "Please report this issue" in result.output
    
    def test_invalid_json_config_file(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test handling of corrupted configuration file."""
        config_path = temp_config_dir / "config.json"
        with open(config_path, 'w') as f:
            f.write("{invalid json content")
        
        result = runner.invoke(main, [
            'tickets',
            '--config-path', str(config_path)
        ])
        
        assert result.exit_code != 0
        assert "Error reading config file" in result.output
    
    def test_file_permission_error_in_configure(self, runner: CliRunner) -> None:
        """Test file permission error during configuration save."""
        with patch('keyring.set_password'), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            
            result = runner.invoke(main, [
                'configure',
                '--domain', 'test.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token'
            ])
        
        assert result.exit_code != 0
        assert "Failed to write configuration file" in result.output
    
    def test_graceful_degradation_with_groups_api_failure(self, runner: CliRunner, temp_config_dir: Path) -> None:
        """Test graceful degradation when groups API fails but tickets API succeeds."""
        config_path = temp_config_dir / "config.json"
        config_data = {"domain": "test.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token'), \
             patch('requests.Session.request') as mock_request:
            
            def mock_api_response(method, url, **kwargs):
                mock_response = Mock()
                
                if 'groups.json' in url:
                    # Groups API fails
                    mock_response.status_code = 500
                    mock_response.ok = False
                    mock_response.reason = "Internal Server Error"
                elif 'tickets.json' in url:
                    # Tickets API succeeds
                    mock_response.status_code = 200
                    mock_response.ok = True
                    mock_response.json.return_value = {
                        "tickets": [
                            {
                                "id": 1,
                                "subject": "Test ticket",
                                "description": "Test description",
                                "status": "open",
                                "created_at": "2024-01-01T10:00:00Z",
                                "updated_at": "2024-01-01T10:00:00Z",
                                "assignee_id": 123,
                                "group_id": 456,
                                "url": "https://test.zendesk.com/api/v2/tickets/1.json"
                            }
                        ]
                    }
                
                return mock_response
            
            mock_request.side_effect = mock_api_response
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        # Should succeed with fallback group names
        assert result.exit_code == 0
        assert "Test ticket" in result.output
        # Should show fallback group name since groups API failed
        assert "Group 456" in result.output or "456" in result.output