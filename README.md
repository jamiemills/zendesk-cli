# Zendesk CLI

A command-line utility to list open Zendesk tickets assigned to you or your groups, displaying them in a beautiful tabular format.

## Features

- 🎫 List open Zendesk tickets
- 👤 Filter tickets assigned to you
- 👥 Filter tickets by group
- 🔒 Secure credential storage using keyring
- 🎨 Beautiful table output with Rich
- ⚙️ Easy configuration management

## Installation

```bash
# Install the package in development mode
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure your Zendesk credentials

```bash
zendesk configure
```

You'll be prompted for:

- **Zendesk domain** (e.g., `company.zendesk.com`)
- **Email address** (your Zendesk account email)
- **API token** (generate from Zendesk Admin → APIs)

### 2. List your tickets

```bash
# List all open tickets
zendesk tickets

# List only tickets assigned to you
zendesk tickets --assignee-only

# List tickets for a specific group
zendesk tickets --group 12345

# List tickets for multiple groups
zendesk tickets --group 12345,6789,1111
```

## Example Outputs

### Configuration Setup

```bash
$ zendesk configure --test
🔧 Zendesk CLI Configuration
========================================
Zendesk domain (e.g., company.zendesk.com): acme.zendesk.com
Your email address: john.doe@acme.com
Your API token: 
✅ Configuration saved to: /Users/john/.config/zendesk-cli/config.json

🔍 Testing connection...
✅ Connection successful!
   Logged in as: John Doe (john.doe@acme.com)
   User ID: 12345

🎉 Setup complete! You can now run 'zendesk tickets' to list your tickets.
```

### Listing All Tickets

```bash
$ zendesk tickets
📋 Fetching all open tickets...

📊 Found 3 open ticket(s):
                              🎫 Zendesk Tickets                              
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Ticket # ┃ Team       ┃ Description                          ┃ First Opened ┃
┣━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━┫
┃ #1234    ┃ Group 456  ┃ Login system not working for users   ┃ 2024-01-15   ┃
┃ #1235    ┃ Group 789  ┃ Feature request: Add dark mode sup...┃ 2024-01-16   ┃
┃ #1236    ┃ Unassigned ┃ Performance issues on dashboard      ┃ 2024-01-17   ┃
┗━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Days Open  ┃ Last Updated ┃ Days Since Update┃ Link                           ┃
┣━━━━━━━━━━━━╋━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 13         ┃ 2024-01-20   ┃ 8                ┃ https://acme.zendesk.com/ti... ┃
┃ 12         ┃ 2024-01-16   ┃ 12               ┃ https://acme.zendesk.com/ti... ┃
┃ 11         ┃ 2024-01-17   ┃ 11               ┃ https://acme.zendesk.com/ti... ┃
┗━━━━━━━━━━━━┻━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📈 Summary:
   Total: 3 tickets
   Status: open: 3
```

### Filtering by Multiple Groups

```bash
$ zendesk tickets --group 456,789,123
📋 Fetching tickets for groups 456, 789, 123...

📊 Found 25 open ticket(s):
                              🎫 Zendesk Tickets                              
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Ticket # ┃ Team       ┃ Description                          ┃ First Opened ┃
┣━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━┫
┃ #5678    ┃ Group 456  ┃ Multi-team collaboration issue       ┃ 2024-01-18   ┃
┃ #5679    ┃ Group 789  ┃ Cross-department feature request     ┃ 2024-01-17   ┃
┃ #5680    ┃ Group 123  ┃ Shared resource allocation problem   ┃ 2024-01-16   ┃
┗━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┛

📈 Summary:
   Total: 25 tickets
   Status: open: 20, pending: 5
```

### Filtering by Assignee

```bash
$ zendesk tickets --assignee-only
📋 Fetching tickets assigned to you...

📊 Found 1 open ticket(s):
                              🎫 Zendesk Tickets                              
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Ticket # ┃ Team       ┃ Description                          ┃ First Opened ┃
┣━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━┫
┃ #1234    ┃ Group 456  ┃ Login system not working for users   ┃ 2024-01-15   ┃
┗━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Days Open  ┃ Last Updated ┃ Days Since Update┃ Link                           ┃
┣━━━━━━━━━━━━╋━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 13         ┃ 2024-01-20   ┃ 8                ┃ https://acme.zendesk.com/ti... ┃
┗━━━━━━━━━━━━┻━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📈 Summary:
   Total: 1 tickets
   Status: open: 1
```

### No Tickets Found

```bash
$ zendesk tickets --assignee-only
📋 Fetching tickets assigned to you...
✅ No open tickets found!
```

### Error Handling

```bash
$ zendesk tickets
❌ No configuration found. Run 'zendesk configure' first.
```

```bash
$ zendesk configure --test
🔧 Zendesk CLI Configuration
========================================
Zendesk domain (e.g., company.zendesk.com): bad-domain.zendesk.com
Your email address: wrong@email.com
Your API token: bad_token
✅ Configuration saved to: /Users/john/.config/zendesk-cli/config.json

🔍 Testing connection...
❌ Connection test failed: Authentication failed. Please check your email and API token.

💡 Suggestions:
   • Check your API token is correct
   • Verify your email address
   • Run 'zendesk configure' to update credentials

Please check your credentials and try again.
```

### Help Output

```bash
$ zendesk --help
Usage: zendesk [OPTIONS] COMMAND [ARGS]...

  Zendesk CLI - Manage your Zendesk tickets from the command line.

  This tool allows you to:
  - List open tickets assigned to you or your groups
  - Configure your Zendesk credentials securely
  - Display tickets in a beautiful table format

  Get started by running:
      zendesk configure

  Then list your tickets with:
      zendesk tickets

Options:
  -v, --verbose       Enable verbose output
  --log-file PATH     Log file path
  --version           Show the version and exit.
  --help              Show this message and exit.

Commands:
  configure  Configure Zendesk CLI credentials and settings.
  tickets    List open Zendesk tickets assigned to you or your groups.
```

## Configuration

Configuration is stored securely:

- **Non-sensitive data**: `~/.config/zendesk-cli/config.json` (Linux/Mac) or `%APPDATA%\zendesk-cli\config.json` (Windows)
- **API token**: Stored securely in your system keyring

### Manual Configuration

You can also configure using command-line flags:

```bash
zendesk configure \
  --domain company.zendesk.com \
  --email your-email@company.com \
  --api-token your-api-token \
  --test
```

## API Token Setup

1. Log into your Zendesk instance
2. Go to **Admin Center** → **Apps and integrations** → **APIs** → **Zendesk API**
3. Enable **"Token access"**
4. Click **"Add API token"**
5. Copy the generated token

## Commands

### `zendesk tickets`

List open Zendesk tickets with detailed information.

**Options:**

- `--assignee-only`: Show only tickets assigned to you
- `--group ID[,ID,...]`: Filter tickets by group ID(s). Use comma-separated values for multiple groups
- `--config-path PATH`: Use custom configuration file

**Output includes:**

- Ticket number
- Team/Group assigned
- Short description
- Creation date and days since created
- Last update date and days since updated
- Direct link to ticket

### `zendesk configure`

Configure Zendesk CLI credentials and settings.

**Options:**

- `--domain DOMAIN`: Zendesk domain
- `--email EMAIL`: Your email address
- `--api-token TOKEN`: Your API token
- `--config-path PATH`: Custom configuration file path
- `--test`: Test connection after configuration

### Global Options

- `--verbose, -v`: Enable verbose output
- `--log-file PATH`: Write logs to file
- `--help`: Show help message

## Examples

```bash
# First time setup
zendesk configure --test

# Daily workflow
zendesk tickets --assignee-only

# Team workflow - single group
zendesk tickets --group 456

# Multiple teams workflow
zendesk tickets --group 456,789,123

# Debugging
zendesk --verbose tickets

# Custom configuration
zendesk --config-path ./my-config.json tickets
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd zendesk-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run integration tests with real API
python test_real_api.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Troubleshooting

### Authentication Issues

```bash
# Test your configuration
zendesk configure --test

# Check configuration
cat ~/.config/zendesk-cli/config.json
```

### Common Errors

- **"No configuration found"**: Run `zendesk configure` first
- **"Authentication failed"**: Check your API token and email
- **"Permission denied"**: Ensure your user has access to the Zendesk API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
