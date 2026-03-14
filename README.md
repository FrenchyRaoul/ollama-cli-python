# Ollama CLI

A command-line tool to query an Ollama LLM for help with terminal commands and operations.

## Installation

1. Navigate to the project directory:
```bash
cd ollama-cli
```

2. Install using uv:
```bash
uv pip install -e .
```

## Configuration

1. Edit `config.yaml` to set your Ollama server details:
```yaml
ollama:
  host: "192.168.0.146"  # Your Ollama server IP
  port: 11434            # Default Ollama port
  model: "llama2"        # Model to use
```

2. (Optional) If authentication is required, create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your credentials
```

## Usage

### Ask a question
```bash
ollama-ask ask how do I find large files in a directory
ollama-ask ask what is the difference between grep and awk
ollama-ask ask how to compress a directory with tar
```

### List available models
```bash
ollama-ask models
```

### Show current configuration
```bash
ollama-ask info
```

### Use a custom config file
```bash
ollama-ask --config /path/to/config.yaml ask your question here
```

## Examples

```bash
# Find files modified in the last 7 days
ollama-ask ask how to find files modified in the last 7 days

# Learn about process management
ollama-ask ask how to kill a process by name

# Get help with git commands
ollama-ask ask how to undo the last commit in git
```

## Requirements

- Python 3.8+
- Access to an Ollama server
- Ollama server must have at least one model pulled

## Troubleshooting

If you get connection errors:
1. Verify Ollama is running on the remote machine
2. Check the IP address and port in `config.yaml`
3. Ensure Ollama is configured to accept network connections
4. Check firewall settings on both machines