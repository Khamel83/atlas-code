"""
Memory Manager for Atlas Code V5

Lightweight memory management for conversation history, context persistence,
and intelligent context window optimization.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ContextEntry:
    """Single context entry in memory."""
    timestamp: datetime
    entry_type: str  # "user_query", "ai_response", "system_event"
    content: str
    metadata: Dict[str, Any]
    tokens_estimate: int = 0
    importance: float = 1.0  # 0.0 to 1.0, higher = more important

@dataclass
class ConversationSession:
    """Represents a conversation session."""
    session_id: str
    start_time: datetime
    last_activity: datetime
    entries: List[ContextEntry]
    total_tokens: int = 0
    metadata: Dict[str, Any] = None

class MemoryManager:
    """
    Lightweight memory management system for conversation history,
    context persistence, and intelligent context optimization.
    """
    
    def __init__(self, config_dir: str):
        """Initialize memory manager with configuration."""
        self.config_dir = config_dir
        
        # Load settings
        self.settings = self._load_settings()
        memory_config = self.settings.get('memory_management', {})
        
        # Configuration
        self.max_history_entries = memory_config.get('max_history_entries', 1000)
        self.context_window_overlap = memory_config.get('context_window_overlap', 0.1)
        self.cleanup_after_days = memory_config.get('cleanup_after_days', 30)
        self.compress_old_entries = memory_config.get('compress_old_entries', True)
        
        # Memory storage
        self.current_session: Optional[ConversationSession] = None
        self.session_history: Dict[str, ConversationSession] = {}
        
        # Context management
        self.active_context: List[ContextEntry] = []
        self.max_context_tokens = self.settings.get('system_settings', {}).get('max_context_length', 100000)
        
        # File paths
        data_dir = os.path.join(os.path.dirname(self.config_dir), 'data')
        os.makedirs(data_dir, exist_ok=True)
        self.memory_file = os.path.join(data_dir, 'memory.jsonl')
        self.sessions_file = os.path.join(data_dir, 'sessions.json')
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Load existing memory
        self._load_memory()
        
        logger.info(f"Memory manager initialized with max {self.max_history_entries} entries")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load system settings."""
        try:
            settings_path = os.path.join(self.config_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
            return self._get_default_settings()
    
    def _load_memory(self):
        """Load existing memory from disk."""
        try:
            # Load session history
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                    
                for session_id, session_data in sessions_data.items():
                    # Convert back to objects
                    entries = []
                    for entry_data in session_data.get('entries', []):
                        entry = ContextEntry(
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            entry_type=entry_data['entry_type'],
                            content=entry_data['content'],
                            metadata=entry_data['metadata'],
                            tokens_estimate=entry_data.get('tokens_estimate', 0),
                            importance=entry_data.get('importance', 1.0)
                        )
                        entries.append(entry)
                    
                    session = ConversationSession(
                        session_id=session_id,
                        start_time=datetime.fromisoformat(session_data['start_time']),
                        last_activity=datetime.fromisoformat(session_data['last_activity']),
                        entries=entries,
                        total_tokens=session_data.get('total_tokens', 0),
                        metadata=session_data.get('metadata', {})
                    )
                    
                    self.session_history[session_id] = session
                
                logger.info(f"Loaded {len(self.session_history)} sessions from memory")
            
            # Load current memory entries from JSONL
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    for line in f:
                        try:
                            entry_data = json.loads(line.strip())
                            entry = ContextEntry(
                                timestamp=datetime.fromisoformat(entry_data['timestamp']),
                                entry_type=entry_data['entry_type'],
                                content=entry_data['content'],
                                metadata=entry_data['metadata'],
                                tokens_estimate=entry_data.get('tokens_estimate', 0),
                                importance=entry_data.get('importance', 1.0)
                            )
                            self.active_context.append(entry)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Skipping invalid memory entry: {e}")
                
                logger.info(f"Loaded {len(self.active_context)} context entries")
        
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new conversation session."""
        
        with self._lock:
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.current_session = ConversationSession(
                session_id=session_id,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                entries=[],
                metadata={}
            )
            
            logger.info(f"Started new session: {session_id}")
            return session_id
    
    def add_context(
        self,
        content: str,
        entry_type: str = "user_query",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0
    ) -> ContextEntry:
        """Add content to conversation context."""
        
        with self._lock:
            if metadata is None:
                metadata = {}
            
            # Estimate tokens (rough approximation)
            tokens_estimate = max(1, len(content) // 4)
            
            entry = ContextEntry(
                timestamp=datetime.now(),
                entry_type=entry_type,
                content=content,
                metadata=metadata,
                tokens_estimate=tokens_estimate,
                importance=importance
            )
            
            # Add to active context
            self.active_context.append(entry)
            
            # Add to current session if active
            if self.current_session:
                self.current_session.entries.append(entry)
                self.current_session.last_activity = datetime.now()
                self.current_session.total_tokens += tokens_estimate
            
            # Optimize context window if needed
            self._optimize_context_window()
            
            # Save periodically
            if len(self.active_context) % 10 == 0:
                self._save_memory()
            
            logger.debug(f"Added {entry_type} context: {len(content)} chars, {tokens_estimate} tokens")
            return entry
    
    def get_context_window(
        self,
        max_tokens: Optional[int] = None,
        include_types: Optional[List[str]] = None,
        min_importance: float = 0.0
    ) -> List[ContextEntry]:
        """Get optimized context window for AI requests."""
        
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        with self._lock:
            # Filter entries by type and importance
            filtered_entries = []
            for entry in self.active_context:
                if include_types and entry.entry_type not in include_types:
                    continue
                if entry.importance < min_importance:
                    continue
                filtered_entries.append(entry)
            
            # Sort by importance and recency (hybrid approach)
            def sort_key(entry: ContextEntry) -> float:
                # Combine importance with recency bias
                age_hours = (datetime.now() - entry.timestamp).total_seconds() / 3600
                recency_factor = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
                return entry.importance * recency_factor
            
            filtered_entries.sort(key=sort_key, reverse=True)
            
            # Select entries within token limit
            selected_entries = []
            total_tokens = 0
            
            for entry in filtered_entries:
                if total_tokens + entry.tokens_estimate <= max_tokens:
                    selected_entries.append(entry)
                    total_tokens += entry.tokens_estimate
                else:
                    break
            
            # Sort selected entries by timestamp for chronological order
            selected_entries.sort(key=lambda e: e.timestamp)
            
            logger.debug(f"Context window: {len(selected_entries)} entries, {total_tokens} tokens")
            return selected_entries
    
    def search_memory(
        self,
        query: str,
        max_results: int = 10,
        entry_types: Optional[List[str]] = None,
        min_relevance: float = 0.3
    ) -> List[Tuple[ContextEntry, float]]:
        """Search memory for relevant content."""
        
        query_lower = query.lower()
        results = []
        
        with self._lock:
            all_entries = self.active_context.copy()
            
            # Add entries from session history
            for session in self.session_history.values():
                all_entries.extend(session.entries)
            
            for entry in all_entries:
                if entry_types and entry.entry_type not in entry_types:
                    continue
                
                # Simple text-based relevance scoring
                content_lower = entry.content.lower()
                
                # Exact match bonus
                exact_matches = query_lower.count(' ') + 1
                found_matches = sum(1 for word in query_lower.split() if word in content_lower)
                exact_score = found_matches / exact_matches if exact_matches > 0 else 0
                
                # Substring match
                substring_score = 0.5 if query_lower in content_lower else 0
                
                # Keyword density
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                common_words = query_words & content_words
                density_score = len(common_words) / len(query_words) if query_words else 0
                
                # Combined relevance score
                relevance = (exact_score * 0.5 + substring_score * 0.3 + density_score * 0.2) * entry.importance
                
                if relevance >= min_relevance:
                    results.append((entry, relevance))
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:max_results]
            
            logger.debug(f"Memory search: '{query}' returned {len(results)} results")
            return results
    
    def get_conversation_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of conversation session."""
        
        with self._lock:
            if session_id:
                session = self.session_history.get(session_id)
                if not session:
                    return {"error": f"Session {session_id} not found"}
                entries = session.entries
            elif self.current_session:
                session = self.current_session
                entries = session.entries
            else:
                entries = self.active_context
                session = None
            
            if not entries:
                return {
                    "total_entries": 0,
                    "total_tokens": 0,
                    "duration_minutes": 0,
                    "entry_types": {}
                }
            
            # Calculate statistics
            entry_type_counts = {}
            total_tokens = 0
            
            for entry in entries:
                entry_type_counts[entry.entry_type] = entry_type_counts.get(entry.entry_type, 0) + 1
                total_tokens += entry.tokens_estimate
            
            # Calculate duration
            if session:
                duration = (session.last_activity - session.start_time).total_seconds() / 60
            else:
                duration = (entries[-1].timestamp - entries[0].timestamp).total_seconds() / 60
            
            return {
                "session_id": session.session_id if session else "current",
                "total_entries": len(entries),
                "total_tokens": total_tokens,
                "duration_minutes": duration,
                "entry_types": entry_type_counts,
                "start_time": entries[0].timestamp.isoformat(),
                "last_activity": entries[-1].timestamp.isoformat()
            }
    
    def cleanup_old_entries(self, days: Optional[int] = None):
        """Clean up old memory entries."""
        
        if days is None:
            days = self.cleanup_after_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self._lock:
            # Clean active context
            original_count = len(self.active_context)
            self.active_context = [e for e in self.active_context if e.timestamp > cutoff_date]
            cleaned_count = original_count - len(self.active_context)
            
            # Clean session history
            sessions_to_remove = []
            for session_id, session in self.session_history.items():
                if session.last_activity < cutoff_date:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.session_history[session_id]
            
            logger.info(f"Cleaned up {cleaned_count} context entries and {len(sessions_to_remove)} sessions")
            
            # Save changes
            self._save_memory()
    
    def _optimize_context_window(self):
        """Optimize context window to stay within limits."""
        
        if len(self.active_context) <= self.max_history_entries:
            return
        
        # Calculate current token usage
        total_tokens = sum(entry.tokens_estimate for entry in self.active_context)
        
        if total_tokens <= self.max_context_tokens:
            return
        
        # Remove least important old entries
        self.active_context.sort(key=lambda e: (e.importance, e.timestamp))
        
        # Keep overlap for continuity
        target_size = int(self.max_history_entries * (1 - self.context_window_overlap))
        
        if len(self.active_context) > target_size:
            removed_count = len(self.active_context) - target_size
            self.active_context = self.active_context[removed_count:]
            logger.debug(f"Removed {removed_count} entries for context optimization")
    
    def _save_memory(self):
        """Save memory to disk."""
        try:
            # Save active context to JSONL
            with open(self.memory_file, 'w') as f:
                for entry in self.active_context:
                    entry_data = asdict(entry)
                    entry_data['timestamp'] = entry.timestamp.isoformat()
                    f.write(json.dumps(entry_data) + '\n')
            
            # Save session history
            sessions_data = {}
            for session_id, session in self.session_history.items():
                session_data = {
                    'start_time': session.start_time.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'total_tokens': session.total_tokens,
                    'metadata': session.metadata or {},
                    'entries': []
                }
                
                for entry in session.entries:
                    entry_data = asdict(entry)
                    entry_data['timestamp'] = entry.timestamp.isoformat()
                    session_data['entries'].append(entry_data)
                
                sessions_data[session_id] = session_data
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            
            logger.debug("Memory saved to disk")
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def end_session(self):
        """End current session and save it to history."""
        
        with self._lock:
            if self.current_session:
                # Save to session history
                self.session_history[self.current_session.session_id] = self.current_session
                
                logger.info(f"Ended session {self.current_session.session_id} with {len(self.current_session.entries)} entries")
                
                self.current_session = None
                self._save_memory()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        
        with self._lock:
            active_tokens = sum(entry.tokens_estimate for entry in self.active_context)
            
            # Session statistics
            session_stats = {}
            total_session_entries = 0
            for session_id, session in self.session_history.items():
                session_stats[session_id] = {
                    'entries': len(session.entries),
                    'tokens': session.total_tokens,
                    'duration_hours': (session.last_activity - session.start_time).total_seconds() / 3600
                }
                total_session_entries += len(session.entries)
            
            return {
                'active_context_entries': len(self.active_context),
                'active_context_tokens': active_tokens,
                'max_context_tokens': self.max_context_tokens,
                'context_utilization': active_tokens / self.max_context_tokens if self.max_context_tokens > 0 else 0,
                'total_sessions': len(self.session_history),
                'total_session_entries': total_session_entries,
                'current_session_active': self.current_session is not None,
                'current_session_entries': len(self.current_session.entries) if self.current_session else 0,
                'session_stats': session_stats
            }
    
    def export_session(self, session_id: str, format: str = 'json') -> Optional[str]:
        """Export session data in specified format."""
        
        with self._lock:
            session = self.session_history.get(session_id)
            if not session:
                return None
            
            if format.lower() == 'json':
                export_data = {
                    'session_id': session.session_id,
                    'start_time': session.start_time.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'total_tokens': session.total_tokens,
                    'metadata': session.metadata,
                    'entries': []
                }
                
                for entry in session.entries:
                    entry_data = asdict(entry)
                    entry_data['timestamp'] = entry.timestamp.isoformat()
                    export_data['entries'].append(entry_data)
                
                return json.dumps(export_data, indent=2)
            
            elif format.lower() == 'markdown':
                lines = [
                    f"# Session: {session.session_id}",
                    f"**Start Time:** {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"**Duration:** {(session.last_activity - session.start_time).total_seconds() / 60:.1f} minutes",
                    f"**Total Entries:** {len(session.entries)}",
                    f"**Total Tokens:** {session.total_tokens}",
                    "",
                    "## Conversation History",
                    ""
                ]
                
                for entry in session.entries:
                    timestamp = entry.timestamp.strftime('%H:%M:%S')
                    lines.append(f"### {timestamp} - {entry.entry_type.title()}")
                    lines.append(f"{entry.content}")
                    lines.append("")
                
                return "\n".join(lines)
            
            return None
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Default settings if config missing."""
        return {
            'memory_management': {
                'max_history_entries': 1000,
                'context_window_overlap': 0.1,
                'cleanup_after_days': 30,
                'compress_old_entries': True
            },
            'system_settings': {
                'max_context_length': 100000
            }
        }

# Example usage and testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test memory manager
    memory = MemoryManager("../config")
    
    print("🧠 Testing Memory Manager")
    print("=" * 40)
    
    # Start session
    session_id = memory.start_session()
    print(f"Started session: {session_id}")
    
    # Add various context entries
    test_entries = [
        ("write a python function", "user_query"),
        ("def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)", "ai_response"),
        ("explain how it works", "user_query"),
        ("This is a recursive implementation...", "ai_response"),
        ("optimize for performance", "user_query")
    ]
    
    for content, entry_type in test_entries:
        memory.add_context(content, entry_type)
    
    # Test context window
    context_window = memory.get_context_window(max_tokens=1000)
    print(f"\nContext window: {len(context_window)} entries")
    
    # Test memory search
    search_results = memory.search_memory("fibonacci")
    print(f"Search results for 'fibonacci': {len(search_results)} matches")
    
    # Test conversation summary
    summary = memory.get_conversation_summary()
    print(f"\nConversation summary:")
    print(f"- Total entries: {summary['total_entries']}")
    print(f"- Total tokens: {summary['total_tokens']}")
    print(f"- Duration: {summary['duration_minutes']:.1f} minutes")
    
    # Memory statistics
    stats = memory.get_memory_stats()
    print(f"\nMemory stats:")
    print(f"- Active entries: {stats['active_context_entries']}")
    print(f"- Active tokens: {stats['active_context_tokens']}")
    print(f"- Context utilization: {stats['context_utilization']:.1%}")
    
    # End session
    memory.end_session()
    print(f"\nSession ended and saved")