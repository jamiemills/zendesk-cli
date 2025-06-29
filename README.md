# TicketQ

A universal command-line utility and Python library for managing tickets across multiple ticketing systems. TicketQ provides a unified interface for Zendesk, Jira, ServiceNow, and other platforms through a pluggable adapter architecture.

## Core Concepts

**TicketQ** connects to various ticketing systems via their APIs to provide a fast, unified terminal interface for ticket management. It uses pluggable adapters to support multiple platforms, secure credential storage, and provides rich filtering, sorting, and export capabilities.

**Key Benefits:**
- 🔌 **Multi-platform support** - Zendesk, Jira, ServiceNow through adapters
- 🚀 **Fast ticket overview** - See all your tickets at a glance
- 🎯 **Smart filtering** - Filter by assignee, groups, status, or combinations
- 📊 **Flexible sorting** - Sort by any column for better organization  
- 💾 **CSV export** - Export filtered results with full descriptions
- 🔒 **Secure** - API tokens stored safely in system keyring
- 🎨 **Beautiful output** - Rich terminal tables with color coding
- 📦 **Library ready** - Use programmatically in your Python applications
- 🔧 **Adapter architecture** - Easy to extend with new ticketing systems

## Installation

### Core TicketQ Installation

```bash
# Install TicketQ core with CLI dependencies
pip install "ticketq[cli]"

# Or install from GitHub
pip install "git+https://github.com/jamiemills/ticketq.git[cli]"
```

### Adapter Installation

TicketQ requires adapter packages for specific ticketing systems:

```bash
# Install Zendesk adapter
pip install ticketq-zendesk

# Install Jira adapter (planned)
pip install ticketq-jira

# Install ServiceNow adapter (planned)
pip install ticketq-servicenow
```

### Library Only (for developers)

```bash
# Install core library without CLI dependencies
pip install ticketq

# Or from GitHub
pip install git+https://github.com/jamiemills/ticketq.git
```

### For Development

```bash
# Clone and install with all dependencies
git clone https://github.com/jamiemills/ticketq.git
cd ticketq
pip install -e ".[cli,dev]"
pip install -e "./src/ticketq-zendesk"  # Install Zendesk adapter in dev mode
```

## Quick Start

### 1. Install TicketQ and an adapter

```bash
# Install TicketQ with CLI support
pip install "ticketq[cli]"

# Install Zendesk adapter
pip install ticketq-zendesk
```

### 2. Configure an adapter

```bash
# Configure Zendesk (or any available adapter)
tq configure --adapter zendesk

# Or let TicketQ auto-detect
tq configure
```

You'll be prompted for adapter-specific credentials (e.g., for Zendesk):
- **Domain** (e.g., `company.zendesk.com`)
- **Email address** (your account email)  
- **API token** ([generate from platform](https://developer.zendesk.com/api-reference/introduction/security-and-auth/#api-token))

### 3. List tickets

```bash
# List all open tickets
tq tickets

# List only your assigned tickets
tq tickets --assignee-only

# List tickets by team/group
tq tickets --group "Support Team"

# View available adapters
tq adapters
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

### `tq tickets` - List tickets

**Basic Usage:**
```bash
tq tickets [OPTIONS]
```

**All Options:**
```bash
--assignee-only              # Show only tickets assigned to you
--group TEXT                 # Filter by group ID(s) or name(s) (comma-separated)
--status TEXT                # Filter by status(es) (comma-separated, default: open)
--sort-by [id|title|status|team|created_at|updated_at|days_created|days_updated]
--csv PATH                   # Export results to CSV file
--config-path PATH           # Use custom configuration directory
--adapter TEXT               # Override adapter selection
```

**Status Values:**
- `new` - Newly created tickets
- `open` - Open and active tickets  
- `pending` - Waiting for customer response
- `hold` - On hold/paused tickets
- `solved` - Resolved tickets
- `closed` - Closed and archived tickets

### `tq configure` - Setup credentials

**Basic Usage:**
```bash
tq configure [OPTIONS]
```

**Options:**
```bash
--adapter TEXT               # Adapter to configure (zendesk, jira, servicenow)
--config-path PATH           # Custom configuration directory path
--test                       # Test connection after configuration
--list-adapters              # List available adapters and exit
```

### `tq adapters` - Manage adapters

**Basic Usage:**
```bash
tq adapters [OPTIONS]
```

**Options:**
```bash
--config-path PATH           # Use custom configuration directory
--test                       # Test all configured adapters
--install-guide              # Show installation guide for adapters
```

## Usage Examples

### Basic Filtering

```bash
# All open tickets (default)
tq tickets

# Multiple statuses - tickets that are open OR pending
tq tickets --status "open,pending"

# Tickets on hold or closed
tq tickets --status "hold,closed"

# Only your assigned tickets
tq tickets --assignee-only

# Specific team's tickets
tq tickets --group "Support Team"

# Multiple teams
tq tickets --group "Support Team,Engineering,Sales"

# Use specific adapter
tq tickets --adapter zendesk
```

### Sorting & Organization

```bash
# Sort by oldest tickets first (most urgent)
tq tickets --sort-by days_created

# Sort by most stale (needs attention)
tq tickets --sort-by days_updated

# Sort by team for grouping
tq tickets --sort-by team

# Sort by ticket ID
tq tickets --sort-by id
```

### CSV Export

```bash
# Export all open tickets
tq tickets --csv tickets.csv

# Export stale tickets sorted by age
tq tickets --status "open,pending" --sort-by days_updated --csv stale.csv

# Export team-specific tickets
tq tickets --group "Support Team" --csv support_tickets.csv

# Export multiple statuses for reporting
tq tickets --status "hold,closed" --csv closed_tickets.csv
```

### Advanced Combinations

```bash
# Find stale pending tickets for specific teams
tq tickets --status "pending" --group "Support Team,Level 2" --sort-by days_updated --csv stale_pending.csv

# Export all your tickets across all statuses
tq tickets --assignee-only --status "new,open,pending,hold" --sort-by created_at --csv my_tickets.csv

# Get overview of closed tickets by team
tq tickets --status "solved,closed" --sort-by team --csv closed_by_team.csv
```

## Example Output

### Table Display

```bash
$ tq tickets --status "open,pending" --sort-by days_updated
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
$ tq tickets --csv tickets.csv
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
$ tq configure --adapter zendesk --test
🔧 Configuring Zendesk adapter
Enter your configuration details:
Zendesk domain (e.g., company.zendesk.com): company.zendesk.com
Your email address: user@company.com
Your API token: [hidden]
✅ Configuration saved for zendesk adapter

🔍 Testing connection...
✅ Successfully connected as John Doe (user@company.com)
✅ Configuration test successful!

🎉 Setup complete! You can now run 'tq tickets' to list your tickets.
```

### No Results

```bash
$ tq tickets --assignee-only --status closed
📋 Fetching closed tickets...
✅ No closed tickets found!
```

## Configuration

### Automatic Setup
Configuration is stored securely across platforms:

- **Linux/Mac**: `~/.config/ticketq/config.json`
- **Windows**: `%APPDATA%\ticketq\config.json`
- **API Token**: Stored securely in system keyring (not in the JSON file)

### Manual Configuration
Configure using command-line flags:

```bash
tq configure --adapter zendesk --test
# Interactive prompts will guide you through configuration
```

### Custom Configuration File
```bash
tq tickets --config-path ./custom-config/
```

## API Token Setup

1. Log into your Zendesk instance as an administrator
2. Go to **Admin Center** → **Apps and integrations** → **APIs** → **Zendesk API**  
3. Enable **"Token access"** if not already enabled
4. Click **"+ Add API token"**
5. Enter a description (e.g., "CLI Tool Access")
6. Copy the generated token (save it securely - you won't see it again)
7. Use this token when running `tq configure --adapter zendesk`

**Reference**: [Zendesk API Token Documentation](https://developer.zendesk.com/api-reference/introduction/security-and-auth/#api-token)

## Troubleshooting

### Common Issues

**"No configuration found"**
```bash
# Solution: Run configuration first
tq configure --adapter zendesk --test
```

**"Authentication failed"**
```bash
# Solution: Check credentials and reconfigure
tq configure --adapter zendesk --test

# List configured adapters
tq adapters
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
tq --verbose tickets
tq --log-file debug.log tickets
```

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/jamiemills/ticketq.git
cd ticketq

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

TicketQ can be used as a Python library in your own applications. This is useful for automation, integration with web applications, or building custom reporting tools across multiple ticketing platforms.

### Basic Library Usage

```python
from ticketq import TicketQLibrary

# Initialize with auto-detected adapter
tq = TicketQLibrary.from_config()

# Or initialize with specific adapter
tq = TicketQLibrary.from_config(adapter_name="zendesk")

# Test connection
if tq.test_connection():
    print("✅ Connected successfully")

# Get tickets with filtering
tickets = tq.get_tickets(
    status=["open", "pending"],
    assignee_only=True,
    sort_by="days_updated"
)

print(f"Found {len(tickets)} tickets")

# Export to CSV
tq.export_to_csv(tickets, "my_tickets.csv")

# Get adapter information
adapter_info = tq.get_adapter_info()
print(f"Using {adapter_info['display_name']} adapter")
```

### Web Application Integration

```python
from flask import Flask, jsonify
from ticketq import TicketQLibrary

app = Flask(__name__)
tq = TicketQLibrary.from_config()

@app.route('/api/tickets')
def get_tickets_api():
    try:
        tickets = tq.get_tickets(status=["open", "pending"])
        adapter_info = tq.get_adapter_info()
        return jsonify({
            'success': True,
            'count': len(tickets),
            'adapter': adapter_info['name'],
            'tickets': [ticket.dict() for ticket in tickets]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Automated Reporting

```python
from ticketq import TicketQLibrary
from datetime import datetime

def daily_stale_tickets_report():
    tq = TicketQLibrary.from_config()
    
    # Get stale tickets (not updated in 3+ days)
    all_tickets = tq.get_tickets(status=["open", "pending"])
    stale_tickets = [t for t in all_tickets if t.days_since_updated >= 3]
    
    # Export with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    adapter_name = tq.get_adapter_info()['name']
    tq.export_to_csv(stale_tickets, f"reports/{adapter_name}_stale_tickets_{timestamp}.csv")
    
    return len(stale_tickets)
```

### Progress Callbacks

```python
from ticketq import TicketQLibrary

def progress_callback(message):
    print(f"[INFO] {message}")

tq = TicketQLibrary.from_config(
    adapter_name="zendesk",
    progress_callback=progress_callback
)

# Operations will now report progress:
# [INFO] Fetching tickets...
# [INFO] Found 25 ticket(s)
tickets = tq.get_tickets()
```

### Error Handling

```python
from ticketq import (
    TicketQLibrary,
    AuthenticationError,
    NetworkError,
    ConfigurationError,
    PluginError
)

try:
    tq = TicketQLibrary.from_config()
    tickets = tq.get_tickets()
    
except AuthenticationError:
    print("❌ Invalid credentials")
except NetworkError:
    print("❌ Network connection failed")
except ConfigurationError:
    print("❌ Configuration missing or invalid")
except PluginError:
    print("❌ Adapter not found or failed to load")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

### Multi-Adapter Usage

```python
from ticketq import TicketQLibrary

# Use different adapters for different operations
zendesk_tq = TicketQLibrary.from_config(adapter_name="zendesk")
jira_tq = TicketQLibrary.from_config(adapter_name="jira")

# Combine tickets from multiple systems
all_tickets = []
all_tickets.extend(zendesk_tq.get_tickets(status=["open"]))
all_tickets.extend(jira_tq.get_tickets(status=["in progress"]))

print(f"Total tickets across all systems: {len(all_tickets)}")
```

### Library API Reference

The library provides these main classes:

- **`TicketQLibrary`** - Main interface for all operations
- **`LibraryTicket`** - Ticket data model with JSON serialization
- **`LibraryUser`** - User data model  
- **`LibraryGroup`** - Group/team data model

Key methods on `TicketQLibrary`:
- `get_tickets()` - Retrieve tickets with filtering and sorting
- `get_ticket()` - Get a specific ticket by ID
- `get_current_user()` - Get current authenticated user info
- `get_groups()` - Get all available groups/teams
- `search_tickets()` - Search tickets with system-specific queries
- `export_to_csv()` - Export tickets to CSV format
- `test_connection()` - Verify API connection
- `get_adapter_info()` - Get information about current adapter

For complete examples, see the comprehensive example files:

- **[`examples/library_usage.py`](examples/library_usage.py)** - Complete library API examples
- **[`examples/automation_scripts.py`](examples/automation_scripts.py)** - Automation and scheduled reporting
- **[`examples/web_integration.py`](examples/web_integration.py)** - Flask and FastAPI integration

## Support

- **Documentation**: This README and inline help (`tq --help`)
- **Repository**: [https://github.com/jamiemills/ticketq](https://github.com/jamiemills/ticketq)
- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/jamiemills/ticketq/issues)
- **Adapters**: 
  - [Zendesk API Documentation](https://developer.zendesk.com/api-reference/)
  - Jira API Documentation (planned)
  - ServiceNow API Documentation (planned)

## Adapter Development

Want to add support for a new ticketing system? TicketQ's adapter architecture makes it easy:

1. Create a new package (e.g., `ticketq-linear`) 
2. Implement the adapter interfaces (`BaseAdapter`, `BaseAuth`, `BaseClient`)
3. Register your adapter with the entry point: `"ticketq.adapters"`
4. Users can install and use it: `pip install ticketq-linear`

See the [Zendesk adapter implementation](src/ticketq_zendesk/) for a complete example.

## License

MIT License - see [LICENSE](LICENSE) for details.