#!/usr/bin/env python3
"""
Example usage of zendesk-cli as a library.

This script demonstrates how to use the zendesk-cli package programmatically
in your own Python applications.
"""

import json
from datetime import datetime
from pathlib import Path

from zendesk_cli import ZendeskLibrary, LibraryTicket, ConfigurationError


def basic_usage_example():
    """Basic library usage example."""
    print("=== Basic Library Usage ===")
    
    # Method 1: Initialize with explicit credentials
    try:
        zd = ZendeskLibrary.from_credentials(
            domain="your-domain.zendesk.com",
            email="your-email@company.com",
            api_token="your-api-token"
        )
        print("✅ Initialized with credentials")
    except ConfigurationError as e:
        print(f"⚠️  Configuration error (expected with fake credentials): {e}")
        return
    
    # Method 2: Initialize from config file
    try:
        zd = ZendeskLibrary.from_config()
        print("✅ Initialized from config file")
    except ConfigurationError as e:
        print(f"⚠️  Config file not found (expected): {e}")
        return
    
    # Test connection
    try:
        if zd.test_connection():
            print("✅ Connection test successful")
    except Exception as e:
        print(f"⚠️  Connection test failed (expected): {e}")
        return
    
    # Get tickets with various filters
    try:
        # Get all open tickets
        tickets = zd.get_tickets(status="open")
        print(f"📋 Found {len(tickets)} open tickets")
        
        # Get tickets with multiple statuses
        tickets = zd.get_tickets(status=["open", "pending", "hold"])
        print(f"📋 Found {len(tickets)} tickets (open, pending, hold)")
        
        # Get only your assigned tickets
        tickets = zd.get_tickets(assignee_only=True)
        print(f"👤 Found {len(tickets)} tickets assigned to you")
        
        # Get tickets for specific teams
        tickets = zd.get_tickets(groups=["Support Team", "Engineering"])
        print(f"🏢 Found {len(tickets)} tickets for specified teams")
        
        # Get tickets with sorting
        tickets = zd.get_tickets(
            status=["open", "pending"],
            sort_by="days_updated",  # Most stale first
            include_team_names=True
        )
        print(f"📊 Found {len(tickets)} sorted tickets")
        
        # Export to CSV
        if tickets:
            csv_path = "example_tickets.csv"
            zd.export_to_csv(tickets, csv_path)
            print(f"💾 Exported tickets to {csv_path}")
            
    except Exception as e:
        print(f"⚠️  Ticket operations failed: {e}")


def flask_integration_example():
    """Example of integrating with a Flask web application."""
    print("\n=== Flask Integration Example ===")
    
    try:
        from flask import Flask, jsonify, request
        
        app = Flask(__name__)
        
        # Initialize Zendesk library (in real app, do this once)
        zd = ZendeskLibrary.from_config()
        
        @app.route('/api/tickets')
        def get_tickets_api():
            """API endpoint to get tickets."""
            # Get query parameters
            status = request.args.get('status', 'open')
            assignee_only = request.args.get('assignee_only', 'false').lower() == 'true'
            groups = request.args.get('groups')
            sort_by = request.args.get('sort_by')
            
            # Parse groups parameter
            group_list = groups.split(',') if groups else None
            
            try:
                tickets = zd.get_tickets(
                    status=status.split(','),
                    assignee_only=assignee_only,
                    groups=group_list,
                    sort_by=sort_by
                )
                
                # Convert to JSON-serializable format
                ticket_data = [ticket.dict() for ticket in tickets]
                
                return jsonify({
                    'success': True,
                    'count': len(tickets),
                    'tickets': ticket_data
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/export')
        def export_tickets_api():
            """API endpoint to export tickets to CSV."""
            try:
                tickets = zd.get_tickets()
                csv_path = f"exports/tickets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                # Ensure export directory exists
                Path(csv_path).parent.mkdir(exist_ok=True)
                
                zd.export_to_csv(tickets, csv_path)
                
                return jsonify({
                    'success': True,
                    'file_path': csv_path,
                    'ticket_count': len(tickets)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        print("🌐 Flask routes defined:")
        print("  GET /api/tickets?status=open&assignee_only=true")
        print("  GET /api/export")
        
    except ImportError:
        print("⚠️  Flask not installed - skipping Flask example")
    except Exception as e:
        print(f"⚠️  Flask example setup failed: {e}")


def automated_reporting_example():
    """Example of automated ticket reporting."""
    print("\n=== Automated Reporting Example ===")
    
    try:
        # Initialize library
        zd = ZendeskLibrary.from_config()
        
        # Generate daily stale tickets report
        def daily_stale_tickets_report():
            """Generate report of stale tickets."""
            print("📊 Generating daily stale tickets report...")
            
            # Get tickets that haven't been updated in 3+ days
            all_tickets = zd.get_tickets(status=["open", "pending"])
            stale_tickets = [
                ticket for ticket in all_tickets 
                if ticket.days_since_updated >= 3
            ]
            
            # Sort by staleness (most stale first)
            stale_tickets.sort(key=lambda t: t.days_since_updated, reverse=True)
            
            # Export to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"reports/stale_tickets_{timestamp}.csv"
            
            # Ensure reports directory exists
            Path(csv_path).parent.mkdir(exist_ok=True)
            
            zd.export_to_csv(stale_tickets, csv_path)
            
            # Generate summary
            summary = {
                'total_stale_tickets': len(stale_tickets),
                'most_stale_days': stale_tickets[0].days_since_updated if stale_tickets else 0,
                'teams_affected': len(set(t.team_name for t in stale_tickets if t.team_name)),
                'report_path': str(csv_path)
            }
            
            # Save summary as JSON
            summary_path = f"reports/stale_summary_{timestamp}.json"
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"📋 Found {len(stale_tickets)} stale tickets")
            print(f"💾 Report saved to {csv_path}")
            print(f"📄 Summary saved to {summary_path}")
            
            return summary
        
        # Generate team workload report
        def team_workload_report():
            """Generate report of ticket distribution by team."""
            print("👥 Generating team workload report...")
            
            tickets = zd.get_tickets(status=["open", "pending"])
            
            # Group by team
            team_workload = {}
            for ticket in tickets:
                team = ticket.team_name or "Unassigned"
                if team not in team_workload:
                    team_workload[team] = {
                        'total_tickets': 0,
                        'avg_age_days': 0,
                        'oldest_ticket_days': 0
                    }
                
                team_workload[team]['total_tickets'] += 1
                team_workload[team]['oldest_ticket_days'] = max(
                    team_workload[team]['oldest_ticket_days'],
                    ticket.days_since_created
                )
            
            # Calculate averages
            for team, data in team_workload.items():
                team_tickets = [t for t in tickets if (t.team_name or "Unassigned") == team]
                if team_tickets:
                    data['avg_age_days'] = sum(t.days_since_created for t in team_tickets) // len(team_tickets)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"reports/team_workload_{timestamp}.json"
            
            Path(report_path).parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(team_workload, f, indent=2)
            
            print(f"👥 Analyzed {len(team_workload)} teams")
            print(f"📄 Report saved to {report_path}")
            
            return team_workload
        
        # Run reports (would normally be scheduled)
        print("🔄 Running automated reports...")
        # daily_stale_tickets_report()
        # team_workload_report()
        print("✅ Reports would be generated here")
        
    except Exception as e:
        print(f"⚠️  Reporting example failed: {e}")


def progress_callback_example():
    """Example using progress callbacks for long operations."""
    print("\n=== Progress Callback Example ===")
    
    progress_log = []
    
    def progress_callback(message):
        """Callback to track progress."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        progress_log.append(log_entry)
        print(f"🔄 {log_entry}")
    
    try:
        # Initialize with progress callback
        zd = ZendeskLibrary.from_credentials(
            domain="test.zendesk.com",
            email="test@example.com",
            api_token="fake_token",
            progress_callback=progress_callback
        )
        
        # Operations will now report progress
        # tickets = zd.get_tickets(status=["open", "pending", "hold"])
        print("✅ Progress callback configured")
        
    except Exception as e:
        print(f"⚠️  Progress example failed: {e}")


def error_handling_example():
    """Example of comprehensive error handling."""
    print("\n=== Error Handling Example ===")
    
    from zendesk_cli import (
        AuthenticationError,
        APIError,
        NetworkError,
        ConfigurationError
    )
    
    try:
        # This will fail with fake credentials
        zd = ZendeskLibrary.from_credentials(
            domain="fake.zendesk.com",
            email="fake@example.com",
            api_token="fake_token"
        )
        
        tickets = zd.get_tickets()
        
    except AuthenticationError as e:
        print(f"🔑 Authentication failed: {e}")
        print("   → Check your email and API token")
        
    except NetworkError as e:
        print(f"🌐 Network error: {e}")
        print("   → Check your internet connection and domain")
        
    except APIError as e:
        print(f"🔧 API error: {e}")
        print("   → Check Zendesk service status")
        
    except ConfigurationError as e:
        print(f"⚙️  Configuration error: {e}")
        print("   → Run configuration setup")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   → Contact support")


if __name__ == "__main__":
    print("🎯 Zendesk CLI Library Usage Examples\n")
    
    # Note: These examples use fake credentials and will show expected errors
    basic_usage_example()
    flask_integration_example()
    automated_reporting_example()
    progress_callback_example()
    error_handling_example()
    
    print("\n✨ Examples complete!")
    print("\nTo use with real data:")
    print("1. Configure your credentials: zendesk configure")
    print("2. Replace fake credentials in examples with real ones")
    print("3. Run the examples with your Zendesk instance")