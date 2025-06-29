#!/usr/bin/env python3
"""
TicketQ Automation Scripts Examples

This file contains practical automation examples using TicketQ for common
administrative and operational tasks.

Prerequisites:
- Install TicketQ: pip install "ticketq[cli]"
- Install adapter: pip install ticketq-zendesk
- Configure adapter: tq configure --adapter zendesk
- Optionally install schedule: pip install schedule
"""

import csv
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Any
import json
import logging

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("💡 Install 'schedule' package for automated scheduling: pip install schedule")

from ticketq import TicketQLibrary
from ticketq.lib.models import LibraryTicket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticketq_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TicketReporter:
    """Class for generating automated ticket reports."""
    
    def __init__(self, adapter_name: str = None):
        """Initialize the reporter with a specific adapter."""
        self.tq = TicketQLibrary.from_config(adapter_name=adapter_name)
        self.adapter_info = self.tq.get_adapter_info()
        logger.info(f"Initialized reporter with {self.adapter_info['display_name']} adapter")
    
    def generate_stale_tickets_report(self, days_threshold: int = 3) -> List[LibraryTicket]:
        """Generate report of tickets that haven't been updated in X days."""
        logger.info(f"Generating stale tickets report (threshold: {days_threshold} days)")
        
        # Get all open/pending tickets
        tickets = self.tq.get_tickets(
            status=["open", "pending"],
            sort_by="days_updated"
        )
        
        # Filter for stale tickets
        stale_tickets = [
            ticket for ticket in tickets 
            if ticket.days_since_updated >= days_threshold
        ]
        
        logger.info(f"Found {len(stale_tickets)} stale tickets (out of {len(tickets)} total)")
        return stale_tickets
    
    def generate_team_workload_report(self) -> Dict[str, Dict[str, Any]]:
        """Generate report showing ticket distribution by team."""
        logger.info("Generating team workload report")
        
        tickets = self.tq.get_tickets(status=["open", "pending"])
        
        # Group tickets by team
        team_stats = {}
        unassigned_count = 0
        
        for ticket in tickets:
            team_name = ticket.team_name or "Unassigned"
            
            if team_name == "Unassigned":
                unassigned_count += 1
                continue
                
            if team_name not in team_stats:
                team_stats[team_name] = {
                    "total": 0,
                    "open": 0,
                    "pending": 0,
                    "avg_age": 0,
                    "oldest_ticket": None
                }
            
            stats = team_stats[team_name]
            stats["total"] += 1
            
            if ticket.status.lower() == "open":
                stats["open"] += 1
            elif ticket.status.lower() == "pending":
                stats["pending"] += 1
            
            # Track oldest ticket
            if (stats["oldest_ticket"] is None or 
                ticket.days_since_created > stats["oldest_ticket"].days_since_created):
                stats["oldest_ticket"] = ticket
        
        # Calculate average ages
        for team_name, stats in team_stats.items():
            team_tickets = [t for t in tickets if t.team_name == team_name]
            if team_tickets:
                stats["avg_age"] = sum(t.days_since_created for t in team_tickets) / len(team_tickets)
        
        if unassigned_count > 0:
            team_stats["Unassigned"] = {"total": unassigned_count}
        
        logger.info(f"Generated workload report for {len(team_stats)} teams")
        return team_stats
    
    def generate_sla_breach_report(self, sla_days: int = 5) -> List[LibraryTicket]:
        """Generate report of tickets approaching or breaching SLA."""
        logger.info(f"Generating SLA breach report (SLA: {sla_days} days)")
        
        tickets = self.tq.get_tickets(status=["open", "pending"])
        
        # Categorize tickets
        breached = [t for t in tickets if t.days_since_created > sla_days]
        approaching = [t for t in tickets if sla_days - 1 <= t.days_since_created <= sla_days]
        
        logger.info(f"SLA Report: {len(breached)} breached, {len(approaching)} approaching")
        
        return {
            "breached": breached,
            "approaching": approaching,
            "sla_days": sla_days
        }


def daily_stale_tickets_report(export_dir: str = "reports"):
    """Daily automation: Export stale tickets to CSV."""
    logger.info("Starting daily stale tickets report")
    
    try:
        # Ensure reports directory exists
        Path(export_dir).mkdir(exist_ok=True)
        
        reporter = TicketReporter()
        stale_tickets = reporter.generate_stale_tickets_report(days_threshold=3)
        
        if stale_tickets:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            adapter_name = reporter.adapter_info['name']
            filename = f"{export_dir}/stale_tickets_{adapter_name}_{timestamp}.csv"
            
            # Export to CSV
            reporter.tq.export_to_csv(stale_tickets, filename)
            
            logger.info(f"✅ Exported {len(stale_tickets)} stale tickets to {filename}")
            
            # Generate summary
            summary = {
                "date": datetime.now().isoformat(),
                "adapter": adapter_name,
                "total_stale_tickets": len(stale_tickets),
                "stalest_ticket_id": stale_tickets[0].id if stale_tickets else None,
                "stalest_ticket_age": stale_tickets[0].days_since_updated if stale_tickets else None,
                "export_file": filename
            }
            
            return summary
        else:
            logger.info("✅ No stale tickets found - no report needed")
            return {"date": datetime.now().isoformat(), "total_stale_tickets": 0}
            
    except Exception as e:
        logger.error(f"❌ Daily stale tickets report failed: {e}")
        raise


def weekly_team_report(export_dir: str = "reports"):
    """Weekly automation: Generate comprehensive team workload report."""
    logger.info("Starting weekly team report")
    
    try:
        Path(export_dir).mkdir(exist_ok=True)
        
        reporter = TicketReporter()
        team_stats = reporter.generate_team_workload_report()
        
        # Generate report file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        adapter_name = reporter.adapter_info['name']
        report_file = f"{export_dir}/team_workload_{adapter_name}_{timestamp}.json"
        
        # Save detailed JSON report
        with open(report_file, 'w') as f:
            # Convert LibraryTicket objects to dicts for JSON serialization
            serializable_stats = {}
            for team, stats in team_stats.items():
                serializable_stats[team] = {
                    k: v.dict() if hasattr(v, 'dict') else v 
                    for k, v in stats.items() 
                    if k != 'oldest_ticket'
                }
                if 'oldest_ticket' in stats and stats['oldest_ticket']:
                    serializable_stats[team]['oldest_ticket_id'] = stats['oldest_ticket'].id
                    serializable_stats[team]['oldest_ticket_age'] = stats['oldest_ticket'].days_since_created
            
            json.dump(serializable_stats, f, indent=2, default=str)
        
        # Generate human-readable CSV summary
        csv_file = f"{export_dir}/team_summary_{adapter_name}_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Team", "Total Tickets", "Open", "Pending", "Avg Age (Days)", "Oldest Ticket ID"])
            
            for team, stats in team_stats.items():
                if "total" in stats:  # Skip incomplete entries
                    writer.writerow([
                        team,
                        stats.get("total", 0),
                        stats.get("open", 0),
                        stats.get("pending", 0),
                        f"{stats.get('avg_age', 0):.1f}",
                        stats.get("oldest_ticket").id if stats.get("oldest_ticket") else "N/A"
                    ])
        
        logger.info(f"✅ Weekly team report saved to {report_file} and {csv_file}")
        
        return {
            "date": datetime.now().isoformat(),
            "teams_analyzed": len(team_stats),
            "json_report": report_file,
            "csv_report": csv_file
        }
        
    except Exception as e:
        logger.error(f"❌ Weekly team report failed: {e}")
        raise


def sla_monitoring_alert(sla_days: int = 5, email_config: Dict[str, str] = None):
    """Monitor SLA breaches and send email alerts."""
    logger.info(f"Starting SLA monitoring (SLA: {sla_days} days)")
    
    try:
        reporter = TicketReporter()
        sla_report = reporter.generate_sla_breach_report(sla_days)
        
        breached = sla_report["breached"]
        approaching = sla_report["approaching"]
        
        if breached or approaching:
            # Generate alert message
            alert_message = f"""
SLA MONITORING ALERT - {reporter.adapter_info['display_name']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SLA BREACHED ({len(breached)} tickets):
"""
            for ticket in breached[:10]:  # Show top 10
                alert_message += f"  • #{ticket.id}: {ticket.title[:50]}... (Age: {ticket.days_since_created} days)\n"
            
            if len(breached) > 10:
                alert_message += f"  ... and {len(breached) - 10} more breached tickets\n"
            
            alert_message += f"""
APPROACHING SLA ({len(approaching)} tickets):
"""
            for ticket in approaching[:10]:  # Show top 10
                alert_message += f"  • #{ticket.id}: {ticket.title[:50]}... (Age: {ticket.days_since_created} days)\n"
            
            # Export detailed report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sla_file = f"reports/sla_breach_report_{timestamp}.csv"
            Path("reports").mkdir(exist_ok=True)
            
            all_risk_tickets = breached + approaching
            if all_risk_tickets:
                reporter.tq.export_to_csv(all_risk_tickets, sla_file)
                alert_message += f"\nDetailed report exported to: {sla_file}\n"
            
            logger.warning(f"SLA ALERT: {len(breached)} breached, {len(approaching)} approaching")
            
            # Send email if configured
            if email_config:
                send_email_alert(
                    subject=f"SLA Alert: {len(breached)} breached tickets",
                    body=alert_message,
                    attachment=sla_file if all_risk_tickets else None,
                    email_config=email_config
                )
            
            return {
                "alert_generated": True,
                "breached_count": len(breached),
                "approaching_count": len(approaching),
                "report_file": sla_file if all_risk_tickets else None
            }
        else:
            logger.info("✅ All tickets within SLA - no alerts needed")
            return {"alert_generated": False, "breached_count": 0, "approaching_count": 0}
            
    except Exception as e:
        logger.error(f"❌ SLA monitoring failed: {e}")
        raise


def send_email_alert(subject: str, body: str, attachment: str = None, email_config: Dict[str, str] = None):
    """Send email alert with optional CSV attachment."""
    if not email_config:
        logger.info("No email configuration provided - skipping email")
        return
    
    try:
        msg = MimeMultipart()
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'plain'))
        
        # Add attachment if provided
        if attachment and Path(attachment).exists():
            with open(attachment, "rb") as f:
                part = MimeBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment).name}'
                )
                msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(email_config['smtp_host'], email_config.get('smtp_port', 587))
        server.starttls()
        server.login(email_config['username'], email_config['password'])
        server.sendmail(email_config['from'], email_config['to'], msg.as_string())
        server.quit()
        
        logger.info(f"✅ Email alert sent to {email_config['to']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to send email alert: {e}")


def export_all_tickets_backup(export_dir: str = "backups"):
    """Create a complete backup export of all tickets."""
    logger.info("Starting complete ticket backup")
    
    try:
        Path(export_dir).mkdir(exist_ok=True)
        
        tq = TicketQLibrary.from_config()
        adapter_info = tq.get_adapter_info()
        
        # Get all tickets across all statuses
        all_statuses = ["new", "open", "pending", "hold", "solved", "closed"]
        all_tickets = []
        
        for status in all_statuses:
            try:
                status_tickets = tq.get_tickets(status=status)
                all_tickets.extend(status_tickets)
                logger.info(f"  {status}: {len(status_tickets)} tickets")
            except Exception as e:
                logger.warning(f"  Failed to get {status} tickets: {e}")
        
        if all_tickets:
            # Remove duplicates (in case of status overlaps)
            unique_tickets = {ticket.id: ticket for ticket in all_tickets}
            unique_tickets_list = list(unique_tickets.values())
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            adapter_name = adapter_info['name']
            backup_file = f"{export_dir}/complete_backup_{adapter_name}_{timestamp}.csv"
            
            # Export with full descriptions
            tq.export_to_csv(unique_tickets_list, backup_file, include_full_description=True)
            
            logger.info(f"✅ Complete backup created: {backup_file}")
            logger.info(f"   Total unique tickets: {len(unique_tickets_list)}")
            
            return {
                "backup_created": True,
                "total_tickets": len(unique_tickets_list),
                "backup_file": backup_file,
                "adapter": adapter_name
            }
        else:
            logger.warning("No tickets found for backup")
            return {"backup_created": False, "total_tickets": 0}
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        raise


def setup_scheduled_automation():
    """Set up scheduled automation tasks."""
    if not SCHEDULE_AVAILABLE:
        print("❌ 'schedule' package not installed. Install with: pip install schedule")
        return
    
    logger.info("Setting up scheduled automation tasks")
    
    # Schedule daily stale ticket reports at 9 AM
    schedule.every().day.at("09:00").do(daily_stale_tickets_report)
    
    # Schedule weekly team reports on Mondays at 8 AM
    schedule.every().monday.at("08:00").do(weekly_team_report)
    
    # Schedule SLA monitoring every 4 hours
    schedule.every(4).hours.do(sla_monitoring_alert, sla_days=5)
    
    # Schedule weekly backups on Sundays at 2 AM
    schedule.every().sunday.at("02:00").do(export_all_tickets_backup)
    
    logger.info("✅ Scheduled tasks configured:")
    logger.info("   • Daily stale tickets report: 9:00 AM")
    logger.info("   • Weekly team workload report: Mondays 8:00 AM")
    logger.info("   • SLA monitoring: Every 4 hours")
    logger.info("   • Weekly backup: Sundays 2:00 AM")
    
    return schedule


def run_scheduled_tasks():
    """Run the scheduled task loop."""
    if not SCHEDULE_AVAILABLE:
        print("❌ 'schedule' package not installed. Install with: pip install schedule")
        return
    
    scheduler = setup_scheduled_automation()
    
    logger.info("🤖 Starting automated scheduler...")
    logger.info("   Press Ctrl+C to stop")
    
    try:
        while True:
            scheduler.run_pending()
            import time
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("🛑 Automation scheduler stopped")


def main():
    """Demonstration of automation scripts."""
    print("🤖 TicketQ Automation Scripts Examples")
    print("=====================================")
    
    # Example email configuration (replace with your settings)
    email_config = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your_email@gmail.com",
        "password": "your_app_password",
        "from": "your_email@gmail.com",
        "to": "alerts@company.com"
    }
    
    try:
        print("\n1. 📊 Running daily stale tickets report...")
        stale_summary = daily_stale_tickets_report()
        print(f"   Result: {stale_summary}")
        
        print("\n2. 👥 Running weekly team workload report...")
        team_summary = weekly_team_report()
        print(f"   Result: {team_summary}")
        
        print("\n3. ⚠️  Running SLA monitoring...")
        # Note: Pass None for email_config to skip actual email sending in demo
        sla_summary = sla_monitoring_alert(sla_days=5, email_config=None)
        print(f"   Result: {sla_summary}")
        
        print("\n4. 💾 Creating complete backup...")
        backup_summary = export_all_tickets_backup()
        print(f"   Result: {backup_summary}")
        
        print("\n✅ All automation examples completed successfully!")
        print("\n💡 To run continuously with scheduling:")
        print("   1. Install schedule: pip install schedule")
        print("   2. Configure email settings in the script")
        print("   3. Run: python automation_scripts.py --schedule")
        
    except Exception as e:
        logger.error(f"❌ Automation example failed: {e}")
        print(f"Make sure you have configured TicketQ first: tq configure --adapter zendesk")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        run_scheduled_tasks()
    else:
        main()