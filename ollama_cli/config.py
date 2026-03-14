import os
import platform
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for Ollama CLI."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config.yaml file. If None, looks in current directory.
        """
        # Load environment variables
        load_dotenv()
        
        # Determine config file path
        if config_path is None:
            # Look for config.yaml in current directory, then in package directory
            current_dir = Path.cwd() / "config.yaml"
            package_dir = Path(__file__).parent.parent / "config.yaml"
            
            if current_dir.exists():
                config_path = str(current_dir)
            elif package_dir.exists():
                config_path = str(package_dir)
            else:
                raise FileNotFoundError(
                    "config.yaml not found. Please create one in the current directory."
                )
        
        # Load YAML configuration
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Parse configuration
        ollama_config = self._config.get('ollama', {})
        self.host = ollama_config.get('host', 'localhost')
        self.port = ollama_config.get('port', 11434)
        self.model = ollama_config.get('model', 'llama2')
        
        request_config = self._config.get('request', {})
        self.timeout = request_config.get('timeout', 30)
        self.stream = request_config.get('stream', False)
        
        # Get credentials from environment
        self.username = os.getenv('OLLAMA_USERNAME')
        self.password = os.getenv('OLLAMA_PASSWORD')
        
        # Context file path
        self.context_file = self._find_context_file()
    
    def _find_context_file(self) -> Optional[Path]:
        """Find context.md file in .ollama directory.
        
        Searches in:
        1. ~/.ollama/context.md (user home)
        2. ./.ollama/context.md (current directory)
        
        Returns:
            Path to context file if found, None otherwise
        """
        # Check home directory first
        home_context = Path.home() / ".ollama" / "context.md"
        if home_context.exists():
            return home_context
        
        # Check current directory
        local_context = Path.cwd() / ".ollama" / "context.md"
        if local_context.exists():
            return local_context
        
        return None
    
    def get_system_info(self) -> str:
        """Get system information to include as context.
        
        Returns:
            Formatted string with system information
        """
        shell = os.environ.get('SHELL', 'unknown')
        system = platform.system()
        release = platform.release()
        hostname = platform.node()
        
        return f"""System Information:
- Operating System: {system} {release}
- Hostname: {hostname}
- Shell: {shell}
- Python: {platform.python_version()}"""
    
    def get_context(self) -> Optional[str]:
        """Read and return context from context.md file.
        
        Returns:
            Context text if file exists, None otherwise
        """
        if self.context_file and self.context_file.exists():
            try:
                return self.context_file.read_text()
            except Exception:
                return None
        return None
    
    def get_full_context(self) -> str:
        """Get full context including system info and user context.
        
        Returns:
            Combined context string
        """
        parts = [self.get_system_info()]
        
        user_context = self.get_context()
        if user_context:
            parts.append(f"\nUser Context:\n{user_context}")
        
        return "\n".join(parts)
    
    @property
    def base_url(self) -> str:
        """Get the base URL for Ollama API."""
        return f"http://{self.host}:{self.port}"
    
    @property
    def auth(self) -> Optional[tuple]:
        """Get authentication tuple if credentials are set."""
        if self.username and self.password:
            return (self.username, self.password)
        return None

# Made with Bob
