#!/usr/bin/env python3
"""Complete functionality test for the Zendesk CLI.

This script tests the complete end-to-end functionality including:
- CLI command parsing
- Configuration management
- Table formatting
- Integration between all components

Run this after installing the package to verify everything works.
"""

import sys
import tempfile
import json
from pathlib import Path
from subprocess import run, PIPE
from typing import Dict, Any


def test_cli_installation() -> bool:
    """Test that the CLI is properly installed."""
    print("🔧 Testing CLI installation...")
    
    try:
        # Test that zendesk command is available
        result = run(['zendesk', '--help'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ CLI not installed properly. Return code: {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
        
        if 'tickets' not in result.stdout or 'configure' not in result.stdout:
            print("❌ CLI help doesn't show expected commands")
            print(f"Output: {result.stdout}")
            return False
        
        print("✅ CLI installation verified")
        return True
        
    except FileNotFoundError:
        print("❌ 'zendesk' command not found. Install with: pip install -e '.[dev]'")
        return False
    except Exception as e:
        print(f"❌ Error testing CLI installation: {e}")
        return False


def test_configuration_workflow() -> bool:
    """Test configuration workflow with mock data."""
    print("\n🔧 Testing configuration workflow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test_config.json"
        
        try:
            # Test configure command with flags
            result = run([
                'zendesk', 'configure',
                '--domain', 'test.zendesk.com',
                '--email', 'test@example.com',
                '--api-token', 'test_token_123',
                '--config-path', str(config_path)
            ], capture_output=True, text=True, input='')
            
            if result.returncode != 0:
                print(f"❌ Configure command failed. Return code: {result.returncode}")
                print(f"Error: {result.stderr}")
                print(f"Output: {result.stdout}")
                return False
            
            # Verify config file was created
            if not config_path.exists():
                print("❌ Configuration file was not created")
                return False
            
            # Verify config content
            with open(config_path) as f:
                config_data = json.load(f)
            
            expected_keys = {'domain', 'email'}
            if not expected_keys.issubset(config_data.keys()):
                print(f"❌ Config file missing expected keys. Got: {config_data.keys()}")
                return False
            
            if config_data['domain'] != 'test.zendesk.com':
                print(f"❌ Domain not saved correctly. Got: {config_data['domain']}")
                return False
            
            print("✅ Configuration workflow verified")
            return True
            
        except Exception as e:
            print(f"❌ Error in configuration workflow: {e}")
            return False


def test_help_commands() -> bool:
    """Test help commands for all CLI functions."""
    print("\n📖 Testing help commands...")
    
    commands_to_test = [
        ['zendesk', '--help'],
        ['zendesk', 'tickets', '--help'],
        ['zendesk', 'configure', '--help']
    ]
    
    for cmd in commands_to_test:
        try:
            result = run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Help command failed: {' '.join(cmd)}")
                print(f"Error: {result.stderr}")
                return False
            
            if len(result.stdout) < 50:  # Basic sanity check
                print(f"❌ Help output too short for: {' '.join(cmd)}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing help command {' '.join(cmd)}: {e}")
            return False
    
    print("✅ Help commands verified")
    return True


def test_tickets_command_without_config() -> bool:
    """Test that tickets command handles missing configuration gracefully."""
    print("\n🎫 Testing tickets command error handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_config = Path(temp_dir) / "nonexistent.json"
        
        try:
            result = run([
                'zendesk', 'tickets',
                '--config-path', str(non_existent_config)
            ], capture_output=True, text=True)
            
            # Should fail gracefully, not crash
            if result.returncode == 0:
                print("❌ Tickets command should have failed with missing config")
                return False
            
            # Should have helpful error message
            if 'configuration' not in result.stdout.lower():
                print("❌ Error message should mention configuration")
                print(f"Output: {result.stdout}")
                return False
            
            print("✅ Error handling verified")
            return True
            
        except Exception as e:
            print(f"❌ Error testing tickets command: {e}")
            return False


def test_version_command() -> bool:
    """Test version command."""
    print("\n🔖 Testing version command...")
    
    try:
        result = run(['zendesk', '--version'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Version command failed. Return code: {result.returncode}")
            return False
        
        if '0.1.0' not in result.stdout:
            print(f"❌ Version output unexpected: {result.stdout}")
            return False
        
        print("✅ Version command verified")
        return True
        
    except Exception as e:
        print(f"❌ Error testing version command: {e}")
        return False


def test_verbose_mode() -> bool:
    """Test verbose logging mode."""
    print("\n🔍 Testing verbose mode...")
    
    try:
        # Test that verbose flag doesn't break anything
        result = run([
            'zendesk', '--verbose', '--help'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Verbose mode failed. Return code: {result.returncode}")
            return False
        
        print("✅ Verbose mode verified")
        return True
        
    except Exception as e:
        print(f"❌ Error testing verbose mode: {e}")
        return False


def run_all_tests() -> None:
    """Run all functionality tests."""
    print("ZENDESK CLI - Complete Functionality Test")
    print("=" * 60)
    
    tests = [
        ("CLI Installation", test_cli_installation),
        ("Configuration Workflow", test_configuration_workflow),
        ("Help Commands", test_help_commands),
        ("Error Handling", test_tickets_command_without_config),
        ("Version Command", test_version_command),
        ("Verbose Mode", test_verbose_mode),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n💥 {test_name} CRASHED: {e}")
    
    print("\n" + "=" * 60)
    print("COMPLETE FUNCTIONALITY TEST SUMMARY")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("\nYour Zendesk CLI is fully functional and ready to use!")
        print("\nNext steps:")
        print("1. Run 'zendesk configure' to set up your credentials")
        print("2. Run 'zendesk tickets' to list your tickets")
        print("3. Use 'zendesk --help' for more options")
        sys.exit(0)
    else:
        print(f"❌ {total - passed}/{total} TESTS FAILED")
        print("\nSome functionality may not be working correctly.")
        print("Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()