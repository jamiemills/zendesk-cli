# Zendesk CLI

A powerful command-line utility and Python library for managing Zendesk tickets. Use it as a CLI tool for terminal-based ticket management, or integrate it into your Python applications as a library.

## Core Concepts

**Zendesk CLI** connects to your Zendesk instance via API to provide a fast, terminal-based interface for ticket management. It uses secure credential storage and provides rich filtering, sorting, and export capabilities.

**Key Benefits:**
- 🚀 **Fast ticket overview** - See all your tickets at a glance
- 🎯 **Smart filtering** - Filter by assignee, groups, status, or combinations
- 📊 **Flexible sorting** - Sort by any column for better organization  
- 💾 **CSV export** - Export filtered results with full descriptions
- 🔒 **Secure** - API tokens stored safely in system keyring
- 🎨 **Beautiful output** - Rich terminal tables with color coding
- 📦 **Library ready** - Use programmatically in your Python applications
- 🔧 **Flexible installation** - CLI-only or library-only installation options

## Installation

### As CLI Tool (Full Installation)

```bash
# Install directly from GitHub with CLI dependencies
pip install "git+https://github.com/jamiemills/zendesk-cli.git[cli]"

# Or clone and install locally
git clone https://github.com/jamiemills/zendesk-cli.git
cd zendesk-cli
pip install -e ".[cli]"
```

### As Library Only

```bash
# Install core library without CLI dependencies
pip install git+https://github.com/jamiemills/zendesk-cli.git

# Or locally
pip install -e .
```

### For Development

```bash
# Clone and install with all dependencies
git clone https://github.com/jamiemills/zendesk-cli.git
cd zendesk-cli
pip install -e ".[cli,dev]"
```

## Quick Start

### 1. Configure Zendesk credentials

```bash
zendesk configure
```

You'll be prompted for:
- **Zendesk domain** (e.g., `company.zendesk.com`)
- **Email address** (your Zendesk account email)  
- **API token** ([generate from Zendesk](https://developer.zendesk.com/api-reference/introduction/security-and-auth/#api-token))

### 2. List tickets

```bash
# List all open tickets
zendesk tickets

# List only your assigned tickets
zendesk tickets --assignee-only

# List tickets by team/group
zendesk tickets --group "Support Team"
```

## Complete Feature List

### ✅ Core Features
- **Multi-status filtering** - Filter by single or multiple statuses (`--status "open,pending"`)
- **Team/group filtering** - Filter by team names or IDs (`--group "Support Team,Engineering"`)
- **Assignee filtering** - Show only tickets assigned to you (`--assignee-only`)
- **Column sorting** - Sort by any column (`--sort-by days-updated`)
- **CSV export** - Export results with full descriptions (`--csv tickets.csv`)
- **Team name resolution** - Shows actual team names instead of group IDs
- **Secure credential storage** - API tokens stored in system keyring
- **Rich terminal output** - Beautiful colored tables with proper formatting

### ✅ Filtering Options
- **By Status**: `new`, `open`, `pending`, `hold`, `solved`, `closed`
- **By Assignment**: Personal tickets, team tickets, or all tickets
- **By Groups**: Single team, multiple teams, or group IDs
- **Multiple Status**: Combine statuses like `"hold,closed"` for OR logic

### ✅ Sorting Options
- **ticket** - Sort by ticket number
- **status** - Sort by ticket status
- **team** - Sort by team/group name  
- **description** - Sort by description text
- **opened** - Sort by creation date (newest first)
- **days-opened** - Sort by age since creation
- **updated** - Sort by last update date (newest first)
- **days-updated** - Sort by staleness since last update

### ✅ Export Features
- **CSV export** with full ticket descriptions (not truncated)
- **Proper escaping** of commas and special characters
- **All columns included** matching table display format
- **UTF-8 encoding** for international character support

## Command Reference

### `zendesk tickets` - List tickets

**Basic Usage:**
```bash
zendesk tickets [OPTIONS]
```

**All Options:**
```bash
--assignee-only              # Show only tickets assigned to you
--group TEXT                 # Filter by group ID(s) or name(s) (comma-separated)
--status TEXT                # Filter by status(es) (comma-separated, default: open)
--sort-by [ticket|status|team|description|opened|days-opened|updated|days-updated]
--csv PATH                   # Export results to CSV file
--config-path PATH           # Use custom configuration file
```

**Status Values:**
- `new` - Newly created tickets
- `open` - Open and active tickets  
- `pending` - Waiting for customer response
- `hold` - On hold/paused tickets
- `solved` - Resolved tickets
- `closed` - Closed and archived tickets

### `zendesk configure` - Setup credentials

**Basic Usage:**
```bash
zendesk configure [OPTIONS]
```

**Options:**
```bash
--domain TEXT                # Zendesk domain (e.g., company.zendesk.com)
--email TEXT                 # Your email address
--api-token TEXT             # Your API token
--config-path PATH           # Custom configuration file path
--test                       # Test connection after configuration
```

## Usage Examples

### Basic Filtering

```bash
# All open tickets (default)
zendesk tickets

# Multiple statuses - tickets that are open OR pending
zendesk tickets --status "open,pending"

# Tickets on hold or closed
zendesk tickets --status "hold,closed"

# Only your assigned tickets
zendesk tickets --assignee-only

# Specific team's tickets
zendesk tickets --group "Support Team"

# Multiple teams
zendesk tickets --group "Support Team,Engineering,Sales"
```

### Sorting & Organization

```bash
# Sort by oldest tickets first (most urgent)
zendesk tickets --sort-by days-opened

# Sort by most stale (needs attention)
zendesk tickets --sort-by days-updated

# Sort by team for grouping
zendesk tickets --sort-by team

# Sort by ticket number
zendesk tickets --sort-by ticket
```

### CSV Export

```bash
# Export all open tickets
zendesk tickets --csv tickets.csv

# Export stale tickets sorted by age
zendesk tickets --status "open,pending" --sort-by days-updated --csv stale.csv

# Export team-specific tickets
zendesk tickets --group "Support Team" --csv support_tickets.csv

# Export multiple statuses for reporting
zendesk tickets --status "hold,closed" --csv closed_tickets.csv
```

### Advanced Combinations

```bash
# Find stale pending tickets for specific teams
zendesk tickets --status "pending" --group "Support Team,Level 2" --sort-by days-updated --csv stale_pending.csv

# Export all your tickets across all statuses
zendesk tickets --assignee-only --status "new,open,pending,hold" --sort-by opened --csv my_tickets.csv

# Get overview of closed tickets by team
zendesk tickets --status "solved,closed" --sort-by team --csv closed_by_team.csv
```

## Example Output

### Table Display

```bash
$ zendesk tickets --status "open,pending" --sort-by days-updated
📋 Fetching open,pending tickets...

📊 Found 4 open,pending ticket(s):
                                    🎫 Zendesk Tickets                                    
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Ticket # ┃ Status  ┃ Team Name       ┃ Description               ┃ Opened                    ┃
┣━━━━━━━━━━╋━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ #12345   ┃ Open    ┃ Support Team    ┃ Login system not work...  ┃ 2024-01-15                ┃
┃ #12346   ┃ Pending ┃ Engineering     ┃ Database performance i... ┃ 2024-01-18                ┃
┃ #12347   ┃ Open    ┃ Support Team    ┃ Email notifications no... ┃ 2024-01-20                ┃
┃ #12348   ┃ Pending ┃ Level 2 Support ┃ Complex integration is... ┃ 2024-01-22                ┃
┗━━━━━━━━━━┻━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Days Since Opened   ┃ Updated                   ┃ Days Since Updated        ┃ Link                                  ┃
┣━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 13                  ┃ 2024-01-20                ┃ 8                         ┃ https://company.zendesk.com/agent/... ┃
┃ 10                  ┃ 2024-01-22                ┃ 6                         ┃ https://company.zendesk.com/agent/... ┃
┃ 8                   ┃ 2024-01-24                ┃ 4                         ┃ https://company.zendesk.com/agent/... ┃
┃ 6                   ┃ 2024-01-26                ┃ 2                         ┃ https://company.zendesk.com/agent/... ┃
┗━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📈 Summary:
   Total: 4 tickets
   Status: open: 2, pending: 2
```

### CSV Export

```bash
$ zendesk tickets --csv tickets.csv
📋 Fetching open tickets...
✅ Exported 4 tickets to tickets.csv

📊 Found 4 open ticket(s):
[table output continues...]
```

**CSV Content (tickets.csv):**
```csv
"Ticket #","Status","Team Name","Description","Opened","Days Since Opened","Updated","Days Since Updated","Link"
"#12345","Open","Support Team","Login system not working for users - customers report authentication failures","2024-01-15","13","2024-01-20","8","https://company.zendesk.com/agent/tickets/12345"
"#12346","Pending","Engineering","Database performance issues causing timeouts","2024-01-18","10","2024-01-22","6","https://company.zendesk.com/agent/tickets/12346"
```

### Configuration

```bash
$ zendesk configure --test
🔧 Zendesk CLI Configuration
========================================
Zendesk domain (e.g., company.zendesk.com): company.zendesk.com
Your email address: user@company.com
Your API token: [hidden]
✅ Configuration saved successfully

🔍 Testing connection...
✅ Connection successful!
   Logged in as: John Doe (user@company.com)
   User ID: 12345

🎉 Setup complete! You can now run 'zendesk tickets' to list your tickets.
```

### No Results

```bash
$ zendesk tickets --assignee-only --status closed
📋 Fetching closed tickets assigned to you...
✅ No closed tickets found!
```

## Configuration

### Automatic Setup
Configuration is stored securely across platforms:

- **Linux/Mac**: `~/.config/zendesk-cli/config.json`
- **Windows**: `%APPDATA%\zendesk-cli\config.json`
- **API Token**: Stored securely in system keyring (not in the JSON file)

### Manual Configuration
Configure using command-line flags:

```bash
zendesk configure \
  --domain company.zendesk.com \
  --email your-email@company.com \
  --api-token your-api-token \
  --test
```

### Custom Configuration File
```bash
zendesk tickets --config-path ./custom-config.json
```

## API Token Setup

1. Log into your Zendesk instance as an administrator
2. Go to **Admin Center** → **Apps and integrations** → **APIs** → **Zendesk API**  
3. Enable **"Token access"** if not already enabled
4. Click **"+ Add API token"**
5. Enter a description (e.g., "CLI Tool Access")
6. Copy the generated token (save it securely - you won't see it again)
7. Use this token when running `zendesk configure`

**Reference**: [Zendesk API Token Documentation](https://developer.zendesk.com/api-reference/introduction/security-and-auth/#api-token)

## Troubleshooting

### Common Issues

**"No configuration found"**
```bash
# Solution: Run configuration first
zendesk configure --test
```

**"Authentication failed"**
```bash
# Solution: Check credentials and reconfigure
zendesk configure --test

# Check current configuration  
cat ~/.config/zendesk-cli/config.json
```

**"Permission denied"**
- Ensure your Zendesk user has API access enabled
- Verify your user role has ticket viewing permissions
- Check that your API token hasn't expired

**"Group 'Team Name' not found"**
- Verify the team name exists in your Zendesk instance
- Try using the group ID instead: `--group 12345`
- Check you have access to view that group's tickets

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
zendesk --verbose tickets
zendesk --log-file debug.log tickets
```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/jamiemills/zendesk-cli.git
cd zendesk-cli

# Create virtual environment  
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test category
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports  
isort src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Ensure code quality checks pass (`black`, `ruff`, `mypy`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Library Usage

The zendesk-cli package can be used as a Python library in your own applications. This is useful for automation, integration with web applications, or building custom reporting tools.

### Basic Library Usage

```python
from zendesk_cli import ZendeskLibrary

# Initialize with credentials
zd = ZendeskLibrary.from_credentials(
    domain="company.zendesk.com",
    email="user@company.com",
    api_token="your_token"
)

# Or initialize from config file
zd = ZendeskLibrary.from_config()

# Test connection
if zd.test_connection():
    print("✅ Connected successfully")

# Get tickets with filtering
tickets = zd.get_tickets(
    status=["open", "pending"],
    assignee_only=True,
    sort_by="days_updated"
)

print(f"Found {len(tickets)} tickets")

# Export to CSV
zd.export_to_csv(tickets, "my_tickets.csv")
```

### Web Application Integration

```python
from flask import Flask, jsonify
from zendesk_cli import ZendeskLibrary

app = Flask(__name__)
zd = ZendeskLibrary.from_config()

@app.route('/api/tickets')
def get_tickets_api():
    try:
        tickets = zd.get_tickets(status=["open", "pending"])
        return jsonify({
            'success': True,
            'count': len(tickets),
            'tickets': [ticket.dict() for ticket in tickets]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Automated Reporting

```python
from zendesk_cli import ZendeskLibrary
from datetime import datetime

def daily_stale_tickets_report():
    zd = ZendeskLibrary.from_config()
    
    # Get stale tickets (not updated in 3+ days)
    all_tickets = zd.get_tickets(status=["open", "pending"])
    stale_tickets = [t for t in all_tickets if t.days_since_updated >= 3]
    
    # Export with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zd.export_to_csv(stale_tickets, f"reports/stale_tickets_{timestamp}.csv")
    
    return len(stale_tickets)
```

### Progress Callbacks

```python
from zendesk_cli import ZendeskLibrary

def progress_callback(message):
    print(f"[INFO] {message}")

zd = ZendeskLibrary.from_credentials(
    domain="company.zendesk.com",
    email="user@company.com",
    api_token="your_token",
    progress_callback=progress_callback
)

# Operations will now report progress:
# [INFO] Fetching tickets...
# [INFO] Found 25 ticket(s)
tickets = zd.get_tickets()
```

### Error Handling

```python
from zendesk_cli import (
    ZendeskLibrary,
    AuthenticationError,
    NetworkError,
    ConfigurationError
)

try:
    zd = ZendeskLibrary.from_config()
    tickets = zd.get_tickets()
    
except AuthenticationError:
    print("❌ Invalid credentials")
except NetworkError:
    print("❌ Network connection failed")
except ConfigurationError:
    print("❌ Configuration missing or invalid")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Library API Reference

The library provides these main classes:

- **`ZendeskLibrary`** - Main interface for all operations
- **`LibraryTicket`** - Ticket data model with JSON serialization
- **`LibraryUser`** - User data model  
- **`LibraryGroup`** - Group/team data model

Key methods on `ZendeskLibrary`:
- `get_tickets()` - Retrieve tickets with filtering and sorting
- `get_tickets_with_teams()` - Retrieve tickets with resolved team names
- `export_to_csv()` - Export tickets to CSV format
- `test_connection()` - Verify API connection
- `configure()` - Update configuration programmatically

For complete examples, see the [`examples/library_usage.py`](examples/library_usage.py) file.

## Support

- **Documentation**: This README and inline help (`zendesk --help`)
- **Repository**: [https://github.com/jamiemills/zendesk-cli](https://github.com/jamiemills/zendesk-cli)
- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/jamiemills/zendesk-cli/issues)
- **API Reference**: [Zendesk API Documentation](https://developer.zendesk.com/api-reference/)