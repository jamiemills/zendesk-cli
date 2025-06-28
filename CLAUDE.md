# Zendesk CLI Tool - Implementation Specification

## Overview

A command-line utility that connects to Zendesk's API to list, filter, sort, and export support tickets. The application displays tickets in a beautiful tabular format with comprehensive filtering options and supports CSV export for further analysis.

## Application Purpose

This tool addresses the common need for support teams and managers to quickly view and analyze Zendesk tickets from the command line. It provides:

- **Quick ticket overview** - See all relevant tickets at a glance without logging into the web interface
- **Advanced filtering** - Filter by status, assignee, teams, or combinations thereof
- **Flexible sorting** - Sort by any column for better organization and prioritization
- **Data export** - Export filtered results to CSV for reporting and analysis
- **Team efficiency** - Enable support teams to triage and manage tickets more efficiently

## Complete Feature Specification

### Core Functionality

1. **Ticket Listing**
   - Display tickets in a rich terminal table format
   - Show: ticket number, status, team name, description, opened date, days since opened, updated date, days since updated, direct link
   - Support for pagination (handled transparently via API)

2. **Multi-Status Filtering**
   - Filter by single status: `--status open`
   - Filter by multiple statuses with OR logic: `--status "open,pending,hold"`
   - Supported statuses: new, open, pending, hold, solved, closed

3. **Assignment Filtering**
   - Personal tickets only: `--assignee-only`
   - Team/group tickets: `--group "Support Team"`
   - Multiple teams: `--group "Support Team,Engineering,Level 2"`
   - All tickets (default behavior)

4. **Flexible Sorting**
   - Sort by ticket number: `--sort-by ticket`
   - Sort by status: `--sort-by status`
   - Sort by team: `--sort-by team`
   - Sort by description: `--sort-by description`
   - Sort by creation date: `--sort-by opened` (newest first)
   - Sort by age: `--sort-by days-opened` (oldest first)
   - Sort by update date: `--sort-by updated` (most recently updated first)
   - Sort by staleness: `--sort-by days-updated` (most stale first)

5. **CSV Export**
   - Export filtered and sorted results: `--csv tickets.csv`
   - Include full descriptions (not truncated like table display)
   - Proper CSV escaping for commas and special characters
   - UTF-8 encoding support
   - All columns from table display

6. **Team Name Resolution**
   - Convert group IDs to human-readable team names
   - Graceful fallback to group IDs when names unavailable
   - Support filtering by team names or IDs

7. **Secure Configuration**
   - Store credentials securely using system keyring
   - Platform-appropriate configuration file locations
   - Support for custom configuration file paths

### Command Line Interface

#### Primary Commands

**`tickets` Command**
```bash
app-name tickets [OPTIONS]

Options:
  --assignee-only              Show only tickets assigned to you
  --group TEXT                 Filter by group ID(s) or name(s) (comma-separated)
  --status TEXT                Filter by status(es) (comma-separated, default: open)
  --sort-by [ticket|status|team|description|opened|days-opened|updated|days-updated]
                              Sort results by column
  --csv PATH                   Export results to CSV file
  --config-path PATH           Use custom configuration file
```

**`configure` Command**
```bash
app-name configure [OPTIONS]

Options:
  --domain TEXT                Zendesk domain (e.g., company.zendesk.com)
  --email TEXT                 Your email address
  --api-token TEXT             Your API token
  --config-path PATH           Custom configuration file path
  --test                       Test connection after configuration
```

**Global Options**
```bash
--verbose, -v                 Enable verbose output
--log-file PATH               Write logs to file
--help                        Show help message
--version                     Show version information
```

#### Usage Examples

```bash
# Basic usage
app-name tickets                                    # All open tickets
app-name tickets --assignee-only                   # Your tickets only
app-name tickets --group "Support Team"            # Team tickets

# Multi-status filtering (OR logic)
app-name tickets --status "open,pending"           # Open OR pending
app-name tickets --status "hold,closed"            # Hold OR closed

# Sorting for prioritization
app-name tickets --sort-by days-updated            # Most stale first
app-name tickets --sort-by days-opened             # Oldest tickets first
app-name tickets --sort-by team                    # Group by team

# CSV export for reporting
app-name tickets --csv all_tickets.csv
app-name tickets --status "pending" --sort-by days-updated --csv stale.csv

# Complex combinations
app-name tickets --status "open,pending" --group "Support,Level 2" --sort-by days-updated --csv report.csv
```

## Technical Architecture

### Architectural Layers

```text
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface Layer                      │
├─────────────────────────────────────────────────────────────┤
│ • Command parsing and validation                             │
│ • User input handling and option processing                  │
│ • Output formatting (tables, CSV)                           │
│ • Error message display with suggestions                     │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                   Application Services Layer                 │
├─────────────────────────────────────────────────────────────┤
│ • TicketService (business logic for ticket operations)       │
│ • AuthService (authentication and configuration)             │
│ • ConfigurationService (secure credential management)        │
│ • FormatterService (table and CSV output formatting)         │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                      API Client Layer                        │
├─────────────────────────────────────────────────────────────┤
│ • HTTP client with authentication                            │
│ • Request/response handling                                  │
│ • Error handling and retry logic                            │
│ • API endpoint abstraction                                   │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                       Data Models Layer                      │
├─────────────────────────────────────────────────────────────┤
│ • Ticket model with validation and computed properties       │
│ • User model for authentication                             │
│ • Group model for team information                          │
│ • Configuration model with validation                       │
│ • Custom exception hierarchy                                │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                        Utilities Layer                       │
├─────────────────────────────────────────────────────────────┤
│ • Date/time calculations                                     │
│ • Logging configuration                                      │
│ • Platform-specific file paths                              │
│ • String formatting and truncation                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Models

#### Core Domain Models

**Ticket Model**
```text
Properties:
- id: Unique ticket identifier (integer)
- subject: Ticket title/summary (string)
- description: Full ticket description (string)
- status: Current status (enum: new, open, pending, hold, solved, closed)
- created_at: Creation timestamp (datetime)
- updated_at: Last modification timestamp (datetime)
- assignee_id: Assigned user ID (optional integer)
- group_id: Assigned group/team ID (optional integer)
- url: Direct link to ticket in Zendesk web interface (string)

Computed Properties:
- short_description: Truncated description for table display (≤50 characters)
- days_since_created: Days between creation and now (integer)
- days_since_updated: Days between last update and now (integer)

Validation Rules:
- id must be positive integer
- status must be valid enum value
- created_at must be valid datetime
- updated_at must be >= created_at
- url must be valid HTTP/HTTPS URL
```

**User Model**
```text
Properties:
- id: Unique user identifier (integer)
- name: Full user name (string)
- email: Email address (string)
- group_ids: List of group IDs user belongs to (list of integers)

Validation Rules:
- id must be positive integer
- email must be valid email format
- group_ids must be list of positive integers
```

**Group Model**
```text
Properties:
- id: Unique group identifier (integer)
- name: Human-readable group/team name (string)
- description: Optional group description (string)

Validation Rules:
- id must be positive integer
- name must be non-empty string
```

**Configuration Model**
```text
Properties:
- domain: Zendesk instance domain (string)
- email: User email for authentication (string)
- api_token: API token for authentication (string, stored securely)

Validation Rules:
- domain must be valid hostname ending in .zendesk.com
- email must be valid email format
- api_token must be non-empty string (minimum length validation)
```

#### Exception Hierarchy

```text
ZendeskCliError (base exception)
├── AuthenticationError (invalid credentials, expired tokens)
├── APIError (HTTP errors, server issues)
│   ├── RateLimitError (429 rate limiting)
│   └── NetworkError (connection issues, timeouts)
├── ConfigurationError (missing/invalid configuration)
├── ValidationError (invalid input data)
└── KeyringError (credential storage issues)

Each exception includes:
- Human-readable error message
- Actionable suggestions for resolution
- Context information (status codes, retry timing, etc.)
- Original exception chaining for debugging
```

### Zendesk API Integration

#### Required API Endpoints

**1. Search API (Primary)**
```text
Endpoint: GET /api/v2/search.json
Purpose: Flexible ticket searching with complex filters
Query Format: type:ticket status:open assignee:123
Multi-Status: Multiple separate API calls combined client-side
Parameters:
- query: Search query string
- page[size]: Results per page (max 100)
- page[after]: Pagination cursor

Response Format:
- results: Array of ticket objects
- meta: Pagination information
- count: Total result count
```

**2. Users API**
```text
Endpoint: GET /api/v2/users/me.json
Purpose: Get current authenticated user information
Response:
- user: User object with id, name, email, group_ids
```

**3. Groups API**
```text
Endpoint: GET /api/v2/groups.json
Purpose: Get team/group information for name resolution
Response:
- groups: Array of group objects with id, name, description
```

#### Authentication Strategy

**API Token Authentication**
```text
Method: HTTP Basic Authentication
Format: {email}/token:{api_token}
Header: Authorization: Basic <base64_encoded_credentials>

Security Requirements:
- Store API token in system keyring (not configuration file)
- Validate token on first use
- Handle token expiration gracefully
- Support token rotation
```

#### API Client Features

**Request Handling**
- HTTP client with configurable timeouts
- Automatic retry with exponential backoff
- Rate limiting respect (HTTP 429 handling)
- SSL certificate validation
- User-Agent header identification

**Response Processing**
- JSON parsing with error handling
- Data model validation
- Pagination handling
- Error classification and user-friendly messages

**Multi-Status Implementation**
```text
Challenge: Zendesk Search API OR syntax can be unreliable
Solution: Multiple API calls combined client-side

Algorithm:
1. For single status: Direct API call with status filter
2. For multiple statuses:
   - Make separate API call for each status
   - Combine results and deduplicate by ticket ID
   - Sort combined results by specified column
   - Preserve original sort order
```

### Output Formatting

#### Table Format

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                🎫 Zendesk Tickets                                    │
├──────────┬─────────┬─────────────────┬─────────────────────────┬─────────────────────┤
│ Ticket # │ Status  │ Team Name       │ Description             │ Opened              │
├──────────┼─────────┼─────────────────┼─────────────────────────┼─────────────────────┤
│ #12345   │ Open    │ Support Team    │ Login system not work...│ 2024-01-15          │
│ #12346   │ Pending │ Engineering     │ Database performance...  │ 2024-01-18          │
└──────────┴─────────┴─────────────────┴─────────────────────────┴─────────────────────┘

├─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┤
│ Days Since Opened   │ Updated             │ Days Since Updated  │ Link                │
├─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ 13                  │ 2024-01-20          │ 8                   │ https://company...  │
│ 10                  │ 2024-01-22          │ 6                   │ https://company...  │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

📈 Summary:
   Total: 2 tickets
   Status: open: 1, pending: 1
```

**Table Features:**
- Rich terminal formatting with colors and borders
- Unicode box-drawing characters for clean appearance
- Automatic column width adjustment
- Description truncation with ellipsis (≤25 characters for table)
- Status capitalization for readability
- Summary statistics with breakdown by status

#### CSV Format

```csv
"Ticket #","Status","Team Name","Description","Opened","Days Since Opened","Updated","Days Since Updated","Link"
"#12345","Open","Support Team","Login system not working for users - full description here","2024-01-15","13","2024-01-20","8","https://company.zendesk.com/agent/tickets/12345"
```

**CSV Features:**
- All fields quoted with QUOTE_ALL for maximum compatibility
- Full descriptions (not truncated)
- UTF-8 encoding for international characters
- Proper escaping of commas, quotes, and newlines
- Header row with column names
- Status capitalization for consistency

### Configuration Management

#### Storage Strategy

**Platform-Specific Locations:**
```text
Linux/macOS: ~/.config/zendesk-cli/config.json
Windows: %APPDATA%\zendesk-cli\config.json

Configuration File (JSON):
{
  "domain": "company.zendesk.com",
  "email": "user@company.com"
}

Secure Storage (System Keyring):
- API token stored separately using system keyring
- Service name: "zendesk-cli"
- Account name: user email address
```

**Configuration Validation:**
- Domain format validation (must end in .zendesk.com)
- Email format validation
- API token presence and minimum length validation
- Connection testing on configuration

#### Error Handling Strategy

**Error Categories and Responses:**

1. **Authentication Errors (401)**
   - Message: "Authentication failed. Please check your email and API token."
   - Suggestions: Check credentials, run configuration, verify token validity

2. **Rate Limiting (429)**
   - Message: "Rate limit exceeded. Please wait before making more requests."
   - Action: Automatic retry with exponential backoff
   - Suggestions: Reduce request frequency, wait specified time

3. **Network Errors**
   - Message: "Failed to connect to Zendesk. Please check your internet connection."
   - Suggestions: Check network, verify domain, try again later

4. **Configuration Errors**
   - Message: "No configuration found. Run 'app-name configure' first."
   - Suggestions: Run configuration command, check file permissions

5. **Validation Errors**
   - Message: "Invalid status 'xyz'. Valid statuses: new, open, pending, hold, solved, closed"
   - Suggestions: Use valid status names, check spelling

**Error Message Format:**
```text
❌ Error: [Clear description of what went wrong]

💡 Suggestions:
   • [Actionable step 1]
   • [Actionable step 2]
   • [Actionable step 3]
```

### Development Implementation Guide

#### Test-Driven Development Strategy

**Testing Pyramid:**
```text
Unit Tests (70%):
- Model validation and computed properties
- Service layer business logic
- Utility functions (date calculations, formatting)
- CLI argument parsing
- Configuration validation

Integration Tests (20%):
- API client with mocked HTTP responses
- End-to-end command execution with mock data
- Configuration file handling
- Error scenarios and recovery

End-to-End Tests (10%):
- Complete workflows with real API (optional)
- Authentication flow testing
- Cross-platform compatibility
```

**TDD Implementation Phases:**

**Phase 1: Core Models**
1. Write tests for Ticket model validation
2. Implement Ticket model with computed properties
3. Write tests for date utility functions
4. Implement date calculations
5. Write tests for configuration model
6. Implement secure configuration management

**Phase 2: API Client**
1. Write tests for HTTP client with mocked responses
2. Implement basic HTTP client with authentication
3. Write tests for error handling scenarios
4. Implement comprehensive error handling and retry logic
5. Write tests for multi-status API call strategy
6. Implement multi-status handling

**Phase 3: Business Logic**
1. Write tests for ticket filtering and processing
2. Implement TicketService with filtering logic
3. Write tests for team name resolution
4. Implement group lookup and caching
5. Write tests for sorting functionality
6. Implement flexible sorting

**Phase 4: CLI Interface**
1. Write tests for command parsing and validation
2. Implement CLI commands with argument handling
3. Write tests for output formatting
4. Implement table and CSV formatters
5. Write tests for error message display
6. Implement user-friendly error handling

**Phase 5: Integration**
1. Write integration tests for complete workflows
2. Wire up all components
3. Write tests for configuration management
4. Implement secure credential storage
5. Write tests for platform compatibility
6. Final integration and polish

#### Quality Requirements

**Code Quality Standards:**
- Strong typing throughout the application
- Comprehensive input validation
- User-friendly error messages with actionable suggestions
- Consistent code formatting and organization
- Clear inline documentation

**Security Requirements:**
- Secure credential storage using system keyring
- Input sanitization and validation
- HTTPS-only API communication
- No secrets in logs or error messages
- Proper handling of API permission errors

**Performance Requirements:**
- CLI commands complete within reasonable time (< 10 seconds typical)
- Efficient API usage with caching where appropriate
- Minimal memory footprint
- Quick recovery from transient failures

#### Platform Considerations

**Cross-Platform Support:**
- Configuration file locations follow platform conventions
- Keyring integration works on Windows, macOS, Linux
- Path handling uses platform-appropriate separators
- Terminal formatting supports various terminal emulators

**Dependencies:**
- Minimal external dependencies
- Well-maintained libraries only
- Fallback behavior when optional dependencies unavailable
- Clear installation instructions for all platforms

## Implementation Technology Choices

While this specification is language-agnostic, here are technology considerations for different implementation approaches:

### Language Options

**Python:**
- Pros: Rich ecosystem (click, requests, rich, keyring), rapid development
- Cons: Runtime dependency, packaging complexity
- Best for: Rapid prototyping, rich CLI libraries

**Go:**
- Pros: Single binary, fast startup, excellent CLI support
- Cons: More verbose, smaller ecosystem
- Best for: Production deployment, performance-critical applications

**Node.js:**
- Pros: JSON-native, good CLI libraries, easy async handling
- Cons: Runtime dependency, security concerns
- Best for: Teams familiar with JavaScript

**Rust:**
- Pros: Single binary, memory safety, excellent performance
- Cons: Steeper learning curve, smaller ecosystem
- Best for: System tools, performance requirements

### Key Libraries/Dependencies

**CLI Framework:**
- Python: click, argparse
- Go: cobra, cli
- Node.js: commander, yargs
- Rust: clap, structopt

**HTTP Client:**
- Python: requests, httpx
- Go: net/http, resty
- Node.js: axios, node-fetch
- Rust: reqwest, hyper

**Table Formatting:**
- Python: rich, tabulate
- Go: tablewriter, termtables
- Node.js: cli-table3, table
- Rust: tabled, prettytable

**Secure Storage:**
- Python: keyring
- Go: keyring, go-keyring
- Node.js: keytar, node-keyring
- Rust: keyring

## Success Criteria

### Functional Requirements
- ✅ Successfully lists tickets with all required information
- ✅ Supports all specified filtering options (status, assignee, group)
- ✅ Provides flexible sorting by any column
- ✅ Exports results to properly formatted CSV
- ✅ Resolves team names from group IDs
- ✅ Handles multi-status filtering correctly (OR logic)

### User Experience Requirements
- ✅ Intuitive command-line interface
- ✅ Beautiful, readable table output
- ✅ Clear, actionable error messages
- ✅ Fast response times (< 10 seconds typical)
- ✅ Secure credential storage
- ✅ Cross-platform compatibility

### Technical Requirements
- ✅ Comprehensive test coverage (≥90%)
- ✅ Robust error handling for all scenarios
- ✅ Secure API token storage
- ✅ Efficient API usage with retry logic
- ✅ Clean, maintainable code architecture
- ✅ Clear documentation for users and developers

### Quality Gates
- All automated tests pass
- Static analysis passes (linting, type checking, security scans)
- Manual testing with real Zendesk API succeeds
- Cross-platform testing completed
- Security review passed
- Documentation complete and accurate
- Performance requirements met