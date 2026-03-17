import re
import pyperclip
from typing import List, Tuple


def extract_commands(response: str) -> List[Tuple[str, str]]:
    """Extract labeled commands from response text.
    
    Looks for commands in format: [CMD:label] command_text
    
    Args:
        response: The response text from the model
        
    Returns:
        List of tuples (label, command)
    """
    pattern = r'\[CMD:(\w+)\]\s*(.+?)(?=\[CMD:|$)'
    matches = re.findall(pattern, response, re.DOTALL)
    
    commands = []
    for label, command in matches:
        # Clean up the command text
        command = command.strip()
        # Remove markdown code block markers if present
        command = re.sub(r'^```\w*\n?', '', command)
        command = re.sub(r'\n?```$', '', command)
        command = command.strip()
        commands.append((label, command))
    
    return commands


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard.
    
    Args:
        text: Text to copy
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False

# Made with Bob
