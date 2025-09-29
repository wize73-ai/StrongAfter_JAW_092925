"""
StrongAfter Therapy Blackboard - Shared Memory System
=====================================================

Core blackboard implementation providing thread-safe shared memory space
for multi-agent collaboration in trauma recovery assistance processing.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

The blackboard serves as a centralized knowledge space where specialized
agents can read and write information to collaboratively process therapeutic
requests while maintaining data integrity and processing coordination.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading


logger = logging.getLogger(__name__)


@dataclass
class BlackboardEntry:
    """Represents a single entry on the blackboard"""
    key: str
    value: Any
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TherapyBlackboard:
    """
    Central blackboard for therapy processing system.

    Manages shared state between multiple Knowledge Source agents
    and provides thread-safe access to data.
    """

    def __init__(self):
        self._data: Dict[str, BlackboardEntry] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self.processing_start_time = None
        self.metrics = {
            'total_writes': 0,
            'total_reads': 0,
            'agent_contributions': {},
            'processing_stages': {}
        }

        # Initialize data structure
        self._initialize_structure()

    def _initialize_structure(self):
        """Initialize blackboard with expected data structure"""
        initial_data = {
            'user_input': None,
            'preprocessed_text': None,
            'user_intent': None,
            'theme_candidates': [],
            'theme_scores': {},
            'selected_themes': [],
            'retrieved_excerpts': {},
            'excerpt_summaries': {},
            'partial_summaries': {},
            'citations': [],
            'final_response': None,
            'quality_score': None,
            'confidence_scores': {},
            'processing_status': {
                'theme_analysis': 'pending',
                'excerpt_retrieval': 'pending',
                'summary_generation': 'pending',
                'quality_assurance': 'pending'
            },
            'streaming_updates': [],
            'error_messages': [],
            'fallback_triggered': False
        }

        for key, value in initial_data.items():
            self._data[key] = BlackboardEntry(
                key=key,
                value=value,
                source='initialization',
                confidence=1.0
            )

    def write(self, key: str, value: Any, source: str, confidence: float = 1.0,
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Write data to the blackboard with source tracking

        Args:
            key: The data key
            value: The data value
            source: Source agent/system writing the data
            confidence: Confidence level (0.0 - 1.0)
            metadata: Additional metadata about the entry
        """
        with self._lock:
            entry = BlackboardEntry(
                key=key,
                value=value,
                source=source,
                confidence=confidence,
                metadata=metadata or {}
            )

            self._data[key] = entry
            self.metrics['total_writes'] += 1

            # Track agent contributions
            if source not in self.metrics['agent_contributions']:
                self.metrics['agent_contributions'][source] = 0
            self.metrics['agent_contributions'][source] += 1

            # Log significant writes
            logger.info(f"Blackboard write: {key} by {source} (confidence: {confidence})")

            # Notify subscribers
            self._notify_subscribers(key, entry)

    def read(self, key: str) -> Any:
        """
        Read data from the blackboard

        Args:
            key: The data key to read

        Returns:
            The value associated with the key, or None if not found
        """
        with self._lock:
            self.metrics['total_reads'] += 1
            entry = self._data.get(key)
            return entry.value if entry else None

    def read_entry(self, key: str) -> Optional[BlackboardEntry]:
        """
        Read full entry including metadata from the blackboard

        Args:
            key: The data key to read

        Returns:
            The BlackboardEntry or None if not found
        """
        with self._lock:
            return self._data.get(key)

    def has_data(self, key: str) -> bool:
        """Check if blackboard has data for the given key"""
        with self._lock:
            entry = self._data.get(key)
            return entry is not None and entry.value is not None

    def is_ready_for(self, operation: str) -> bool:
        """
        Check if prerequisites are available for a given operation

        Args:
            operation: The operation to check prerequisites for

        Returns:
            True if all prerequisites are met
        """
        prerequisites = {
            'theme_analysis': ['preprocessed_text', 'theme_candidates'],
            'excerpt_retrieval': ['selected_themes'],
            'summary_generation': ['retrieved_excerpts', 'selected_themes'],
            'quality_assurance': ['final_response'],
            'streaming_update': ['theme_scores']
        }

        required = prerequisites.get(operation, [])
        return all(self.has_data(key) for key in required)

    def subscribe(self, key: str, callback: Callable[[BlackboardEntry], None]) -> None:
        """
        Subscribe to changes for a specific key

        Args:
            key: The key to subscribe to
            callback: Function to call when key is updated
        """
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(callback)

    def _notify_subscribers(self, key: str, entry: BlackboardEntry) -> None:
        """Notify subscribers of changes"""
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    callback(entry)
                except Exception as e:
                    logger.error(f"Error in subscriber callback for {key}: {e}")

    def get_processing_status(self) -> Dict[str, str]:
        """Get current processing status"""
        return self.read('processing_status') or {}

    def update_processing_status(self, stage: str, status: str, source: str) -> None:
        """Update processing status for a specific stage"""
        current_status = self.get_processing_status()
        current_status[stage] = status

        # Track timing
        if status == 'completed':
            if stage not in self.metrics['processing_stages']:
                self.metrics['processing_stages'][stage] = []

            stage_time = time.time() - (self.processing_start_time or time.time())
            self.metrics['processing_stages'][stage].append(stage_time)

        self.write('processing_status', current_status, source)

    def add_streaming_update(self, update: Dict[str, Any], source: str) -> None:
        """Add a streaming update for real-time user feedback"""
        updates = self.read('streaming_updates') or []
        update['timestamp'] = datetime.now().isoformat()
        update['source'] = source
        updates.append(update)
        self.write('streaming_updates', updates, source)

    def add_error(self, error_message: str, source: str, severity: str = 'error') -> None:
        """Add an error message to the blackboard"""
        errors = self.read('error_messages') or []
        error_entry = {
            'message': error_message,
            'source': source,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        errors.append(error_entry)
        self.write('error_messages', errors, source)
        logger.error(f"Blackboard error from {source}: {error_message}")

    def is_complete(self) -> bool:
        """Check if processing is complete"""
        return (self.has_data('final_response') and
                self.read('quality_score') is not None and
                self.read('quality_score') >= 0.7)

    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        with self._lock:
            total_time = None
            if self.processing_start_time:
                total_time = time.time() - self.processing_start_time

            return {
                **self.metrics,
                'total_processing_time': total_time,
                'blackboard_size': len(self._data),
                'completion_status': self.is_complete()
            }

    def start_processing(self) -> None:
        """Mark the start of processing"""
        self.processing_start_time = time.time()
        logger.info("Blackboard processing started")

    def clear(self) -> None:
        """Clear the blackboard (for testing)"""
        with self._lock:
            self._initialize_structure()
            self.processing_start_time = None
            self.metrics = {
                'total_writes': 0,
                'total_reads': 0,
                'agent_contributions': {},
                'processing_stages': {}
            }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current blackboard state"""
        with self._lock:
            return {
                'has_input': self.has_data('user_input'),
                'has_themes': self.has_data('selected_themes'),
                'has_excerpts': self.has_data('retrieved_excerpts'),
                'has_response': self.has_data('final_response'),
                'processing_status': self.get_processing_status(),
                'error_count': len(self.read('error_messages') or []),
                'metrics': self.get_metrics()
            }

    def __str__(self) -> str:
        """String representation of blackboard state"""
        summary = self.get_state_summary()
        return f"TherapyBlackboard(complete={self.is_complete()}, {summary})"