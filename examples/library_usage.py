#!/usr/bin/env python3
"""
TicketQ Library Usage Examples

This file demonstrates how to use TicketQ as a Python library for programmatic
access to ticketing systems across different platforms.

Prerequisites:
- Install TicketQ: pip install "ticketq[cli]"
- Install adapter: pip install ticketq-zendesk
- Configure adapter: tq configure --adapter zendesk
"""

from datetime import datetime
from typing import List
import logging

from ticketq import TicketQLibrary
from ticketq.lib.models import LibraryTicket
from ticketq.models.exceptions import (
    AuthenticationError,
    NetworkError,
    ConfigurationError,
    PluginError,
    TicketQError
)

# Configure logging to see progress messages
logging.basicConfig(level=logging.INFO)


def basic_usage():
    """Basic library usage example."""
    print("=" * 60)
    print("BASIC LIBRARY USAGE")
    print("=" * 60)
    
    try:
        # Initialize with auto-detected adapter
        print("🔌 Initializing TicketQ library...")
        tq = TicketQLibrary.from_config()
        
        # Get adapter information
        adapter_info = tq.get_adapter_info()
        print(f"✅ Using {adapter_info['display_name']} adapter v{adapter_info['version']}")
        
        # Test connection
        print("🔍 Testing connection...")
        if tq.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
        
        # Get current user
        user = tq.get_current_user()
        if user:
            print(f"👤 Authenticated as: {user.name} ({user.email})")
        
        # Get basic ticket list
        print("\n📋 Fetching open tickets...")
        tickets = tq.get_tickets(status="open")
        print(f"Found {len(tickets)} open tickets")
        
        # Display first few tickets
        for i, ticket in enumerate(tickets[:3]):
            print(f"  #{ticket.id}: {ticket.title[:50]}...")
            print(f"    Status: {ticket.status}, Team: {ticket.team_name or 'Unassigned'}")
            print(f"    Age: {ticket.days_since_created} days")
        
        if len(tickets) > 3:
            print(f"  ... and {len(tickets) - 3} more tickets")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def advanced_filtering():
    """Advanced filtering and sorting examples."""
    print("\n" + "=" * 60)
    print("ADVANCED FILTERING & SORTING")
    print("=" * 60)
    
    try:
        tq = TicketQLibrary.from_config()
        
        # Multiple status filtering
        print("🔍 Getting tickets with multiple statuses...")
        tickets = tq.get_tickets(status=["open", "pending"])
        print(f"Found {len(tickets)} open/pending tickets")
        
        # Assignee-only filtering
        print("\n🔍 Getting your assigned tickets...")
        my_tickets = tq.get_tickets(assignee_only=True)
        print(f"Found {len(my_tickets)} tickets assigned to you")
        
        # Group/team filtering
        print("\n🔍 Getting tickets by team...")
        groups = tq.get_groups()
        if groups:
            first_group = groups[0]
            print(f"Filtering by team: {first_group.name}")
            team_tickets = tq.get_tickets(groups=[first_group.name])
            print(f"Found {len(team_tickets)} tickets for {first_group.name}")
        
        # Sorting examples
        print("\n📊 Sorting examples...")
        
        # Sort by staleness (most urgent first)
        stale_tickets = tq.get_tickets(
            status=["open", "pending"],
            sort_by="days_updated"
        )
        print(f"Tickets sorted by staleness: {len(stale_tickets)}")
        if stale_tickets:
            stalest = stale_tickets[0]
            print(f"  Most stale: #{stalest.id} ({stalest.days_since_updated} days since update)")
        
        # Sort by creation date (newest first)
        recent_tickets = tq.get_tickets(sort_by="created_at")
        print(f"Tickets sorted by creation date: {len(recent_tickets)}")
        if recent_tickets:
            newest = recent_tickets[0]
            print(f"  Newest: #{newest.id} (created {newest.days_since_created} days ago)")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def search_functionality():
    """Search functionality example."""
    print("\n" + "=" * 60)
    print("SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    try:
        tq = TicketQLibrary.from_config()
        
        # Search for tickets (adapter-specific query format)
        print("🔍 Searching tickets...")
        
        # Note: Search query format depends on the adapter
        # For Zendesk: can use Zendesk search syntax
        # For Jira: would use JQL syntax
        # For ServiceNow: would use ServiceNow query syntax
        
        adapter_info = tq.get_adapter_info()
        if adapter_info['name'] == 'zendesk':
            # Example Zendesk search
            search_results = tq.search_tickets("type:ticket status:open")
            print(f"Found {len(search_results)} tickets from search")
            
            # Display search results
            for ticket in search_results[:3]:
                print(f"  #{ticket.id}: {ticket.title[:50]}...")
        else:
            print(f"Search syntax for {adapter_info['name']} adapter not shown in this example")
            
    except Exception as e:
        print(f"❌ Search error: {e}")


def csv_export_examples():
    """CSV export functionality examples."""
    print("\n" + "=" * 60)
    print("CSV EXPORT EXAMPLES")
    print("=" * 60)
    
    try:
        tq = TicketQLibrary.from_config()
        
        # Get tickets for export
        tickets = tq.get_tickets(status=["open", "pending"], sort_by="days_updated")
        
        if not tickets:
            print("No tickets found for export")
            return
        
        print(f"📊 Exporting {len(tickets)} tickets...")
        
        # Basic export with full descriptions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"tickets_export_{timestamp}.csv"
        
        tq.export_to_csv(tickets, csv_file, include_full_description=True)
        print(f"✅ Full export saved to: {csv_file}")
        
        # Export with truncated descriptions (faster processing)
        csv_file_short = f"tickets_summary_{timestamp}.csv"
        tq.export_to_csv(tickets, csv_file_short, include_full_description=False)
        print(f"✅ Summary export saved to: {csv_file_short}")
        
        print(f"\n📋 Export includes these columns:")
        print("  • Ticket ID, Title, Status, Team Name")
        print("  • Description (full or truncated)")
        print("  • Created/Updated dates and age calculations")
        print("  • Direct link to ticket in source system")
        print("  • Adapter name for multi-system exports")
        
    except Exception as e:
        print(f"❌ Export error: {e}")


def error_handling_examples():
    """Comprehensive error handling examples."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 60)
    
    # Example 1: Configuration errors
    print("🧪 Testing configuration error handling...")
    try:
        # Try to use non-existent adapter
        tq = TicketQLibrary.from_config(adapter_name="nonexistent")
    except ConfigurationError as e:
        print(f"✅ Caught ConfigurationError: {e.message}")
        if e.suggestions:
            print("   Suggestions:", ", ".join(e.suggestions[:2]))
    except PluginError as e:
        print(f"✅ Caught PluginError: {e.message}")
        
    # Example 2: Connection testing with error handling
    print("\n🧪 Testing connection error handling...")
    try:
        tq = TicketQLibrary.from_config()
        
        # Test various operations with error handling
        tickets = tq.get_tickets()
        print(f"✅ Successfully retrieved {len(tickets)} tickets")
        
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e.message}")
        print("   💡 Tip: Check your API credentials with 'tq configure --test'")
        
    except NetworkError as e:
        print(f"❌ Network error: {e.message}")
        print("   💡 Tip: Check your internet connection and firewall settings")
        
    except TicketQError as e:
        print(f"❌ TicketQ error: {e.message}")
        if e.suggestions:
            print("   Suggestions:")
            for suggestion in e.suggestions:
                print(f"     • {suggestion}")
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def progress_callback_example():
    """Progress callback functionality example."""
    print("\n" + "=" * 60)
    print("PROGRESS CALLBACK EXAMPLE")
    print("=" * 60)
    
    def progress_callback(message: str) -> None:
        """Custom progress callback with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 📊 {message}")
    
    try:
        # Initialize with progress callback
        tq = TicketQLibrary.from_config(progress_callback=progress_callback)
        
        print("🔄 Operations will now show progress...")
        
        # Operations will show progress via callback
        tickets = tq.get_tickets(status=["open", "pending"])
        
        if tickets:
            # Export will also show progress
            tq.export_to_csv(tickets[:5], "progress_example.csv")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def multi_adapter_example():
    """Example of using multiple adapters (when available)."""
    print("\n" + "=" * 60)
    print("MULTI-ADAPTER EXAMPLE")
    print("=" * 60)
    
    # This example shows how you would work with multiple adapters
    # when additional adapter packages are installed
    
    adapters_to_try = ["zendesk", "jira", "servicenow"]
    all_tickets: List[LibraryTicket] = []
    
    for adapter_name in adapters_to_try:
        try:
            print(f"🔌 Trying {adapter_name} adapter...")
            tq = TicketQLibrary.from_config(adapter_name=adapter_name)
            
            adapter_info = tq.get_adapter_info()
            print(f"✅ Connected to {adapter_info['display_name']}")
            
            # Get tickets from this adapter
            tickets = tq.get_tickets(status="open")
            print(f"   Found {len(tickets)} open tickets")
            
            # Add to combined list
            all_tickets.extend(tickets)
            
        except (ConfigurationError, PluginError):
            print(f"⏭️  {adapter_name} adapter not configured or not installed")
        except Exception as e:
            print(f"❌ Error with {adapter_name}: {e}")
    
    if all_tickets:
        print(f"\n📊 Total tickets across all systems: {len(all_tickets)}")
        
        # Group by adapter
        by_adapter = {}
        for ticket in all_tickets:
            adapter = ticket.adapter_name
            if adapter not in by_adapter:
                by_adapter[adapter] = []
            by_adapter[adapter].append(ticket)
        
        for adapter, tickets in by_adapter.items():
            print(f"   {adapter}: {len(tickets)} tickets")
            
        # Export combined results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_export = f"all_systems_tickets_{timestamp}.csv"
        
        # Use any adapter for export (they all have the same export method)
        if all_tickets:
            tq = TicketQLibrary.from_config()
            tq.export_to_csv(all_tickets, combined_export)
            print(f"✅ Combined export saved to: {combined_export}")
    else:
        print("ℹ️  No tickets found across any configured adapters")


def main():
    """Run all examples."""
    print("🎫 TicketQ Library Usage Examples")
    print("=================================")
    print("This script demonstrates various ways to use TicketQ as a Python library.")
    print("Make sure you have configured at least one adapter before running!")
    print()
    
    try:
        # Run all examples
        basic_usage()
        advanced_filtering()
        search_functionality()
        csv_export_examples()
        progress_callback_example()
        multi_adapter_example()
        error_handling_examples()
        
        print("\n" + "=" * 60)
        print("✅ ALL EXAMPLES COMPLETED")
        print("=" * 60)
        print("💡 Next steps:")
        print("   • Modify these examples for your specific use case")
        print("   • Integrate TicketQ into your automation scripts")
        print("   • Build web applications using the library API")
        print("   • Check the README.md for more documentation")
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        print("💡 Make sure you have:")
        print("   1. Installed TicketQ: pip install 'ticketq[cli]'")
        print("   2. Installed an adapter: pip install ticketq-zendesk")
        print("   3. Configured the adapter: tq configure --adapter zendesk")


if __name__ == "__main__":
    main()