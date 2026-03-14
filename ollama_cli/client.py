import requests
from typing import Optional

from .config import Config


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: Config):
        """Initialize Ollama client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.session = requests.Session()
        if config.auth:
            self.session.auth = config.auth
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from Ollama.
        
        Args:
            prompt: The user's question/prompt
            system_prompt: Optional system prompt to guide the model
            
        Returns:
            The model's response text
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.config.base_url}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": self.config.stream
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.config.base_url}. "
                "Please ensure Ollama is running and accessible."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Request timed out after {self.config.timeout} seconds. "
                "Try increasing the timeout in config.yaml."
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error communicating with Ollama: {e}")
    
    def list_models(self) -> list:
        """List available models.
        
        Returns:
            List of available model names
        """
        url = f"{self.config.base_url}/api/tags"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            raise RuntimeError(f"Error listing models: {e}")

# Made with Bob
