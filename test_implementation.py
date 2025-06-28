#!/usr/bin/env python3
"""Test script to verify Phase 1 and Phase 2 implementation.

This script tests the core models and Zendesk client functionality
without requiring actual Zendesk API access.
"""

import sys
from datetime import datetime
from typing import Dict, Any

def test_phase_1_models() -> bool:
    """Test Phase 1: Core Models implementation."""
    print("=" * 50)
    print("TESTING PHASE 1: Core Models")
    print("=" * 50)
    
    try:
        # Test 1: Import and create a Ticket
        print("✓ Testing Ticket model creation...")
        from src.zendesk_cli.models.ticket import Ticket
        
        ticket_data = {
            "id": 12345,
            "subject": "Test Support Ticket",
            "description": "This is a test ticket to verify our implementation works correctly",
            "status": "open",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-02T15:30:00Z",
            "assignee_id": 123,
            "group_id": 456,
            "url": "https://example.zendesk.com/tickets/12345"
        }
        
        ticket = Ticket(**ticket_data)
        assert ticket.id == 12345
        assert ticket.subject == "Test Support Ticket"
        assert ticket.status == "open"
        print(f"  ✓ Created ticket: {ticket.subject}")
        
        # Test 2: Test short_description property
        print("✓ Testing short_description property...")
        # The description is 76 characters, so should be truncated to 50 + "..."
        description = "This is a test ticket to verify our implementation works correctly"
        expected_short = description[:50] + "..."
        assert ticket.short_description == expected_short
        print(f"  ✓ Short description: {ticket.short_description}")
        
        # Test 3: Test date utilities
        print("✓ Testing date utilities...")
        from src.zendesk_cli.utils.date_utils import days_between, parse_zendesk_datetime
        
        date1 = datetime(2024, 1, 1)
        date2 = datetime(2024, 1, 5)
        days = days_between(date1, date2)
        assert days == 4
        print(f"  ✓ Days between calculation: {days} days")
        
        parsed_date = parse_zendesk_datetime("2024-01-01T10:00:00Z")
        assert parsed_date == datetime(2024, 1, 1, 10, 0, 0)
        print(f"  ✓ Zendesk datetime parsing: {parsed_date}")
        
        # Test 4: Test exception handling
        print("✓ Testing custom exceptions...")
        from src.zendesk_cli.models.exceptions import AuthenticationError, APIError
        
        auth_error = AuthenticationError("Invalid credentials")
        assert "Check your API token" in str(auth_error)
        print("  ✓ AuthenticationError includes helpful suggestions")
        
        api_error = APIError("Server error", status_code=500)
        assert api_error.status_code == 500
        print("  ✓ APIError stores status code correctly")
        
        print("\n🎉 PHASE 1 TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 1 TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase_2_client() -> bool:
    """Test Phase 2: Zendesk Client implementation."""
    print("\n" + "=" * 50)
    print("TESTING PHASE 2: Zendesk Client")
    print("=" * 50)
    
    try:
        # Test 1: Client initialization
        print("✓ Testing ZendeskClient initialization...")
        from src.zendesk_cli.services.zendesk_client import ZendeskClient
        
        client = ZendeskClient(
            domain="example.zendesk.com",
            email="test@example.com", 
            api_token="test_token_123"
        )
        
        assert client.domain == "example.zendesk.com"
        assert client.email == "test@example.com"
        assert client.base_url == "https://example.zendesk.com/api/v2"
        print(f"  ✓ Client initialized with domain: {client.domain}")
        print(f"  ✓ Base URL: {client.base_url}")
        
        # Test 2: Authentication headers
        print("✓ Testing authentication header generation...")
        auth_headers = client._get_auth_headers()
        
        assert "Authorization" in auth_headers
        assert auth_headers["Authorization"].startswith("Basic ")
        assert "Content-Type" in auth_headers
        print("  ✓ Authentication headers generated correctly")
        
        # Test 3: Test with mock data (no actual API call)
        print("✓ Testing ticket data processing...")
        sample_ticket_data = {
            "id": 1,
            "subject": "Sample ticket",
            "description": "Test description",
            "status": "open",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "url": "https://example.zendesk.com/tickets/1"
        }
        
        # Verify that we can create Ticket objects from API-like data
        from src.zendesk_cli.models.ticket import Ticket
        ticket = Ticket(**sample_ticket_data)
        assert ticket.id == 1
        print(f"  ✓ Processed ticket data: {ticket.subject}")
        
        print("\n🎉 PHASE 2 TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 2 TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_tests() -> None:
    """Run all implementation tests."""
    print("ZENDESK CLI - Phase 1 & 2 Implementation Test")
    print("=" * 60)
    
    # Add src to Python path so we can import our modules
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    phase1_success = test_phase_1_models()
    phase2_success = test_phase_2_client()
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION TEST SUMMARY")
    print("=" * 60)
    
    if phase1_success and phase2_success:
        print("✅ ALL TESTS PASSED!")
        print("\nPhase 1 (Core Models) and Phase 2 (Zendesk Client) are working correctly.")
        print("\nNext steps:")
        print("- Install dependencies: pip install -e '.[dev]'")
        print("- Run pytest: pytest tests/")
        print("- Continue with Phase 3 (Business Logic)")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nPlease check the error messages above and fix any issues.")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()