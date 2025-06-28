"""Zendesk API client for HTTP operations."""

from __future__ import annotations

import base64
import logging
import time
from typing import List, Dict, Any, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ..models.ticket import Ticket
from ..models.exceptions import (
    APIError, 
    AuthenticationError, 
    NetworkError, 
    RateLimitError,
    TimeoutError
)

logger = logging.getLogger(__name__)


class ZendeskClient:
    """HTTP client for Zendesk API operations."""
    
    def __init__(
        self, 
        domain: str, 
        email: str, 
        api_token: str,
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> None:
        """Initialize the Zendesk client.
        
        Args:
            domain: Zendesk domain (e.g., "company.zendesk.com")
            email: User email for authentication
            api_token: API token for authentication
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        if not domain or not email or not api_token:
            raise ValueError("Domain, email, and API token are required")
            
        self.domain = domain
        self.email = email
        self._api_token = api_token
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        
        # Configure retry strategy for transient failures
        try:
            # Try newer urllib3 parameter name first
            retry_strategy = Retry(
                total=self._max_retries,
                status_forcelist=[408, 429, 500, 502, 503, 504],  # Retry on these HTTP codes
                allowed_methods=["HEAD", "GET", "OPTIONS"],  # Only retry safe methods
                backoff_factor=1.0,  # Wait 1s, 2s, 4s between retries
                raise_on_status=False  # Don't raise exception, let us handle it
            )
        except TypeError:
            # Fall back to older urllib3 parameter name
            retry_strategy = Retry(
                total=self._max_retries,
                status_forcelist=[408, 429, 500, 502, 503, 504],  # Retry on these HTTP codes
                method_whitelist=["HEAD", "GET", "OPTIONS"],  # Only retry safe methods
                backoff_factor=1.0,  # Wait 1s, 2s, 4s between retries
                raise_on_status=False  # Don't raise exception, let us handle it
            )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
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
        params: Optional[Dict[str, Any]] = None,
        retry_on_rate_limit: bool = True
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Zendesk API with comprehensive error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "tickets.json")
            params: Optional query parameters
            retry_on_rate_limit: Whether to retry on rate limit errors
            
        Returns:
            JSON response data
            
        Raises:
            AuthenticationError: If authentication fails (401)
            RateLimitError: If rate limited (429)
            NetworkError: For network connectivity issues
            TimeoutError: For request timeouts
            APIError: For other API errors
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_auth_headers()
        
        # Rate limiting retry logic
        max_rate_limit_retries = 3 if retry_on_rate_limit else 0
        rate_limit_attempts = 0
        
        while True:
            try:
                logger.debug(f"Making {method} request to {url}")
                
                response = self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    timeout=self._timeout
                )
                
                # Handle authentication errors
                if response.status_code == 401:
                    logger.error("Authentication failed")
                    raise AuthenticationError(
                        "Authentication failed. Please check your email and API token."
                    )
                
                # Handle rate limiting with retry logic
                if response.status_code == 429:
                    retry_after = self._parse_retry_after(response)
                    
                    if rate_limit_attempts < max_rate_limit_retries:
                        rate_limit_attempts += 1
                        wait_time = retry_after or (2 ** rate_limit_attempts)  # Exponential backoff
                        logger.warning(f"Rate limited. Retrying in {wait_time} seconds (attempt {rate_limit_attempts}/{max_rate_limit_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limit exceeded, max retries reached")
                        raise RateLimitError(
                            "Rate limit exceeded. Please wait before making more requests.",
                            retry_after=retry_after
                        )
                
                # Handle other client/server errors
                if not response.ok:
                    error_data = self._parse_error_response(response)
                    error_message = self._build_error_message(response, error_data)
                    
                    logger.error(f"API error: {response.status_code} - {error_message}")
                    
                    # Specific error types based on status code
                    if response.status_code == 403:
                        raise APIError(
                            f"Access forbidden: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                    elif 500 <= response.status_code < 600:
                        raise APIError(
                            f"Server error: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                    else:
                        raise APIError(
                            f"API request failed: {error_message}",
                            status_code=response.status_code,
                            response_data=error_data
                        )
                
                # Success - parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Request successful, received {len(str(result))} bytes")
                    return result
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    raise APIError(f"Invalid JSON response from server: {e}") from e
            
            except requests.exceptions.Timeout as e:
                logger.error(f"Request timeout after {self._timeout} seconds")
                raise TimeoutError(
                    f"Request timed out after {self._timeout} seconds",
                    timeout_duration=self._timeout
                ) from e
            
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise NetworkError(f"Failed to connect to {self.domain}: {e}") from e
            
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL error: {e}")
                raise NetworkError(f"SSL/TLS error connecting to {self.domain}: {e}") from e
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Unexpected request error: {e}")
                raise NetworkError(f"Network error: {e}") from e
    
    def _parse_retry_after(self, response: requests.Response) -> Optional[int]:
        """Parse Retry-After header from response.
        
        Args:
            response: HTTP response object
            
        Returns:
            Number of seconds to wait, or None if not specified
        """
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                logger.warning(f"Invalid Retry-After header: {retry_after}")
        return None
    
    def _parse_error_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """Parse error response body safely.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed error data or None if parsing fails
        """
        try:
            return response.json()
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse error response as JSON: {e}")
            return None
    
    def _build_error_message(
        self, 
        response: requests.Response, 
        error_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build a comprehensive error message from response.
        
        Args:
            response: HTTP response object
            error_data: Parsed error data from response body
            
        Returns:
            Formatted error message
        """
        base_message = f"{response.status_code} {response.reason}"
        
        if error_data:
            # Try to extract meaningful error message from response
            if isinstance(error_data, dict):
                error_msg = (
                    error_data.get('error') or 
                    error_data.get('message') or
                    error_data.get('description')
                )
                if error_msg:
                    base_message += f": {error_msg}"
                    
                # Add details if available
                if 'details' in error_data:
                    details = error_data['details']
                    if isinstance(details, dict):
                        detail_parts = [f"{k}: {v}" for k, v in details.items()]
                        if detail_parts:
                            base_message += f" ({', '.join(detail_parts)})"
        
        return base_message
    
    def get_tickets(
        self, 
        assignee_id: Optional[int] = None,
        group_id: Optional[int] = None,
        status: Optional[Union[str, List[str]]] = None
    ) -> List[Ticket]:
        """Get tickets from Zendesk API.
        
        Args:
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID  
            status: Filter by status (single status or list of statuses)
            
        Returns:
            List of Ticket objects
        """
        # Use Search API for complex filtering including status
        if status is not None or assignee_id is not None or group_id is not None:
            # Handle multiple statuses by making separate calls and combining results
            if isinstance(status, list) and len(status) > 1:
                logger.debug(f"Searching for tickets with multiple statuses: {status}")
                all_tickets = []
                ticket_ids_seen = set()
                
                for single_status in status:
                    logger.debug(f"Searching for tickets with status: {single_status}")
                    status_tickets = self._search_tickets(
                        assignee_id=assignee_id, 
                        group_id=group_id, 
                        status=single_status
                    )
                    logger.debug(f"Found {len(status_tickets)} tickets with status '{single_status}'")
                    for ticket in status_tickets:
                        if ticket.id not in ticket_ids_seen:
                            all_tickets.append(ticket)
                            ticket_ids_seen.add(ticket.id)
                
                logger.debug(f"Combined results: {len(all_tickets)} unique tickets")
                # Sort by creation date (newest first) for consistent output
                return sorted(all_tickets, key=lambda t: t.created_at, reverse=True)
            else:
                return self._search_tickets(assignee_id=assignee_id, group_id=group_id, status=status)
        
        # Fallback to basic tickets endpoint for simple listing
        response_data = self._make_request("GET", "tickets.json", {})
        
        tickets = []
        for ticket_data in response_data.get("tickets", []):
            # Always use human-readable ticket URL instead of API URL
            ticket_data["url"] = f"https://{self.domain}/agent/tickets/{ticket_data['id']}"
            
            tickets.append(Ticket(**ticket_data))
        
        logger.debug(f"Retrieved {len(tickets)} tickets")
        return tickets
    
    def _search_tickets(
        self,
        assignee_id: Optional[int] = None,
        group_id: Optional[int] = None,
        status: Optional[Union[str, List[str]]] = None
    ) -> List[Ticket]:
        """Search for tickets using Zendesk Search API.
        
        Args:
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID  
            status: Filter by status (single status or list of statuses)
            
        Returns:
            List of Ticket objects
        """
        # Build search query
        query_parts = ["type:ticket"]
        
        if status is not None:
            if isinstance(status, list):
                if len(status) == 1:
                    query_parts.append(f"status:{status[0]}")
                else:
                    # For multiple statuses, we'll handle this differently
                    # to avoid issues with OR syntax - we'll make separate calls
                    # and combine results in the parent method
                    pass  # Handle multiple statuses in calling method
            else:
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
        
        logger.debug(f"Retrieved {len(tickets)} tickets")
        return tickets
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get information about the current authenticated user.
        
        Returns:
            User data dictionary
        """
        response_data = self._make_request("GET", "users/me.json")
        return response_data["user"]