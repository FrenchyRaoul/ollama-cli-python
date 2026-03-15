import sys
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .config import Config
from .client import OllamaClient
from .history import ConversationHistory


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
        ctx.obj['history'] = ConversationHistory()
        ctx.obj['console'] = Console()
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
@click.option('--no-history', is_flag=True, help='Do not save to history')
@click.pass_context
def ask(ctx, question, no_system, no_context, no_history):
    """Ask a question about terminal commands or operations.
    
    Example: ollama-ask ask how do I find large files in a directory
    """
    client = ctx.obj['client']
    config = ctx.obj['config']
    history = ctx.obj['history']
    console = ctx.obj['console']
    
    # Join question parts into a single string
    question_text = ' '.join(question)
    
    # Build the full prompt with context if available
    full_prompt = question_text
    context_used = False
    if not no_context:
        context = config.get_full_context()
        full_prompt = f"{context}\n\nQuestion: {question_text}"
        context_used = True
        if config.context_file:
            console.print(f"[dim]Using context from: {config.context_file}[/dim]")
    
    console.print(f"[bold cyan]Model:[/bold cyan] {config.model}")
    console.print(f"[bold cyan]Question:[/bold cyan] {question_text}\n")
    
    try:
        system_prompt = None if no_system else SYSTEM_PROMPT
        response = client.generate(full_prompt, system_prompt=system_prompt)
        
        # Display with syntax highlighting
        console.print(Panel(Markdown(response), title="[bold green]Answer[/bold green]", border_style="green"))
        
        # Save to history
        if not no_history:
            history.add_entry(question_text, response, config.model, context_used)
            
    except ConnectionError as e:
        console.print(f"[bold red]Connection Error:[/bold red] {e}", style="red")
        sys.exit(1)
    except TimeoutError as e:
        console.print(f"[bold red]Timeout Error:[/bold red] {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def models(ctx):
    """List available models on the Ollama server."""
    client = ctx.obj['client']
    console = ctx.obj['console']
    
    try:
        model_list = client.list_models()
        if model_list:
            console.print("[bold cyan]Available models:[/bold cyan]")
            for model in model_list:
                console.print(f"  • {model}")
        else:
            console.print("[yellow]No models found.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Show current configuration."""
    config = ctx.obj['config']
    console = ctx.obj['console']
    
    console.print("[bold cyan]Current Configuration:[/bold cyan]")
    console.print(f"  Host: {config.host}")
    console.print(f"  Port: {config.port}")
    console.print(f"  Model: {config.model}")
    console.print(f"  Base URL: {config.base_url}")
    console.print(f"  Timeout: {config.timeout}s")
    console.print(f"  Stream: {config.stream}")
    console.print(f"  Authentication: {'Enabled' if config.auth else 'Disabled'}")


@cli.command()
@click.option('--limit', '-n', default=10, help='Number of entries to show')
@click.pass_context
def history(ctx, limit):
    """Show recent conversation history."""
    history = ctx.obj['history']
    console = ctx.obj['console']
    
    entries = history.get_recent(limit)
    
    if not entries:
        console.print("[yellow]No conversation history found.[/yellow]")
        return
    
    console.print(f"[bold cyan]Recent Conversations (last {len(entries)}):[/bold cyan]\n")
    
    for i, entry in enumerate(entries, 1):
        timestamp = entry['timestamp'].split('T')[0] + ' ' + entry['timestamp'].split('T')[1][:8]
        console.print(f"[bold]{i}. [{timestamp}][/bold] [dim]({entry['model']})[/dim]")
        console.print(f"   [cyan]Q:[/cyan] {entry['question'][:80]}{'...' if len(entry['question']) > 80 else ''}")
        console.print(f"   [green]A:[/green] {entry['answer'][:80]}{'...' if len(entry['answer']) > 80 else ''}")
        console.print()


@cli.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, help='Number of results to show')
@click.pass_context
def search(ctx, query, limit):
    """Search conversation history."""
    history = ctx.obj['history']
    console = ctx.obj['console']
    
    results = history.search(query, limit)
    
    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return
    
    console.print(f"[bold cyan]Search results for '{query}' ({len(results)} found):[/bold cyan]\n")
    
    for i, entry in enumerate(results, 1):
        timestamp = entry['timestamp'].split('T')[0] + ' ' + entry['timestamp'].split('T')[1][:8]
        console.print(f"[bold]{i}. [{timestamp}][/bold] [dim]({entry['model']})[/dim]")
        console.print(f"   [cyan]Q:[/cyan] {entry['question']}")
        console.print(f"   [green]A:[/green] {entry['answer'][:100]}{'...' if len(entry['answer']) > 100 else ''}")
        console.print()

@cli.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), default='bash', help='Shell type')
@click.pass_context
def setup_alias(ctx, shell):
    """Generate shell alias/function for easier use.
    
    This creates a shell function that allows you to use:
        ask "your question here"
    instead of:
        uv run ollama-ask ask your question here
    """
    console = ctx.obj['console']
    
    if shell == 'bash' or shell == 'zsh':
        alias_code = '''# Ollama CLI alias
ask() {
    uv run ollama-ask ask "$@"
}

# Optional: Add these for other commands
alias ask-history="uv run ollama-ask history"
alias ask-search="uv run ollama-ask search"
alias ask-models="uv run ollama-ask models"
'''
        config_file = '~/.bashrc' if shell == 'bash' else '~/.zshrc'
        
    elif shell == 'fish':
        alias_code = '''# Ollama CLI function
function ask
    uv run ollama-ask ask $argv
end

# Optional: Add these for other commands
function ask-history
    uv run ollama-ask history $argv
end

function ask-search
    uv run ollama-ask search $argv
end

function ask-models
    uv run ollama-ask models
end
'''
        config_file = '~/.config/fish/config.fish'
    
    console.print(f"[bold cyan]Shell Alias Setup for {shell}[/bold cyan]\n")
    console.print(f"Add the following to your {config_file}:\n")
    console.print(Panel(alias_code, border_style="green"))
    console.print(f"\n[yellow]Then run:[/yellow] source {config_file}")
    console.print("\n[green]After setup, you can use:[/green]")
    console.print('  ask "how do I find large files"')
    console.print('  ask-history')
    console.print('  ask-search docker')



if __name__ == '__main__':
    cli(obj={})

# Made with Bob
