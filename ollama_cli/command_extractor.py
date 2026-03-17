import re
import pyperclip
from typing import List, Tuple, Optional


def extract_commands(response: str) -> List[Tuple[str, str]]:
    """Extract labeled commands from response text.
    
    Looks for commands in format: [CMD:N] command_text where N is a number
    
    Args:
        response: The response text from the model
        
    Returns:
        List of tuples (label, command)
    """
    pattern = r'\[CMD:(\d+)\]\s*(.+?)(?=\[CMD:|$)'
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


def copy_to_clipboard(text: str) -> tuple[bool, Optional[str]]:
    """Copy text to clipboard.
    
    Args:
        text: Text to copy
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        pyperclip.copy(text)
        return True, None
    except pyperclip.PyperclipException as e:
        error_msg = str(e)
        # Check for display-related errors (SSH without X11)
        if "display" in error_msg.lower() or "DISPLAY" in error_msg:
            return False, "Clipboard unavailable (no X11 display in SSH session)"
        # Check for missing clipboard utilities
        elif "xclip" in error_msg.lower() or "xsel" in error_msg.lower():
            return False, "Install xclip or xsel: sudo pacman -S xclip"
        return False, f"Clipboard error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

# Made with Bob
