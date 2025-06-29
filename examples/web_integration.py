#!/usr/bin/env python3
"""
TicketQ Web Integration Examples

This file demonstrates how to integrate TicketQ into web applications using
popular Python web frameworks like Flask and FastAPI.

Prerequisites:
- Install TicketQ: pip install "ticketq[cli]"
- Install adapter: pip install ticketq-zendesk
- Configure adapter: tq configure --adapter zendesk
- Install web framework: pip install flask OR pip install fastapi[all]
"""

import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Try importing web frameworks
try:
    from flask import Flask, jsonify, request, render_template_string, send_file
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
    from fastapi.responses import JSONResponse, FileResponse
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ticketq import TicketQLibrary
from ticketq.lib.models import LibraryTicket
from ticketq.models.exceptions import (
    TicketQError, AuthenticationError, NetworkError, ConfigurationError
)


# ============================================================================
# FLASK INTEGRATION EXAMPLES
# ============================================================================

def create_flask_app() -> Flask:
    """Create a Flask application with TicketQ integration."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask not installed. Install with: pip install flask")
    
    app = Flask(__name__)
    
    # Initialize TicketQ (you might want to make this configurable)
    try:
        tq = TicketQLibrary.from_config()
        adapter_info = tq.get_adapter_info()
        print(f"✅ Flask app initialized with {adapter_info['display_name']} adapter")
    except Exception as e:
        print(f"❌ Failed to initialize TicketQ: {e}")
        tq = None
    
    @app.errorhandler(Exception)
    def handle_error(error):
        """Global error handler for TicketQ exceptions."""
        if isinstance(error, AuthenticationError):
            return jsonify({
                'error': 'Authentication failed',
                'message': str(error),
                'suggestions': getattr(error, 'suggestions', [])
            }), 401
        elif isinstance(error, NetworkError):
            return jsonify({
                'error': 'Network error',
                'message': str(error),
                'suggestions': getattr(error, 'suggestions', [])
            }), 503
        elif isinstance(error, TicketQError):
            return jsonify({
                'error': 'TicketQ error',
                'message': str(error),
                'suggestions': getattr(error, 'suggestions', [])
            }), 400
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': str(error)
            }), 500
    
    @app.route('/')
    def home():
        """Home page with API documentation."""
        if not tq:
            return "TicketQ not configured. Please configure an adapter first.", 500
        
        adapter_info = tq.get_adapter_info()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TicketQ Web API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold; }
                .get { background: #61affe; }
                .post { background: #49cc90; }
                code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🎫 TicketQ Web API</h1>
            <p>Connected to: <strong>{{ adapter_name }}</strong> ({{ adapter_version }})</p>
            
            <h2>📋 Available Endpoints</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/tickets</code>
                <p>Get tickets with optional filtering</p>
                <p>Parameters: status, assignee_only, groups, sort_by, limit</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/tickets/{id}</code>
                <p>Get a specific ticket by ID</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/user</code>
                <p>Get current authenticated user information</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/groups</code>
                <p>Get all available groups/teams</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/search</code>
                <p>Search tickets with adapter-specific query</p>
                <p>Parameters: q (query string)</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/export</code>
                <p>Export tickets to CSV with optional filtering</p>
                <p>Parameters: same as /api/tickets, returns CSV file</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/stats</code>
                <p>Get ticket statistics and adapter information</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/test</code>
                <p>Test the connection to the ticketing system</p>
            </div>
            
            <h2>🔍 Example Usage</h2>
            <pre>
# Get all open tickets
curl http://localhost:5000/api/tickets?status=open

# Get tickets assigned to current user
curl http://localhost:5000/api/tickets?assignee_only=true

# Get tickets by team
curl http://localhost:5000/api/tickets?groups=Support%20Team

# Export filtered tickets to CSV
curl http://localhost:5000/api/export?status=open,pending -o tickets.csv

# Search tickets
curl http://localhost:5000/api/search?q=login%20issue
            </pre>
        </body>
        </html>
        """
        
        return render_template_string(
            html_template,
            adapter_name=adapter_info['display_name'],
            adapter_version=adapter_info['version']
        )
    
    @app.route('/api/tickets')
    def get_tickets():
        """Get tickets with optional filtering."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            # Parse query parameters
            status = request.args.get('status', 'open')
            if ',' in status:
                status = status.split(',')
            
            assignee_only = request.args.get('assignee_only', 'false').lower() == 'true'
            groups = request.args.get('groups')
            if groups and ',' in groups:
                groups = groups.split(',')
            elif groups:
                groups = [groups]
            
            sort_by = request.args.get('sort_by')
            limit = request.args.get('limit', type=int)
            
            # Get tickets
            tickets = tq.get_tickets(
                status=status,
                assignee_only=assignee_only,
                groups=groups,
                sort_by=sort_by
            )
            
            # Apply limit if specified
            if limit:
                tickets = tickets[:limit]
            
            # Convert to dictionaries for JSON serialization
            tickets_data = [ticket.dict() for ticket in tickets]
            
            adapter_info = tq.get_adapter_info()
            
            return jsonify({
                'success': True,
                'count': len(tickets_data),
                'adapter': adapter_info['name'],
                'tickets': tickets_data,
                'filters': {
                    'status': status,
                    'assignee_only': assignee_only,
                    'groups': groups,
                    'sort_by': sort_by,
                    'limit': limit
                }
            })
            
        except Exception as e:
            raise  # Will be handled by global error handler
    
    @app.route('/api/tickets/<ticket_id>')
    def get_ticket(ticket_id: str):
        """Get a specific ticket by ID."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            ticket = tq.get_ticket(ticket_id)
            
            if ticket:
                return jsonify({
                    'success': True,
                    'ticket': ticket.dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Ticket {ticket_id} not found'
                }), 404
                
        except Exception as e:
            raise
    
    @app.route('/api/user')
    def get_current_user():
        """Get current authenticated user."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            user = tq.get_current_user()
            
            if user:
                return jsonify({
                    'success': True,
                    'user': user.dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unable to get current user'
                }), 404
                
        except Exception as e:
            raise
    
    @app.route('/api/groups')
    def get_groups():
        """Get all available groups."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            groups = tq.get_groups()
            groups_data = [group.dict() for group in groups]
            
            return jsonify({
                'success': True,
                'count': len(groups_data),
                'groups': groups_data
            })
            
        except Exception as e:
            raise
    
    @app.route('/api/search')
    def search_tickets():
        """Search tickets with adapter-specific query."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        try:
            tickets = tq.search_tickets(query)
            tickets_data = [ticket.dict() for ticket in tickets]
            
            return jsonify({
                'success': True,
                'query': query,
                'count': len(tickets_data),
                'tickets': tickets_data
            })
            
        except Exception as e:
            raise
    
    @app.route('/api/export')
    def export_tickets():
        """Export tickets to CSV."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            # Use same filtering logic as get_tickets
            status = request.args.get('status', 'open')
            if ',' in status:
                status = status.split(',')
            
            assignee_only = request.args.get('assignee_only', 'false').lower() == 'true'
            groups = request.args.get('groups')
            if groups and ',' in groups:
                groups = groups.split(',')
            elif groups:
                groups = [groups]
            
            sort_by = request.args.get('sort_by')
            
            # Get tickets
            tickets = tq.get_tickets(
                status=status,
                assignee_only=assignee_only,
                groups=groups,
                sort_by=sort_by
            )
            
            if not tickets:
                return jsonify({'error': 'No tickets found with specified filters'}), 404
            
            # Generate export file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"tmp/tickets_export_{timestamp}.csv"
            Path("tmp").mkdir(exist_ok=True)
            
            tq.export_to_csv(tickets, export_file)
            
            return send_file(
                export_file,
                as_attachment=True,
                download_name=f"tickets_{timestamp}.csv",
                mimetype='text/csv'
            )
            
        except Exception as e:
            raise
    
    @app.route('/api/stats')
    def get_stats():
        """Get ticket statistics and adapter information."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            adapter_info = tq.get_adapter_info()
            
            # Get ticket counts by status
            status_counts = {}
            for status in ['open', 'pending', 'new', 'hold', 'solved', 'closed']:
                try:
                    tickets = tq.get_tickets(status=status)
                    status_counts[status] = len(tickets)
                except:
                    status_counts[status] = 0
            
            # Get current user info
            user = tq.get_current_user()
            
            return jsonify({
                'success': True,
                'adapter': adapter_info,
                'user': user.dict() if user else None,
                'statistics': {
                    'by_status': status_counts,
                    'total_active': status_counts.get('open', 0) + status_counts.get('pending', 0),
                    'generated_at': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            raise
    
    @app.route('/api/test', methods=['POST'])
    def test_connection():
        """Test the connection to the ticketing system."""
        if not tq:
            return jsonify({'error': 'TicketQ not configured'}), 500
        
        try:
            result = tq.test_connection()
            adapter_info = tq.get_adapter_info()
            
            return jsonify({
                'success': result,
                'adapter': adapter_info['name'],
                'tested_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            raise
    
    return app


# ============================================================================
# FASTAPI INTEGRATION EXAMPLES
# ============================================================================

def create_fastapi_app() -> FastAPI:
    """Create a FastAPI application with TicketQ integration."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Install with: pip install fastapi[all]")
    
    app = FastAPI(
        title="TicketQ API",
        description="Universal ticketing system API powered by TicketQ",
        version="1.0.0"
    )
    
    # Initialize TicketQ
    try:
        tq = TicketQLibrary.from_config()
        adapter_info = tq.get_adapter_info()
        print(f"✅ FastAPI app initialized with {adapter_info['display_name']} adapter")
    except Exception as e:
        print(f"❌ Failed to initialize TicketQ: {e}")
        tq = None
    
    # Pydantic models for request/response
    class TicketResponse(BaseModel):
        success: bool
        count: Optional[int] = None
        tickets: Optional[List[Dict[str, Any]]] = None
        ticket: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
    
    class StatsResponse(BaseModel):
        success: bool
        adapter: Optional[Dict[str, str]] = None
        user: Optional[Dict[str, Any]] = None
        statistics: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
    
    @app.exception_handler(TicketQError)
    async def ticketq_exception_handler(request, exc):
        """Handle TicketQ-specific exceptions."""
        status_code = 400
        if isinstance(exc, AuthenticationError):
            status_code = 401
        elif isinstance(exc, NetworkError):
            status_code = 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "suggestions": getattr(exc, 'suggestions', [])
            }
        )
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        adapter_info = tq.get_adapter_info()
        return {
            "message": "TicketQ API",
            "adapter": adapter_info['display_name'],
            "version": adapter_info['version'],
            "docs": "/docs",
            "endpoints": {
                "tickets": "/api/tickets",
                "search": "/api/search",
                "export": "/api/export",
                "stats": "/api/stats"
            }
        }
    
    @app.get("/api/tickets", response_model=TicketResponse)
    async def get_tickets_api(
        status: str = Query("open", description="Ticket status(es), comma-separated"),
        assignee_only: bool = Query(False, description="Only tickets assigned to current user"),
        groups: Optional[str] = Query(None, description="Group name(s), comma-separated"),
        sort_by: Optional[str] = Query(None, description="Sort field"),
        limit: Optional[int] = Query(None, description="Maximum number of tickets to return")
    ):
        """Get tickets with filtering options."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        # Parse comma-separated values
        status_list = status.split(',') if ',' in status else status
        groups_list = groups.split(',') if groups and ',' in groups else ([groups] if groups else None)
        
        tickets = tq.get_tickets(
            status=status_list,
            assignee_only=assignee_only,
            groups=groups_list,
            sort_by=sort_by
        )
        
        if limit:
            tickets = tickets[:limit]
        
        return TicketResponse(
            success=True,
            count=len(tickets),
            tickets=[ticket.dict() for ticket in tickets]
        )
    
    @app.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
    async def get_ticket_api(ticket_id: str):
        """Get a specific ticket by ID."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        ticket = tq.get_ticket(ticket_id)
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        return TicketResponse(
            success=True,
            ticket=ticket.dict()
        )
    
    @app.get("/api/search", response_model=TicketResponse)
    async def search_tickets_api(q: str = Query(..., description="Search query")):
        """Search tickets with adapter-specific query syntax."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        tickets = tq.search_tickets(q)
        
        return TicketResponse(
            success=True,
            count=len(tickets),
            tickets=[ticket.dict() for ticket in tickets]
        )
    
    @app.get("/api/export")
    async def export_tickets_api(
        background_tasks: BackgroundTasks,
        status: str = Query("open", description="Ticket status(es), comma-separated"),
        assignee_only: bool = Query(False, description="Only tickets assigned to current user"),
        groups: Optional[str] = Query(None, description="Group name(s), comma-separated"),
        sort_by: Optional[str] = Query(None, description="Sort field")
    ):
        """Export tickets to CSV file."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        # Parse parameters
        status_list = status.split(',') if ',' in status else status
        groups_list = groups.split(',') if groups and ',' in groups else ([groups] if groups else None)
        
        # Get tickets
        tickets = tq.get_tickets(
            status=status_list,
            assignee_only=assignee_only,
            groups=groups_list,
            sort_by=sort_by
        )
        
        if not tickets:
            raise HTTPException(status_code=404, detail="No tickets found with specified filters")
        
        # Create export file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"tmp/tickets_export_{timestamp}.csv"
        Path("tmp").mkdir(exist_ok=True)
        
        tq.export_to_csv(tickets, export_file)
        
        # Schedule cleanup of temp file after response
        def cleanup():
            try:
                Path(export_file).unlink(missing_ok=True)
            except:
                pass
        
        background_tasks.add_task(cleanup)
        
        return FileResponse(
            export_file,
            media_type='text/csv',
            filename=f"tickets_{timestamp}.csv"
        )
    
    @app.get("/api/stats", response_model=StatsResponse)
    async def get_stats_api():
        """Get comprehensive statistics and adapter information."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        adapter_info = tq.get_adapter_info()
        
        # Get status counts
        status_counts = {}
        for status in ['open', 'pending', 'new', 'hold', 'solved', 'closed']:
            try:
                tickets = tq.get_tickets(status=status)
                status_counts[status] = len(tickets)
            except:
                status_counts[status] = 0
        
        # Get user info
        user = tq.get_current_user()
        
        return StatsResponse(
            success=True,
            adapter=adapter_info,
            user=user.dict() if user else None,
            statistics={
                "by_status": status_counts,
                "total_active": status_counts.get('open', 0) + status_counts.get('pending', 0),
                "generated_at": datetime.now().isoformat()
            }
        )
    
    @app.post("/api/test")
    async def test_connection_api():
        """Test connection to the ticketing system."""
        if not tq:
            raise HTTPException(status_code=500, detail="TicketQ not configured")
        
        result = tq.test_connection()
        adapter_info = tq.get_adapter_info()
        
        return {
            "success": result,
            "adapter": adapter_info['name'],
            "tested_at": datetime.now().isoformat()
        }
    
    return app


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_flask_dev_server():
    """Run Flask development server."""
    if not FLASK_AVAILABLE:
        print("❌ Flask not installed. Install with: pip install flask")
        return
    
    app = create_flask_app()
    print("🚀 Starting Flask development server...")
    print("   URL: http://localhost:5000")
    print("   API Docs: Available at the root URL")
    app.run(debug=True, host='0.0.0.0', port=5000)


def run_fastapi_dev_server():
    """Run FastAPI development server."""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not installed. Install with: pip install fastapi[all]")
        return
    
    app = create_fastapi_app()
    print("🚀 Starting FastAPI development server...")
    print("   URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   ReDoc: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)


def main():
    """Main function to demonstrate web integration options."""
    print("🌐 TicketQ Web Integration Examples")
    print("==================================")
    print()
    print("This script demonstrates how to integrate TicketQ into web applications.")
    print()
    print("Available options:")
    print("  1. Flask integration (simple, traditional)")
    print("  2. FastAPI integration (modern, async, auto-docs)")
    print()
    
    choice = input("Choose framework (1 for Flask, 2 for FastAPI): ").strip()
    
    if choice == "1":
        if FLASK_AVAILABLE:
            run_flask_dev_server()
        else:
            print("❌ Flask not available. Install with: pip install flask")
    elif choice == "2":
        if FASTAPI_AVAILABLE:
            run_fastapi_dev_server()
        else:
            print("❌ FastAPI not available. Install with: pip install fastapi[all]")
    else:
        print("❌ Invalid choice. Please run again and choose 1 or 2.")
        
    print("\n💡 Integration tips:")
    print("   • Add authentication middleware for production use")
    print("   • Implement rate limiting for API endpoints")
    print("   • Add request logging and monitoring")
    print("   • Consider caching for frequently accessed data")
    print("   • Use environment variables for configuration")
    print("   • Add input validation and sanitization")


if __name__ == "__main__":
    main()