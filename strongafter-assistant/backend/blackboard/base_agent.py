"""
Base Agent Class for Blackboard Knowledge Sources

Provides common functionality for all agents in the therapy processing system.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .blackboard import TherapyBlackboard


logger = logging.getLogger(__name__)


@dataclass
class AgentCapabilities:
    """Defines what an agent can do"""
    can_process_parallel: bool = True
    requires_gpu: bool = False
    estimated_processing_time: float = 1.0  # seconds
    confidence_threshold: float = 0.7
    fallback_available: bool = False


class BaseAgent(ABC):
    """
    Base class for all Knowledge Source agents in the blackboard system.

    Each agent is responsible for a specific aspect of therapy processing
    and can work independently while sharing information through the blackboard.
    """

    def __init__(self, name: str, blackboard: TherapyBlackboard, priority: int = 5,
                 capabilities: Optional[AgentCapabilities] = None):
        """
        Initialize the base agent

        Args:
            name: Unique name for this agent
            blackboard: Shared blackboard instance
            priority: Execution priority (higher = runs first)
            capabilities: Agent capabilities and constraints
        """
        self.name = name
        self.blackboard = blackboard
        self.priority = priority
        self.capabilities = capabilities or AgentCapabilities()

        # Agent state
        self.is_running = False
        self.last_execution_time = None
        self.execution_count = 0
        self.errors = []

        # Performance metrics
        self.metrics = {
            'total_executions': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'success_rate': 1.0,
            'last_confidence': 0.0
        }

        logger.info(f"Initialized agent: {self.name} (priority: {self.priority})")

    @abstractmethod
    def can_contribute(self) -> bool:
        """
        Check if this agent can contribute based on current blackboard state

        Returns:
            True if the agent can run, False otherwise
        """
        pass

    @abstractmethod
    async def contribute(self) -> Dict[str, Any]:
        """
        Main agent processing logic

        Returns:
            Dictionary containing processing results and metadata
        """
        pass

    def get_prerequisites(self) -> List[str]:
        """
        Get list of blackboard keys that must be available before this agent can run

        Returns:
            List of required blackboard keys
        """
        return []

    def get_outputs(self) -> List[str]:
        """
        Get list of blackboard keys that this agent will write

        Returns:
            List of blackboard keys this agent produces
        """
        return []

    async def execute(self) -> Dict[str, Any]:
        """
        Execute the agent with error handling and metrics tracking

        Returns:
            Execution results including success status and timing
        """
        if self.is_running:
            logger.warning(f"Agent {self.name} is already running")
            return {'success': False, 'error': 'Agent already running'}

        start_time = time.time()
        self.is_running = True
        result = {'success': False, 'agent': self.name}

        try:
            logger.info(f"Starting agent: {self.name}")

            # Check prerequisites
            if not self.can_contribute():
                result.update({
                    'success': False,
                    'error': 'Prerequisites not met',
                    'prerequisites': self.get_prerequisites()
                })
                return result

            # Update blackboard status
            self._update_processing_status('running')

            # Execute main logic
            contribution_result = await self.contribute()

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, True, contribution_result.get('confidence', 1.0))

            # Mark as completed
            self._update_processing_status('completed')

            result.update({
                'success': True,
                'execution_time': execution_time,
                'confidence': contribution_result.get('confidence', 1.0),
                'outputs': contribution_result.get('outputs', [])
            })

            logger.info(f"Agent {self.name} completed successfully in {execution_time:.2f}s")

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Agent {self.name} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Update metrics for failure
            self._update_metrics(execution_time, False, 0.0)

            # Add error to blackboard
            self.blackboard.add_error(error_msg, self.name)

            # Mark as failed
            self._update_processing_status('failed')

            result.update({
                'success': False,
                'error': error_msg,
                'execution_time': execution_time
            })

        finally:
            self.is_running = False
            self.last_execution_time = time.time()
            self.execution_count += 1

        return result

    def _update_processing_status(self, status: str) -> None:
        """Update processing status on blackboard"""
        stage_name = self.name.lower().replace('agent', '').replace('_', '')
        self.blackboard.update_processing_status(stage_name, status, self.name)

    def _update_metrics(self, execution_time: float, success: bool, confidence: float) -> None:
        """Update agent performance metrics"""
        self.metrics['total_executions'] += 1
        self.metrics['total_time'] += execution_time

        if self.metrics['total_executions'] > 0:
            self.metrics['average_time'] = self.metrics['total_time'] / self.metrics['total_executions']

        # Update success rate
        if success:
            old_successes = self.metrics['success_rate'] * (self.metrics['total_executions'] - 1)
            self.metrics['success_rate'] = (old_successes + 1) / self.metrics['total_executions']
        else:
            old_successes = self.metrics['success_rate'] * (self.metrics['total_executions'] - 1)
            self.metrics['success_rate'] = old_successes / self.metrics['total_executions']

        self.metrics['last_confidence'] = confidence

    def can_run_parallel_with(self, other_agent: 'BaseAgent') -> bool:
        """
        Check if this agent can run in parallel with another agent

        Args:
            other_agent: Another agent to check compatibility with

        Returns:
            True if agents can run in parallel
        """
        if not self.capabilities.can_process_parallel:
            return False

        if not other_agent.capabilities.can_process_parallel:
            return False

        # Check for resource conflicts
        if self.capabilities.requires_gpu and other_agent.capabilities.requires_gpu:
            return False

        # Check for data dependencies
        my_outputs = set(self.get_outputs())
        other_prerequisites = set(other_agent.get_prerequisites())

        # Can't run in parallel if one depends on the other's output
        if my_outputs.intersection(other_prerequisites):
            return False

        other_outputs = set(other_agent.get_outputs())
        my_prerequisites = set(self.get_prerequisites())

        if other_outputs.intersection(my_prerequisites):
            return False

        return True

    def get_estimated_completion_time(self) -> float:
        """
        Get estimated completion time based on historical performance

        Returns:
            Estimated time in seconds
        """
        if self.metrics['average_time'] > 0:
            return self.metrics['average_time']
        return self.capabilities.estimated_processing_time

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and metrics

        Returns:
            Dictionary containing agent status information
        """
        return {
            'name': self.name,
            'priority': self.priority,
            'is_running': self.is_running,
            'can_contribute': self.can_contribute(),
            'capabilities': self.capabilities,
            'metrics': self.metrics,
            'last_execution': self.last_execution_time,
            'execution_count': self.execution_count
        }

    def reset(self) -> None:
        """Reset agent state (useful for testing)"""
        self.is_running = False
        self.last_execution_time = None
        self.execution_count = 0
        self.errors.clear()
        self.metrics = {
            'total_executions': 0,
            'total_time': 0.0,
            'average_time': 0.0,
            'success_rate': 1.0,
            'last_confidence': 0.0
        }

    def __str__(self) -> str:
        """String representation of the agent"""
        status = "running" if self.is_running else "idle"
        can_run = "ready" if self.can_contribute() else "waiting"
        return f"{self.name}(status={status}, can_run={can_run}, priority={self.priority})"

    def __repr__(self) -> str:
        return self.__str__()