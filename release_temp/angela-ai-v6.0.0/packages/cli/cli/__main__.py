import click
import requests

@click.group()
def cli():
    """Unified AI Project CLI"""
    pass

@cli.command()
def health():
    """
    Checks the health of the Unified AI Backend.
    """
    try:
        response = requests.get("http://127.0.0.1:8000/api/v1/health")
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        click.echo(f"Backend Health: {response.json()}")
    except requests.exceptions.ConnectionError:
        click.echo("Error: Could not connect to the backend. Is it running?")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error checking backend health: {e}")

if __name__ == "__main__":
    cli()
