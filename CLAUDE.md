# Zendesk CLI Tool - Implementation Plan

## Overview
A command-line utility to list open Zendesk tickets assigned to the user or their groups, displaying them in a tabular format with key information.

## Required Output Format
- Ticket number
- Team assigned the ticket  
- Ticket short description
- First opened date
- Days since opened
- Last updated date
- Days since updated
- Link to the Zendesk ticket

## API Research & Endpoints

### Primary Endpoints
1. **Tickets API**: `GET /api/v2/tickets.json`
   - Filters: `assignee_id`, `group_id`, `status`
   - Supports pagination via `page[size]` and `page[after]`
   - Returns: id, subject, description, status, created_at, updated_at, assignee_id, group_id

2. **Search API**: `GET /api/v2/search.json`
   - Query: `type:ticket assignee:me status:open` or `type:ticket group:{group_id} status:open`
   - More flexible filtering options
   - Returns similar ticket data structure

3. **Users API**: `GET /api/v2/users/me.json`
   - Get current user info including group memberships
   - Returns: id, name, email, group_ids

4. **Groups API**: `GET /api/v2/groups.json`
   - Get group information for display names
   - Returns: id, name, description

### Authentication Options

#### Option 1: API Token (Recommended for CLI)
- **Pros**: Simple setup, persistent, suitable for personal use
- **Cons**: Long-lived credentials
- **Implementation**: HTTP Basic Auth with `{email}/token:{api_token}`
- **Storage**: Store in config file or environment variable

#### Option 2: OAuth 2.0
- **Pros**: More secure, token expiration
- **Cons**: Complex setup, requires refresh token handling
- **Implementation**: Authorization code flow with PKCE
- **Storage**: Secure token storage with refresh capability

**Recommendation**: Start with API token for simplicity, add OAuth as enhancement.

## Technical Architecture

### Language & Framework
- **Python 3.11+** with modern packaging (pyproject.toml)
- **Core Libraries**:
  - `click` - CLI framework with decorators and type hints
  - `requests` - Simple HTTP client (familiar and reliable)
  - `pydantic` - Data validation and settings management
  - `rich` - Beautiful terminal output and tables
  - `keyring` - Secure credential storage

### Python Best Practices Applied

#### 1. Package Structure & Organization
- **src-layout**: Use `src/` directory to avoid import issues
- **Namespace packages**: Clear module hierarchy
- **__init__.py**: Explicit package definitions
- **Single responsibility**: One class/function per clear purpose

#### 2. Type Safety & Static Analysis
- **Full type hints**: All functions, methods, and variables
- **mypy strict mode**: Catch type errors before runtime
- **pydantic models**: Runtime validation with type safety
- **TypedDict**: For complex dictionary structures
- **Protocol classes**: For interface definitions

#### 3. Error Handling & Exceptions
- **Custom exception hierarchy**: Domain-specific errors
- **Exception chaining**: Preserve original error context
- **Fail fast principle**: Validate inputs early
- **Graceful degradation**: Handle API failures elegantly

#### 4. Code Quality & Standards
- **PEP 8 compliance**: Standard Python style guide
- **Black formatting**: Consistent code formatting
- **isort**: Organized imports
- **ruff**: Fast linting with modern rules
- **Docstrings**: Google/NumPy style documentation

#### 5. Testing Best Practices
- **Test pyramid**: Unit > Integration > E2E
- **Arrange-Act-Assert**: Clear test structure
- **Fixtures**: Reusable test data
- **Parametrized tests**: Multiple scenarios efficiently
- **Mock external dependencies**: Isolated unit tests

### Project Structure (Best Practices Applied)
```
zendesk-cli/
├── src/
│   └── zendesk_cli/
│       ├── __init__.py              # Package initialization, version
│       ├── models/
│       │   ├── __init__.py          # Export public models
│       │   ├── ticket.py            # Ticket domain model
│       │   ├── user.py              # User domain model
│       │   ├── group.py             # Group domain model
│       │   └── exceptions.py        # Custom exception hierarchy
│       ├── services/
│       │   ├── __init__.py          # Service layer exports
│       │   ├── protocols.py         # Interface definitions
│       │   ├── zendesk_client.py    # HTTP client (external API)
│       │   ├── auth_service.py      # Authentication logic
│       │   └── ticket_service.py    # Business logic for tickets
│       ├── cli/
│       │   ├── __init__.py          # CLI package init
│       │   ├── main.py              # CLI entry point and group
│       │   ├── commands/
│       │   │   ├── __init__.py      # Commands package
│       │   │   ├── tickets.py       # Ticket-related commands
│       │   │   └── configure.py     # Configuration commands
│       │   ├── formatters.py        # Output formatting logic
│       │   └── validators.py        # Input validation
│       ├── utils/
│       │   ├── __init__.py          # Utilities package
│       │   ├── config.py            # Configuration management
│       │   ├── date_utils.py        # Date/time utilities
│       │   └── logging.py           # Logging configuration
│       └── py.typed                 # Mark package as typed
├── tests/
│   ├── __init__.py                  # Test package
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_models.py           # Model validation tests
│   │   ├── test_services.py         # Service logic tests
│   │   └── test_utils.py            # Utility function tests
│   ├── integration/
│   │   ├── test_zendesk_client.py   # API integration tests
│   │   └── test_cli_commands.py     # CLI integration tests
│   └── fixtures/
│       ├── api_responses.json       # Mock API responses
│       └── sample_data.py           # Test data factories
├── docs/                            # Documentation
│   ├── api.md                       # API documentation
│   ├── installation.md              # Installation guide
│   └── usage.md                     # Usage examples
├── scripts/                         # Development scripts
│   ├── setup-dev.sh                 # Development environment setup
│   └── release.py                   # Release automation
├── pyproject.toml                   # Modern Python packaging
├── pytest.ini                      # Test configuration
├── mypy.ini                         # Type checking configuration
├── ruff.toml                        # Linting configuration
├── .pre-commit-config.yaml          # Git hooks configuration
├── .gitignore                       # Git ignore rules
├── README.md                        # Project documentation
└── CHANGELOG.md                     # Version history
```

### Data Models (Best Practices Examples)

#### Domain Models with Full Type Safety
```python
# src/zendesk_cli/models/ticket.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator, root_validator

TicketStatus = Literal["new", "open", "pending", "hold", "solved", "closed"]

class Ticket(BaseModel):
    """Zendesk ticket domain model.
    
    Represents a support ticket with all relevant metadata
    for display and processing.
    """
    id: int = Field(..., description="Unique ticket identifier")
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., description="Ticket description/content")
    status: TicketStatus = Field(..., description="Current ticket status")
    created_at: datetime = Field(..., description="Ticket creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    assignee_id: Optional[int] = Field(None, description="Assigned user ID")
    group_id: Optional[int] = Field(None, description="Assigned group ID")
    url: str = Field(..., description="Direct link to ticket")
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Immutable
        use_enum_values = True
        validate_assignment = True
        
    @validator('updated_at')
    def updated_at_after_created_at(cls, v: datetime, values: dict) -> datetime:
        """Ensure updated_at is after created_at."""
        if 'created_at' in values and v < values['created_at']:
            raise ValueError('updated_at must be after created_at')
        return v
        
    @property
    def short_description(self) -> str:
        """Get truncated description for display."""
        return self.description[:50] + "..." if len(self.description) > 50 else self.description
        
    @property
    def days_since_created(self) -> int:
        """Calculate days since ticket creation."""
        from ..utils.date_utils import days_between
        return days_between(self.created_at, datetime.now())
        
    @property
    def days_since_updated(self) -> int:
        """Calculate days since last update."""
        from ..utils.date_utils import days_between
        return days_between(self.updated_at, datetime.now())

# src/zendesk_cli/models/exceptions.py  
class ZendeskCliError(Exception):
    """Base exception for all zendesk-cli errors."""
    pass

class AuthenticationError(ZendeskCliError):
    """Raised when authentication fails."""
    pass

class APIError(ZendeskCliError):
    """Raised when Zendesk API returns an error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class ConfigurationError(ZendeskCliError):
    """Raised when configuration is invalid or missing."""
    pass
```

#### Interface Definitions with Protocols
```python
# src/zendesk_cli/services/protocols.py
from __future__ import annotations

from typing import Protocol, List, Optional
from ..models.ticket import Ticket
from ..models.user import User

class TicketRepository(Protocol):
    """Protocol for ticket data access."""
    
    def get_tickets_for_user(self, user_id: int) -> List[Ticket]:
        """Get all tickets assigned to a user."""
        ...
        
    def get_tickets_for_group(self, group_id: int) -> List[Ticket]:
        """Get all tickets assigned to a group."""
        ...

class AuthService(Protocol):
    """Protocol for authentication services."""
    
    def get_current_user(self) -> User:
        """Get the currently authenticated user."""
        ...
        
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        ...
```

## Test-Driven Development Strategy

### Testing Pyramid
1. **Unit Tests (70%)**: Fast, isolated tests for business logic
2. **Integration Tests (20%)**: Test component interactions
3. **E2E Tests (10%)**: Full workflow testing

### TDD Cycle for Each Feature
1. **Red**: Write failing test first
2. **Green**: Implement minimum code to pass
3. **Refactor**: Improve code while keeping tests green

### Testing Framework & Tools (Best Practices)
- **pytest**: Modern testing framework with excellent plugin ecosystem
- **pytest-mock**: Clean mocking with automatic cleanup
- **responses**: HTTP request mocking with realistic responses
- **coverage.py**: Code coverage with branch analysis
- **pytest-cov**: Coverage integration for pytest
- **pytest-xdist**: Parallel test execution
- **factory-boy**: Test data generation
- **freezegun**: Time-based testing

### Test Structure (Best Practices Examples)
```python
# tests/conftest.py - Shared fixtures
import pytest
from datetime import datetime
from zendesk_cli.models.ticket import Ticket

@pytest.fixture
def sample_ticket() -> Ticket:
    """Create a sample ticket for testing."""
    return Ticket(
        id=12345,
        subject="Test ticket",
        description="This is a test ticket for our CLI",
        status="open",
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 2, 15, 30, 0),
        assignee_id=123,
        group_id=456,
        url="https://example.zendesk.com/tickets/12345"
    )

# tests/unit/test_models.py - Model validation tests
import pytest
from datetime import datetime
from pydantic import ValidationError
from zendesk_cli.models.ticket import Ticket

class TestTicketModel:
    """Test Ticket model validation and behavior."""
    
    def test_ticket_creation_with_valid_data(self, sample_ticket):
        """Test creating ticket with valid data."""
        assert sample_ticket.id == 12345
        assert sample_ticket.subject == "Test ticket"
        assert sample_ticket.status == "open"
    
    def test_ticket_validation_fails_with_invalid_status(self):
        """Test ticket validation fails with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            Ticket(
                id=1,
                subject="Test",
                description="Test description",
                status="invalid_status",  # Invalid status
                created_at=datetime.now(),
                updated_at=datetime.now(),
                url="https://example.com"
            )
        assert "status" in str(exc_info.value)
    
    @pytest.mark.parametrize("description,expected", [
        ("Short description", "Short description"),
        ("This is a very long description that should be truncated", 
         "This is a very long description that should be t..."),
    ])
    def test_short_description_property(self, description, expected):
        """Test short_description property truncation."""
        ticket = Ticket(
            id=1,
            subject="Test",
            description=description,
            status="open",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            url="https://example.com"
        )
        assert ticket.short_description == expected

# tests/unit/test_services.py - Service logic tests
from unittest.mock import Mock, patch
import pytest
import responses
from zendesk_cli.services.ticket_service import TicketService
from zendesk_cli.models.exceptions import APIError

class TestTicketService:
    """Test TicketService business logic."""
    
    @pytest.fixture
    def ticket_service(self):
        """Create ticket service with mocked dependencies."""
        mock_client = Mock()
        return TicketService(client=mock_client)
    
    def test_get_user_tickets_returns_filtered_list(self, ticket_service, sample_ticket):
        """Test getting tickets for specific user."""
        # Arrange
        ticket_service.client.get_tickets.return_value = [sample_ticket]
        
        # Act
        tickets = ticket_service.get_user_tickets(user_id=123)
        
        # Assert
        assert len(tickets) == 1
        assert tickets[0].assignee_id == 123
        ticket_service.client.get_tickets.assert_called_once()
    
    @responses.activate
    def test_api_error_handling(self, ticket_service):
        """Test proper error handling for API failures."""
        # Arrange
        responses.add(
            responses.GET,
            "https://example.zendesk.com/api/v2/tickets.json",
            status=500,
            json={"error": "Internal server error"}
        )
        
        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            ticket_service.get_user_tickets(user_id=123)
        assert exc_info.value.status_code == 500
```

## Implementation Plan (TDD Approach)

### Phase 1: Core Models (Test-First)
1. **Test**: Write tests for Ticket model validation
2. **Implement**: Create Ticket, User, Group models with Pydantic
3. **Test**: Write tests for date calculation utilities
4. **Implement**: Create date utilities for days-since calculations

### Phase 2: Zendesk Client (Test-First)
1. **Test**: Write tests for HTTP client operations (mocked)
2. **Implement**: Create ZendeskClient with requests library
3. **Test**: Write tests for authentication handling
4. **Implement**: Add API token and OAuth support
5. **Refactor**: Add proper error handling

### Phase 3: Business Logic (Test-First)
1. **Test**: Write tests for TicketService (filtering, processing)
2. **Implement**: Create TicketService to fetch and process tickets
3. **Test**: Write tests for AuthService
4. **Implement**: Create AuthService for credential management

### Phase 4: CLI Interface (Test-First)
1. **Test**: Write tests for CLI command parsing
2. **Implement**: Create Click commands for tickets and configure
3. **Test**: Write tests for table formatting
4. **Implement**: Create Rich table formatter
5. **Refactor**: Add user-friendly error messages

### Phase 5: Integration (Test-First)
1. **Test**: Write integration tests with mocked Zendesk API
2. **Implement**: Wire up all components in main.py
3. **Test**: Write end-to-end CLI tests
4. **Implement**: Add configuration file support
5. **Refactor**: Polish and optimize

## Modern Python Development Practices

### Code Quality Tools & Configuration

#### Development Dependencies (pyproject.toml)
```toml
[build-system]
requires = ["hatchling>=1.12.2"]
build-backend = "hatchling.build"

[project]
name = "zendesk-cli"
version = "0.1.0"
description = "CLI tool for managing Zendesk tickets"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "requests>=2.31.0",
    "pydantic>=2.5.0",
    "rich>=13.7.0",
    "keyring>=24.3.0",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "responses>=0.24.0",
    "factory-boy>=3.3.0",
    "freezegun>=1.2.0",
    
    # Code Quality
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "black>=23.11.0",
    "isort>=5.12.0",
    "bandit>=1.7.0",
    "pre-commit>=3.6.0",
    
    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
]

[project.scripts]
zendesk = "zendesk_cli.cli.main:main"

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "S",   # bandit
]
ignore = [
    "E501",  # line too long (handled by black)
    "S101",  # assert statements (fine for tests)
]

[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["S101", "S105", "S106"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true

[tool.black]
target-version = ['py311']
line-length = 88

[tool.isort]
profile = "black"
multi_line_output = 3
```

#### Pre-commit Configuration (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
      
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
      
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-requests]
```

### Configuration Management (Best Practices)
```python
# src/zendesk_cli/utils/config.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, validator
import keyring

class ZendeskConfig(BaseModel):
    """Zendesk CLI configuration."""
    
    domain: str = Field(..., description="Zendesk domain (e.g., company.zendesk.com)")
    email: str = Field(..., description="User email for authentication")
    api_token: Optional[str] = Field(None, description="API token (stored securely)")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        
    @validator('domain')
    def validate_domain(cls, v: str) -> str:
        """Ensure domain is properly formatted."""
        if not v.endswith('.zendesk.com'):
            if '.' not in v:
                v = f"{v}.zendesk.com"
        return v.lower()
        
    @classmethod
    def from_file(cls, config_path: Optional[Path] = None) -> ZendeskConfig:
        """Load configuration from file."""
        if config_path is None:
            config_path = cls.get_default_config_path()
            
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
            
        import json
        with open(config_path) as f:
            data = json.load(f)
            
        # Load API token from keyring if not in file
        if 'api_token' not in data:
            data['api_token'] = keyring.get_password(
                "zendesk-cli", 
                data.get('email', '')
            )
            
        return cls(**data)
        
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file (excluding sensitive data)."""
        if config_path is None:
            config_path = self.get_default_config_path()
            
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save API token to keyring
        if self.api_token:
            keyring.set_password("zendesk-cli", self.email, self.api_token)
            
        # Save non-sensitive config to file
        config_data = {
            "domain": self.domain,
            "email": self.email,
        }
        
        import json
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    @staticmethod
    def get_default_config_path() -> Path:
        """Get default configuration file path."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', '')) / 'zendesk-cli'
        else:  # Unix-like
            config_dir = Path.home() / '.config' / 'zendesk-cli'
        return config_dir / 'config.json'
```

### Logging Configuration (Best Practices)
```python
# src/zendesk_cli/utils/logging.py
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False
) -> None:
    """Configure application logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file to write logs to
        verbose: Enable verbose console output
    """
    # Configure root logger
    root_logger = logging.getLogger("zendesk_cli")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s" if not verbose 
        else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
```

### Error Handling Best Practices
```python
# src/zendesk_cli/models/exceptions.py
from __future__ import annotations

from typing import Optional, Dict, Any

class ZendeskCliError(Exception):
    """Base exception for zendesk-cli with enhanced error context."""
    
    def __init__(
        self, 
        message: str, 
        *,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None
    ):
        super().__init__(message)
        self.details = details or {}
        self.suggestions = suggestions or []
        
    def __str__(self) -> str:
        """Enhanced string representation with suggestions."""
        msg = super().__str__()
        if self.suggestions:
            msg += f"\n\nSuggestions:\n" + "\n".join(f"  • {s}" for s in self.suggestions)
        return msg

class AuthenticationError(ZendeskCliError):
    """Authentication-related errors with helpful suggestions."""
    
    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Check your API token is correct",
            "Verify your email address", 
            "Run 'zendesk configure' to update credentials"
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)

class APIError(ZendeskCliError):
    """API-related errors with status code context."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = {"status_code": status_code}
        if response_data:
            details["response"] = response_data
            
        suggestions = []
        if status_code == 401:
            suggestions.extend([
                "Check your authentication credentials",
                "Your API token may have expired"
            ])
        elif status_code == 403:
            suggestions.append("You may not have permission to access this resource")
        elif status_code == 429:
            suggestions.append("Rate limit exceeded - please wait and try again")
            
        super().__init__(message, details=details, suggestions=suggestions, **kwargs)
        self.status_code = status_code
```

### CLI Interface Design

### CLI Features
```bash
# Rich help output with colors and formatting
zendesk --help

# List tickets (main functionality)
zendesk tickets

# Interactive configuration
zendesk configure

# Basic filtering
zendesk tickets --assignee-only
zendesk tickets --group "Support Team"
```

## Security & Performance

### Security Best Practices
- Secure credential storage with keyring
- Input validation with Pydantic
- No secrets in logs or error messages
- HTTPS certificate validation

### Performance Considerations
- Simple synchronous requests (easier to debug)
- Basic caching for group/user lookups
- Reasonable timeout values
- Clean error handling

## Quality Gates

### Definition of Done (Python Best Practices)
- [ ] All tests pass (unit + integration)
- [ ] Code coverage ≥ 90% with branch coverage
- [ ] Type checking passes with mypy --strict
- [ ] All linting passes (ruff, black, isort)
- [ ] Security scan passes (bandit)
- [ ] Pre-commit hooks pass
- [ ] Documentation is complete and accurate
- [ ] Manual testing with real Zendesk API
- [ ] Error messages are user-friendly with suggestions
- [ ] Configuration follows XDG Base Directory spec
- [ ] Logging is properly configured
- [ ] Package follows modern Python packaging standards

### Continuous Quality Practices
- **Pre-commit hooks**: Prevent bad commits automatically
- **GitHub Actions CI**: Automated testing and quality checks
- **Dependabot**: Automated dependency updates
- **Code review**: All changes reviewed before merge
- **Semantic versioning**: Clear version management
- **Changelog**: Documented changes for each release

### Development Workflow (Best Practices)
```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
pre-commit install

# TDD workflow
pytest --watch  # Run tests continuously during development
mypy src/       # Type checking
ruff check src/ # Linting
black src/      # Code formatting

# Before committing
pre-commit run --all-files  # Run all quality checks
pytest --cov=src --cov-report=html  # Generate coverage report
```

## Success Criteria (Python Excellence)
- ✅ **TDD throughout**: Red-Green-Refactor cycle for all features
- ✅ **Type safety**: Full type hints with strict mypy checking
- ✅ **Code quality**: Modern tooling (ruff, black, isort) with automation
- ✅ **Testing excellence**: High coverage with comprehensive test suite
- ✅ **Error handling**: User-friendly errors with actionable suggestions
- ✅ **Security**: Secure credential storage and input validation
- ✅ **Performance**: Efficient API usage with proper retry logic
- ✅ **Maintainability**: Clear structure following Python conventions
- ✅ **Documentation**: Comprehensive docstrings and user guides
- ✅ **Packaging**: Modern pyproject.toml with proper dependency management
- ✅ **Developer experience**: Easy setup with excellent tooling integration
- ✅ **Production ready**: Robust error handling and logging