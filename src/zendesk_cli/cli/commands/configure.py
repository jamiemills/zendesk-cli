"""Configure command implementation."""

import click
import logging
from typing import Optional

from ...services.auth_service import AuthService
from ...utils.config import ZendeskConfig
from ...models.exceptions import ZendeskCliError

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--domain',
    help='Zendesk domain (e.g., company.zendesk.com)'
)
@click.option(
    '--email',
    help='Your email address'
)
@click.option(
    '--api-token',
    help='Your Zendesk API token'
)
@click.option(
    '--config-path',
    type=click.Path(),
    help='Path to save configuration file'
)
@click.option(
    '--test',
    is_flag=True,
    help='Test the connection after saving configuration'
)
def configure(
    domain: Optional[str],
    email: Optional[str], 
    api_token: Optional[str],
    config_path: Optional[str],
    test: bool
) -> None:
    """Configure Zendesk CLI credentials and settings."""
    
    click.echo("🔧 Zendesk CLI Configuration")
    click.echo("=" * 40)
    
    try:
        # Collect configuration values
        if not domain:
            domain = click.prompt(
                "Zendesk domain (e.g., company.zendesk.com)",
                type=str
            )
        
        if not email:
            email = click.prompt(
                "Your email address",
                type=str
            )
        
        if not api_token:
            api_token = click.prompt(
                "Your API token",
                type=str,
                hide_input=True
            )
        
        # Create configuration
        config = ZendeskConfig(
            domain=domain,
            email=email,
            api_token=api_token
        )
        
        # Save configuration
        auth_service = AuthService()
        auth_service.save_config(config, config_path)
        
        config_location = config_path or auth_service.get_default_config_path()
        click.echo(
            click.style(
                f"✅ Configuration saved to: {config_location}",
                fg='green'
            )
        )
        
        # Test connection if requested
        if test:
            click.echo("\n🔍 Testing connection...")
            
            try:
                client = auth_service.create_client_from_config(config)
                user_info = client.get_current_user()
                
                click.echo(
                    click.style(
                        f"✅ Connection successful!",
                        fg='green'
                    )
                )
                click.echo(f"   Logged in as: {user_info.get('name')} ({user_info.get('email')})")
                click.echo(f"   User ID: {user_info.get('id')}")
                
            except Exception as e:
                click.echo(
                    click.style(
                        f"❌ Connection test failed: {e}",
                        fg='red'
                    )
                )
                click.echo("Please check your credentials and try again.")
                raise click.Abort()
        
        click.echo(
            click.style(
                "\n🎉 Setup complete! You can now run 'zendesk tickets' to list your tickets.",
                fg='green'
            )
        )
        
    except ZendeskCliError as e:
        click.echo(click.style(f"❌ Configuration error: {e}", fg='red'))
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in configure command")
        click.echo(click.style(f"❌ Unexpected error: {e}", fg='red'))
        raise click.Abort()