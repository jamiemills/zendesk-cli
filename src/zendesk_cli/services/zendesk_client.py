"""Zendesk API client for HTTP operations."""

from __future__ import annotations

import base64
import logging
from typing import List, Dict, Any, Optional

import requests

from ..models.ticket import Ticket
from ..models.exceptions import APIError, AuthenticationError

logger = logging.getLogger(__name__)


class ZendeskClient:
    """HTTP client for Zendesk API operations."""
    
    def __init__(self, domain: str, email: str, api_token: str) -> None:
        """Initialize the Zendesk client.
        
        Args:
            domain: Zendesk domain (e.g., "company.zendesk.com")
            email: User email for authentication
            api_token: API token for authentication
        """
        self.domain = domain
        self.email = email
        self._api_token = api_token
        self._timeout = 30.0  # 30 second timeout
    
    @property
    def base_url(self) -> str:
        """Get the base API URL."""
        return f"https://{self.domain}/api/v2"
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        credentials = f"{self.email}/token:{self._api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Zendesk API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "tickets.json")
            params: Optional query parameters
            
        Returns:
            JSON response data
            
        Raises:
            AuthenticationError: If authentication fails (401)
            APIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_auth_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=self._timeout
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your email and API token."
                )
            
            # Handle other API errors
            if not response.ok:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    pass
                    
                raise APIError(
                    f"API request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response_data=error_data
                )
            
            return response.json()
            
        except requests.RequestException as e:
            raise APIError(f"Network error: {e}") from e
    
    def get_tickets(
        self, 
        assignee_id: Optional[int] = None,
        group_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Ticket]:
        """Get tickets from Zendesk API.
        
        Args:
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID  
            status: Filter by status
            
        Returns:
            List of Ticket objects
        """
        # Use Search API for complex filtering including status
        if status is not None or assignee_id is not None or group_id is not None:
            return self._search_tickets(assignee_id=assignee_id, group_id=group_id, status=status)
        
        # Fallback to basic tickets endpoint for simple listing
        response_data = self._make_request("GET", "tickets.json", {})
        
        tickets = []
        for ticket_data in response_data.get("tickets", []):
            # Always use human-readable ticket URL instead of API URL
            ticket_data["url"] = f"https://{self.domain}/agent/tickets/{ticket_data['id']}"
            
            tickets.append(Ticket(**ticket_data))
        
        logger.info(f"Retrieved {len(tickets)} tickets")
        return tickets
    
    def _search_tickets(
        self,
        assignee_id: Optional[int] = None,
        group_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Ticket]:
        """Search for tickets using Zendesk Search API.
        
        Args:
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID  
            status: Filter by status
            
        Returns:
            List of Ticket objects
        """
        # Build search query
        query_parts = ["type:ticket"]
        
        if status is not None:
            query_parts.append(f"status:{status}")
        
        if assignee_id is not None:
            query_parts.append(f"assignee:{assignee_id}")
            
        if group_id is not None:
            query_parts.append(f"group:{group_id}")
        
        query = " ".join(query_parts)
        params = {"query": query}
        
        logger.debug(f"Searching tickets with query: {query}")
        
        response_data = self._make_request("GET", "search.json", params)
        
        tickets = []
        for ticket_data in response_data.get("results", []):
            # Always use human-readable ticket URL instead of API URL
            ticket_data["url"] = f"https://{self.domain}/agent/tickets/{ticket_data['id']}"
            
            tickets.append(Ticket(**ticket_data))
        
        logger.info(f"Retrieved {len(tickets)} tickets")
        return tickets
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get information about the current authenticated user.
        
        Returns:
            User data dictionary
        """
        response_data = self._make_request("GET", "users/me.json")
        return response_data["user"]