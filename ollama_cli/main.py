import sys
import os
from pathlib import Path
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .config import Config
from .client import OllamaClient
from .history import ConversationHistory
from .command_extractor import extract_commands, copy_to_clipboard


SYSTEM_PROMPT_BASE = """You are a helpful terminal assistant. Your role is to help users with command-line tasks,
shell commands, and terminal operations. Be direct and technical.

IMPORTANT: When providing commands that users might want to copy, format them using this special syntax:
[CMD:label] command_here

Where 'label' is a short identifier (like 'cmd1', 'cmd2', or descriptive like 'find', 'grep', etc.)."""

SYSTEM_PROMPT_CONCISE = SYSTEM_PROMPT_BASE + """

Keep responses SHORT and CONCISE:
- Provide the command with minimal explanation
- Only explain if the command is complex or has important caveats
- Skip obvious explanations
- Get straight to the point"""

SYSTEM_PROMPT_VERBOSE = SYSTEM_PROMPT_BASE + """

Provide detailed explanations:
- Explain what each command does
- Include practical examples
- Describe important options and flags
- Mention potential issues or alternatives"""


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
@click.option('--verbose', '-v', is_flag=True, help='Get detailed explanations')
@click.option('--with-history', '-h', is_flag=True, help='Include recent conversation history as context')
@click.option('--history-limit', default=3, help='Number of previous conversations to include (default: 3)')
@click.pass_context
def ask(ctx, question, no_system, no_context, no_history, verbose, with_history, history_limit):
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
    
    # Add conversation history context if requested
    if with_history:
        conv_context = history.get_conversation_context(history_limit)
        if conv_context:
            full_prompt = f"{conv_context}\n\n{full_prompt}"
            console.print(f"[dim]Including {history_limit} previous conversation(s)[/dim]")
    
    # Add file context if available
    if not no_context:
        context = config.get_full_context()
        full_prompt = f"{context}\n\nQuestion: {question_text}"
        context_used = True
        if config.context_file:
            console.print(f"[dim]Using context from: {config.context_file}[/dim]")
    
    console.print(f"[bold cyan]Model:[/bold cyan] {config.model}")
    console.print(f"[bold cyan]Question:[/bold cyan] {question_text}\n")
    
    try:
        # Choose system prompt based on verbose flag
        if no_system:
            system_prompt = None
        elif verbose:
            system_prompt = SYSTEM_PROMPT_VERBOSE
        else:
            system_prompt = SYSTEM_PROMPT_CONCISE
        
        response = client.generate(full_prompt, system_prompt=system_prompt)
        
        # Extract commands from response
        commands = extract_commands(response)
        
        # Display with syntax highlighting
        console.print(Panel(Markdown(response), title="[bold green]Answer[/bold green]", border_style="green"))
        
        # If commands were found, offer to copy them
        if commands:
            console.print(f"\n[bold cyan]Found {len(commands)} command(s):[/bold cyan]")
            for label, cmd in commands:
                # Show first 60 chars of command
                preview = cmd if len(cmd) <= 60 else cmd[:57] + "..."
                console.print(f"  [{label}] {preview}")
            
            console.print("\n[dim]Type a label to copy that command, or press Enter to skip[/dim]")
            choice = Prompt.ask("[bold cyan]Copy command[/bold cyan]", default="")
            
            if choice:
                # Find the command with matching label
                matching_cmd = next((cmd for lbl, cmd in commands if lbl == choice), None)
                if matching_cmd:
                    if copy_to_clipboard(matching_cmd):
                        console.print(f"[bold green]✓ Command '{choice}' copied to clipboard[/bold green]")
                    else:
                        console.print("[bold red]✗ Failed to copy to clipboard[/bold red]")
                        console.print(f"\n[yellow]Command:[/yellow]\n{matching_cmd}")
                else:
                    console.print(f"[yellow]No command found with label '{choice}'[/yellow]")
        
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
    """Automatically add shell alias/function for easier use.
    
    This creates a shell function that allows you to use:
        ask "your question here"
    instead of:
        uv run ollama-ask ask your question here
    """
    console = ctx.obj['console']
    
    # Get the absolute path to the project directory
    project_dir = str(Path(__file__).parent.parent.absolute())
    
    if shell == 'bash' or shell == 'zsh':
        alias_code = f'''
# Ollama CLI alias (added by ollama-ask setup-alias)
ask() {{
    (cd "{project_dir}" && uv run ollama-ask ask "$@")
}}

# Optional: Add these for other commands
alias ask-history="(cd '{project_dir}' && uv run ollama-ask history)"
alias ask-search="(cd '{project_dir}' && uv run ollama-ask search)"
alias ask-models="(cd '{project_dir}' && uv run ollama-ask models)"
'''
        config_file = os.path.expanduser('~/.bashrc' if shell == 'bash' else '~/.zshrc')
        
    elif shell == 'fish':
        alias_code = f'''
# Ollama CLI function (added by ollama-ask setup-alias)
function ask
    cd "{project_dir}" && uv run ollama-ask ask $argv
end

# Optional: Add these for other commands
function ask-history
    cd "{project_dir}" && uv run ollama-ask history $argv
end

function ask-search
    cd "{project_dir}" && uv run ollama-ask search $argv
end

function ask-models
    cd "{project_dir}" && uv run ollama-ask models
end
'''
        config_file = os.path.expanduser('~/.config/fish/config.fish')
    
    # Check if alias already exists
    marker = "# Ollama CLI alias (added by ollama-ask setup-alias)" if shell != 'fish' else "# Ollama CLI function (added by ollama-ask setup-alias)"
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                if marker in content:
                    console.print(f"[yellow]Aliases already exist in {config_file}[/yellow]")
                    console.print("[yellow]Remove the existing aliases first if you want to update them.[/yellow]")
                    return
        
        # Append to config file
        with open(config_file, 'a') as f:
            f.write(alias_code)
        
        console.print(f"[bold green]✓ Aliases added to {config_file}[/bold green]\n")
        console.print(f"[yellow]Run this to activate:[/yellow] source {config_file}")
        console.print("\n[green]After sourcing, you can use:[/green]")
        console.print('  ask "how do I find large files"')
        console.print('  ask-history')
        console.print('  ask-search docker')
        
    except Exception as e:
        console.print(f"[bold red]Error writing to {config_file}:[/bold red] {e}", style="red")
        console.print("\n[yellow]Manual setup:[/yellow]")
        console.print(alias_code)



if __name__ == '__main__':
    cli(obj={})

# Made with Bob
