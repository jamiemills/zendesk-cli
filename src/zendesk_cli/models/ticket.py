"""Ticket domain model for zendesk-cli."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator

from ..utils.date_utils import days_between, parse_zendesk_datetime

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
        
    @validator('created_at', pre=True)
    def parse_created_at(cls, v):
        """Parse created_at datetime string."""
        if isinstance(v, str):
            return parse_zendesk_datetime(v)
        return v
        
    @validator('updated_at', pre=True)
    def parse_updated_at(cls, v):
        """Parse updated_at datetime string."""
        if isinstance(v, str):
            return parse_zendesk_datetime(v)
        return v
        
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
        return days_between(self.created_at, datetime.now())
        
    @property
    def days_since_updated(self) -> int:
        """Calculate days since last update."""
        return days_between(self.updated_at, datetime.now())