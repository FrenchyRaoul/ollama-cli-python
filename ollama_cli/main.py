import sys
import click

from .config import Config
from .client import OllamaClient


SYSTEM_PROMPT = """You are a helpful terminal assistant. Your role is to help users with command-line tasks, 
shell commands, and terminal operations. Provide clear, concise answers with practical examples. 
When suggesting commands, explain what they do. Be direct and technical."""


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config.yaml')
def cli(ctx, config):
    """Ollama CLI - Ask questions about terminal commands and operations."""
    ctx.ensure_object(dict)
    
    try:
        ctx.obj['config'] = Config(config)
        ctx.obj['client'] = OllamaClient(ctx.obj['config'])
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('question', nargs=-1, required=True)
@click.option('--no-system', is_flag=True, help='Disable system prompt')
@click.option('--no-context', is_flag=True, help='Disable context from .ollama/context.md')
@click.pass_context
def ask(ctx, question, no_system, no_context):
    """Ask a question about terminal commands or operations.
    
    Example: ollama-ask ask how do I find large files in a directory
    """
    client = ctx.obj['client']
    config = ctx.obj['config']
    
    # Join question parts into a single string
    question_text = ' '.join(question)
    
    # Build the full prompt with context if available
    full_prompt = question_text
    if not no_context:
        context = config.get_full_context()
        full_prompt = f"{context}\n\nQuestion: {question_text}"
        if config.context_file:
            click.echo(f"Using context from: {config.context_file}")
    
    click.echo(f"Using model: {config.model}")
    click.echo(f"Question: {question_text}\n")
    
    try:
        system_prompt = None if no_system else SYSTEM_PROMPT
        response = client.generate(full_prompt, system_prompt=system_prompt)
        click.echo("Answer:")
        click.echo(response)
    except ConnectionError as e:
        click.echo(f"Connection Error: {e}", err=True)
        sys.exit(1)
    except TimeoutError as e:
        click.echo(f"Timeout Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def models(ctx):
    """List available models on the Ollama server."""
    client = ctx.obj['client']
    
    try:
        model_list = client.list_models()
        if model_list:
            click.echo("Available models:")
            for model in model_list:
                click.echo(f"  - {model}")
        else:
            click.echo("No models found.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Show current configuration."""
    config = ctx.obj['config']
    
    click.echo("Current Configuration:")
    click.echo(f"  Host: {config.host}")
    click.echo(f"  Port: {config.port}")
    click.echo(f"  Model: {config.model}")
    click.echo(f"  Base URL: {config.base_url}")
    click.echo(f"  Timeout: {config.timeout}s")
    click.echo(f"  Stream: {config.stream}")
    click.echo(f"  Authentication: {'Enabled' if config.auth else 'Disabled'}")


if __name__ == '__main__':
    cli(obj={})

# Made with Bob
