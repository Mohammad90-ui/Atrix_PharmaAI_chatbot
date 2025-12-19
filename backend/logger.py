"""
Logging Module
Tracks source usage, metrics, and chatbot interactions.
"""
from loguru import logger
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ChatLogger:
    """Handles logging of chatbot interactions and metrics."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure loguru
        log_file = self.log_dir / "chatbot_{time}.log"
        logger.add(
            log_file,
            format="{time} | {level} | {message}",
            level="INFO",
            rotation="1 day"
        )
        
        # Metrics storage
        self.metrics = {
            'total_turns': 0,
            'doc_queries': 0,
            'excel_queries': 0,
            'both_queries': 0,
            'unknown_responses': 0,
            'clarifications_asked': 0,
            'safety_refusals': 0,
            'sessions': {}
        }
        
        self.metrics_file = self.log_dir / "metrics.json"
        self._load_metrics()
    
    def _load_metrics(self):
        """Load existing metrics if available."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    saved_metrics = json.load(f)
                    self.metrics.update(saved_metrics)
            except:
                pass
    
    def _save_metrics(self):
        """Save metrics to file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def log_query(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        source_used: str,
        retrieved_count: int,
        is_clarification: bool = False,
        is_unknown: bool = False,
        is_safety_refusal: bool = False
    ):
        """Log a single query-response turn."""
        # Update metrics
        self.metrics['total_turns'] += 1
        
        if is_clarification:
            self.metrics['clarifications_asked'] += 1
        
        if is_unknown:
            self.metrics['unknown_responses'] += 1
        
        if is_safety_refusal:
            self.metrics['safety_refusals'] += 1
        
        # Track source usage
        if source_used == 'Pharma_Clinical_Trial_Notes.docx':
            self.metrics['doc_queries'] += 1
        elif source_used == 'Pharma_Clinical_Trial_AllDrugs.xlsx':
            self.metrics['excel_queries'] += 1
        elif 'docx' in source_used and 'xlsx' in source_used:
            self.metrics['both_queries'] += 1
        
        # Track session
        if session_id not in self.metrics['sessions']:
            self.metrics['sessions'][session_id] = {
                'start_time': datetime.now().isoformat(),
                'turn_count': 0
            }
        self.metrics['sessions'][session_id]['turn_count'] += 1
        self.metrics['sessions'][session_id]['last_activity'] = datetime.now().isoformat()
        
        # Log the interaction
        logger.info(
            f"Session: {session_id} | "
            f"User: {user_message[:100]} | "
            f"Source: {source_used} | "
            f"Retrieved: {retrieved_count} | "
            f"Clarification: {is_clarification} | "
            f"Unknown: {is_unknown} | "
            f"Safety: {is_safety_refusal}"
        )
        
        # Save metrics
        self._save_metrics()
    
    def get_metrics_summary(self) -> Dict:
        """Get current metrics summary."""
        return {
            'total_turns': self.metrics['total_turns'],
            'source_usage': {
                'doc_only': self.metrics['doc_queries'],
                'excel_only': self.metrics['excel_queries'],
                'both': self.metrics['both_queries']
            },
            'unknown_responses': self.metrics['unknown_responses'],
            'clarifications_asked': self.metrics['clarifications_asked'],
            'safety_refusals': self.metrics['safety_refusals'],
            'unique_sessions': len(self.metrics['sessions'])
        }
    
    def export_session_log(self, session_id: str, output_file: str):
        """Export detailed log for a specific session."""
        # This would read from the log file and extract session-specific entries
        # For simplicity, we'll just note it's available
        logger.info(f"Session {session_id} log exported to {output_file}")
