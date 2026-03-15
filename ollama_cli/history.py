import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class ConversationHistory:
    """Manage conversation history for Ollama CLI."""
    
    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize conversation history.
        
        Args:
            history_dir: Directory to store history. Defaults to ~/.ollama/history
        """
        if history_dir is None:
            history_dir = Path.home() / ".ollama" / "history"
        
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "conversations.jsonl"
    
    def add_entry(self, question: str, answer: str, model: str, context_used: bool = False):
        """Add a conversation entry to history.
        
        Args:
            question: The user's question
            answer: The model's answer
            model: The model used
            context_used: Whether context was included
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "model": model,
            "context_used": context_used
        }
        
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of conversation entries, most recent first
        """
        if not self.history_file.exists():
            return []
        
        entries = []
        with open(self.history_file, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        return entries[-limit:][::-1]
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search conversation history.
        
        Args:
            query: Search term (case-insensitive)
            limit: Maximum number of results
            
        Returns:
            List of matching entries
        """
        if not self.history_file.exists():
            return []
        
        query_lower = query.lower()
        matches = []
        
        with open(self.history_file, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if (query_lower in entry['question'].lower() or 
                        query_lower in entry['answer'].lower()):
                        matches.append(entry)
        
        return matches[-limit:][::-1]
    
    def clear(self):
        """Clear all conversation history."""
        if self.history_file.exists():
            self.history_file.unlink()

# Made with Bob
