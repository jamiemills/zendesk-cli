#!/usr/bin/env python3
"""Test script to verify implementation works with real Zendesk API.

Set environment variables:
export ZENDESK_DOMAIN="your-company.zendesk.com"
export ZENDESK_EMAIL="your-email@company.com" 
export ZENDESK_API_TOKEN="your-api-token"

Then run: python test_real_api.py
"""

import os
import sys
from typing import Optional

def get_zendesk_config() -> Optional[dict]:
    """Get Zendesk configuration from environment variables."""
    domain = os.environ.get('ZENDESK_DOMAIN')
    email = os.environ.get('ZENDESK_EMAIL')
    api_token = os.environ.get('ZENDESK_API_TOKEN')
    
    if not all([domain, email, api_token]):
        print("❌ Missing required environment variables:")
        print("   ZENDESK_DOMAIN (e.g., 'company.zendesk.com')")
        print("   ZENDESK_EMAIL (your email)")
        print("   ZENDESK_API_TOKEN (your API token)")
        print("\nSet them like:")
        print('   export ZENDESK_DOMAIN="your-company.zendesk.com"')
        print('   export ZENDESK_EMAIL="your-email@company.com"')
        print('   export ZENDESK_API_TOKEN="your-api-token"')
        return None
    
    return {
        'domain': domain,
        'email': email,
        'api_token': api_token
    }

def test_real_zendesk_api():
    """Test against real Zendesk API."""
    print("ZENDESK CLI - Real API Integration Test")
    print("=" * 50)
    
    # Add src to Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    config = get_zendesk_config()
    if not config:
        return False
    
    try:
        print(f"✓ Connecting to: {config['domain']}")
        print(f"✓ Using email: {config['email']}")
        
        # Test 1: Initialize client
        from src.zendesk_cli.services.zendesk_client import ZendeskClient
        client = ZendeskClient(**config)
        print("✓ ZendeskClient initialized")
        
        # Test 2: Get current user (authentication test)
        print("\n--- Testing Authentication ---")
        user_data = client.get_current_user()
        print(f"✅ Authentication successful!")
        print(f"   User: {user_data.get('name')} ({user_data.get('email')})")
        print(f"   User ID: {user_data.get('id')}")
        
        # Test 3: Get tickets
        print("\n--- Testing Ticket Retrieval ---")
        tickets = client.get_tickets()
        print(f"✅ Retrieved {len(tickets)} tickets")
        
        if tickets:
            print("\nFirst few tickets:")
            for i, ticket in enumerate(tickets[:3]):
                print(f"  {i+1}. #{ticket.id} - {ticket.subject[:50]}")
                print(f"     Status: {ticket.status} | Created: {ticket.created_at.strftime('%Y-%m-%d')}")
                print(f"     Days old: {ticket.days_since_created}")
        else:
            print("   No tickets found (this might be normal)")
        
        # Test 4: Test with filters (get current user's tickets)
        print("\n--- Testing Filtered Ticket Retrieval ---")
        user_id = user_data.get('id')
        if user_id:
            user_tickets = client.get_tickets(assignee_id=user_id)
            print(f"✅ Retrieved {len(user_tickets)} tickets assigned to you")
            
            if user_tickets:
                print("Your tickets:")
                for ticket in user_tickets[:5]:
                    print(f"  • #{ticket.id} - {ticket.subject[:40]}...")
        
        print("\n" + "=" * 50)
        print("🎉 ALL REAL API TESTS PASSED!")
        print("Your Zendesk CLI implementation is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Real API test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide helpful error messages
        if "authentication failed" in str(e).lower():
            print("\n💡 Troubleshooting:")
            print("   - Double-check your API token")
            print("   - Verify your email address")
            print("   - Make sure API access is enabled in Zendesk")
        elif "network error" in str(e).lower():
            print("\n💡 Troubleshooting:")
            print("   - Check your internet connection")
            print("   - Verify the Zendesk domain is correct")
        
        return False

if __name__ == "__main__":
    success = test_real_zendesk_api()
    sys.exit(0 if success else 1)