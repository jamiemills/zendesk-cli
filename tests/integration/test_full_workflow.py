"""End-to-end integration tests for complete CLI workflows."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner

from zendesk_cli.cli.main import main


class TestFullWorkflowIntegration:
    """Integration tests for complete end-to-end workflows."""
    
    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def complete_api_responses(self):
        """Complete set of API responses for full workflow testing."""
        return {
            "groups": {
                "groups": [
                    {"id": 456, "name": "Support Team", "description": "Customer support"},
                    {"id": 457, "name": "Engineering Team", "description": "Development"},
                    {"id": 458, "name": "Product Team", "description": "Product management"}
                ]
            },
            "user": {
                "user": {
                    "id": 123,
                    "name": "Test User",
                    "email": "test@example.com",
                    "group_ids": [456, 457]
                }
            },
            "tickets": {
                "tickets": [
                    {
                        "id": 1,
                        "subject": "Login authentication issue",
                        "description": "User cannot authenticate with SSO",
                        "status": "open",
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-03T15:30:00Z",
                        "assignee_id": 123,
                        "group_id": 456,
                        "url": "https://example.zendesk.com/api/v2/tickets/1.json"
                    },
                    {
                        "id": 2,
                        "subject": "Database performance degradation",
                        "description": "Queries running slower than usual",
                        "status": "open",
                        "created_at": "2024-01-02T14:00:00Z",
                        "updated_at": "2024-01-02T16:45:00Z",
                        "assignee_id": 124,
                        "group_id": 457,
                        "url": "https://example.zendesk.com/api/v2/tickets/2.json"
                    },
                    {
                        "id": 3,
                        "subject": "Feature request: Dark mode",
                        "description": "Users requesting dark mode option",
                        "status": "new",
                        "created_at": "2024-01-03T09:00:00Z",
                        "updated_at": "2024-01-03T09:00:00Z",
                        "assignee_id": None,
                        "group_id": 458,
                        "url": "https://example.zendesk.com/api/v2/tickets/3.json"
                    }
                ]
            },
            "search_assignee": {
                "results": [
                    {
                        "id": 1,
                        "subject": "Login authentication issue",
                        "description": "User cannot authenticate with SSO",
                        "status": "open",
                        "created_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-03T15:30:00Z",
                        "assignee_id": 123,
                        "group_id": 456,
                        "url": "https://example.zendesk.com/api/v2/tickets/1.json"
                    }
                ]
            }
        }
    
    def test_complete_configure_to_tickets_with_team_names(
        self, 
        runner: CliRunner, 
        temp_config_dir: Path,
        complete_api_responses: dict
    ) -> None:
        """Test complete workflow from configuration to listing tickets with team names."""
        config_path = temp_config_dir / "config.json"
        
        # Step 1: Configure the CLI
        with patch('keyring.set_password'):
            configure_result = runner.invoke(main, [
                'configure',
                '--domain', 'example.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token_123',
                '--config-path', str(config_path)
            ])
        
        assert configure_result.exit_code == 0
        assert "Configuration saved" in configure_result.output
        
        # Step 2: List all tickets with team names
        with patch('keyring.get_password', return_value='test_token_123'), \
             patch('requests.request') as mock_request:
            
            def api_response_handler(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = complete_api_responses["groups"]
                elif 'tickets.json' in url:
                    mock_response.json.return_value = complete_api_responses["tickets"]
                elif 'users/me.json' in url:
                    mock_response.json.return_value = complete_api_responses["user"]
                
                return mock_response
            
            mock_request.side_effect = api_response_handler
            
            tickets_result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert tickets_result.exit_code == 0
        
        # Verify team names appear in output
        assert "Support Team" in tickets_result.output
        assert "Engineering Team" in tickets_result.output
        assert "Product Team" in tickets_result.output
        
        # Verify ticket information
        assert "Login authentication issue" in tickets_result.output
        assert "Database performance degradation" in tickets_result.output
        assert "Feature request: Dark mode" in tickets_result.output
        
        # Verify table formatting
        assert "Ticket" in tickets_result.output
        assert "Team Name" in tickets_result.output
        assert "Description" in tickets_result.output
        assert "Days Open" in tickets_result.output
    
    def test_assignee_only_workflow_with_team_names(
        self,
        runner: CliRunner,
        temp_config_dir: Path,
        complete_api_responses: dict
    ) -> None:
        """Test workflow with --assignee-only flag showing team names."""
        config_path = temp_config_dir / "config.json"
        
        # Create config file
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token_123'), \
             patch('requests.request') as mock_request:
            
            def api_response_handler(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = complete_api_responses["groups"]
                elif 'users/me.json' in url:
                    mock_response.json.return_value = complete_api_responses["user"]
                elif 'search.json' in url:
                    # Return only tickets assigned to the user
                    mock_response.json.return_value = complete_api_responses["search_assignee"]
                
                return mock_response
            
            mock_request.side_effect = api_response_handler
            
            result = runner.invoke(main, [
                'tickets',
                '--assignee-only',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code == 0
        
        # Should only show tickets assigned to the user
        assert "Login authentication issue" in result.output
        assert "Support Team" in result.output
        
        # Should NOT show tickets assigned to others
        assert "Database performance degradation" not in result.output
        assert "Feature request: Dark mode" not in result.output
    
    def test_group_filter_workflow(
        self,
        runner: CliRunner,
        temp_config_dir: Path,
        complete_api_responses: dict
    ) -> None:
        """Test workflow with --group filter."""
        config_path = temp_config_dir / "config.json"
        
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Mock API responses for group filtering
        engineering_tickets = {
            "results": [ticket for ticket in complete_api_responses["tickets"]["tickets"] 
                       if ticket["group_id"] == 457]  # Engineering Team
        }
        
        with patch('keyring.get_password', return_value='test_token_123'), \
             patch('requests.request') as mock_request:
            
            def api_response_handler(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = complete_api_responses["groups"]
                elif 'search.json' in url:
                    mock_response.json.return_value = engineering_tickets
                
                return mock_response
            
            mock_request.side_effect = api_response_handler
            
            result = runner.invoke(main, [
                'tickets',
                '--group', 'Engineering Team',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code == 0
        
        # Should only show Engineering tickets
        assert "Database performance degradation" in result.output
        assert "Engineering Team" in result.output
        
        # Should NOT show other team tickets
        assert "Login authentication issue" not in result.output
        assert "Support Team" not in result.output
    
    def test_error_recovery_workflow(
        self,
        runner: CliRunner,
        temp_config_dir: Path,
        complete_api_responses: dict
    ) -> None:
        """Test error recovery in complete workflow."""
        config_path = temp_config_dir / "config.json"
        
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token_123'), \
             patch('requests.request') as mock_request:
            
            def api_response_handler(method, url, **kwargs):
                mock_response = Mock()
                
                if 'groups.json' in url:
                    # Groups API fails
                    mock_response.ok = False
                    mock_response.status_code = 500
                    mock_response.reason = "Internal Server Error"
                elif 'tickets.json' in url:
                    # Tickets API succeeds
                    mock_response.ok = True
                    mock_response.status_code = 200
                    mock_response.json.return_value = complete_api_responses["tickets"]
                
                return mock_response
            
            mock_request.side_effect = api_response_handler
            
            result = runner.invoke(main, [
                'tickets',
                '--config-path', str(config_path)
            ])
        
        # Should still succeed and show tickets with fallback group names
        assert result.exit_code == 0
        assert "Login authentication issue" in result.output
        assert "Group 456" in result.output  # Fallback group name
        assert "Group 457" in result.output  # Fallback group name
    
    def test_verbose_mode_workflow(
        self,
        runner: CliRunner,
        temp_config_dir: Path,
        complete_api_responses: dict
    ) -> None:
        """Test workflow with verbose logging enabled."""
        config_path = temp_config_dir / "config.json"
        
        config_data = {"domain": "example.zendesk.com", "email": "test@example.com"}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        with patch('keyring.get_password', return_value='test_token_123'), \
             patch('requests.request') as mock_request:
            
            def api_response_handler(method, url, **kwargs):
                mock_response = Mock()
                mock_response.ok = True
                mock_response.status_code = 200
                
                if 'groups.json' in url:
                    mock_response.json.return_value = complete_api_responses["groups"]
                elif 'tickets.json' in url:
                    mock_response.json.return_value = complete_api_responses["tickets"]
                
                return mock_response
            
            mock_request.side_effect = api_response_handler
            
            result = runner.invoke(main, [
                '--verbose',
                'tickets',
                '--config-path', str(config_path)
            ])
        
        assert result.exit_code == 0
        # Verbose mode shouldn't break functionality
        assert "Support Team" in result.output
        assert "Login authentication issue" in result.output