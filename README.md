# Ollama CLI Python

A command-line tool to query an Ollama LLM for help with terminal commands and operations. Features syntax highlighting, conversation history, and automatic system context.

## Installation

```bash
git clone https://github.com/FrenchyRaoul/ollama-cli-python.git
cd ollama-cli-python
uv pip install -e .
```

## Configuration

### Basic Configuration

Edit `config.yaml` to set your Ollama server details:
```yaml
ollama:
  host: "192.168.0.146"      # Your Ollama server IP
  port: 11434                # Default Ollama port
  model: "qwen2.5-coder:7b"  # Model to use

request:
  timeout: 30  # Request timeout in seconds
  stream: false
```

### Optional: Authentication

If your Ollama server requires authentication, create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add:
# OLLAMA_USERNAME=your_username
# OLLAMA_PASSWORD=your_password
```

### Optional: Custom Context

Create `~/.ollama/context.md` or `./.ollama/context.md` to add custom context to all queries:
```markdown
# My Context
- I prefer using zsh
- I work primarily with Python and Docker
- I use macOS
```

The tool automatically includes system information (OS, hostname, shell) with every query.

## Usage

### Ask Questions

The tool provides syntax-highlighted responses with markdown formatting:

```bash
# Basic question
uv run ollama-ask ask how do I find large files in a directory

# Disable context
uv run ollama-ask ask --no-context what is grep

# Disable system prompt
uv run ollama-ask ask --no-system your question here

# Don't save to history
uv run ollama-ask ask --no-history temporary question
```

### View Conversation History

```bash
# Show recent conversations
uv run ollama-ask history

# Show more entries
uv run ollama-ask history --limit 20

# Search history
uv run ollama-ask search "docker"
uv run ollama-ask search "git" --limit 5
```

### Other Commands

```bash
# List available models
uv run ollama-ask models

# Show current configuration
uv run ollama-ask info

# Use custom config file
uv run ollama-ask --config /path/to/config.yaml ask your question
```

## Features

- **Syntax Highlighting**: Responses are formatted with markdown and syntax highlighting using Rich
- **Conversation History**: All Q&A pairs are saved to `~/.ollama/history/conversations.jsonl`
- **System Context**: Automatically includes OS, hostname, shell, and Python version
- **Custom Context**: Add your own context via `.ollama/context.md`
- **Search History**: Search through past conversations
- **Configurable**: YAML configuration for server, model, and request settings

## Examples

```bash
# Find large files
uv run ollama-ask ask how to find files larger than 100MB

# Docker help
uv run ollama-ask ask how to remove all stopped containers

# Git operations
uv run ollama-ask ask how to undo the last commit

# Search past conversations about docker
uv run ollama-ask search docker
```

## Requirements

- Python 3.8+
- uv (recommended) or pip
- Access to an Ollama server with at least one model pulled

## Recommended Models

For technical/CLI questions:
- **qwen2.5-coder:7b** - Best for code/technical tasks (~4.7GB)
- **llama3.2:3b** - Fast, good general knowledge (~2GB)
- **phi3:mini** - Very small, decent for CLI help (~2.3GB)

Pull a model:
```bash
docker exec -it ollama ollama pull qwen2.5-coder:7b
```

## Troubleshooting

### Connection Errors
1. Verify Ollama is running: `curl http://your-host:11434/api/tags`
2. Check the IP address and port in `config.yaml`
3. Ensure Ollama listens on network interface (not just localhost)
4. Check firewall settings

### Running Ollama with Docker
```bash
docker run -d --network host -v ollama_data:/root/.ollama \
  --name ollama --restart unless-stopped ollama/ollama
```

## License

MIT