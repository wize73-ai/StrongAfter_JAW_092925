"""
StrongAfter Blackboard Control Strategy - Agent Orchestration
============================================================

Multi-agent coordination system for optimized therapeutic content processing.
Implements parallel, sequential, and hybrid execution strategies.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

This module provides intelligent agent orchestration with:
- Adaptive execution strategies based on content complexity
- Parallel processing for independent agent tasks
- Quality-first routing for sensitive trauma content
- Performance metrics and optimization tracking
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .blackboard import TherapyBlackboard
from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Different execution strategies for agent orchestration"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


@dataclass
class ExecutionPlan:
    """Plan for executing agents"""
    parallel_groups: List[List[BaseAgent]]
    sequential_phases: List[List[BaseAgent]]
    estimated_time: float
    strategy: ExecutionStrategy


class BlackboardControlStrategy:
    """
    Intelligent control strategy for orchestrating therapy processing agents.

    Features:
    - Parallel execution of compatible agents
    - Dynamic scheduling based on prerequisites
    - Adaptive processing based on confidence levels
    - Streaming updates and progress monitoring
    - Fault tolerance with fallback strategies
    """

    def __init__(self, blackboard: TherapyBlackboard, agents: List[BaseAgent], themes_data: Optional[List[Dict]] = None):
        """
        Initialize the control strategy

        Args:
            blackboard: Shared blackboard instance
            agents: List of available agents
            themes_data: Pre-loaded themes data
        """
        self.blackboard = blackboard
        self.agents = {agent.name: agent for agent in agents}
        self.themes_data = themes_data or []
        self.execution_history = []
        self.max_iterations = 20
        self.default_timeout = 60.0

        # Performance tracking
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'total_time': 0.0,
            'parallel_efficiency': 0.0,
            'agent_utilization': {}
        }

        logger.info(f"Initialized control strategy with {len(self.agents)} agents")

    async def execute(self, user_input: str, strategy: ExecutionStrategy = ExecutionStrategy.HYBRID) -> Dict[str, Any]:
        """
        Main execution method for processing therapy requests

        Args:
            user_input: User's input text
            strategy: Execution strategy to use

        Returns:
            Final processing results
        """
        start_time = time.time()
        self.blackboard.start_processing()

        try:
            logger.info(f"Starting blackboard execution with strategy: {strategy.value}")

            # Initialize blackboard with user input
            await self._initialize_processing(user_input)

            # Create execution plan
            execution_plan = self._create_execution_plan(strategy)

            # Execute the plan
            results = await self._execute_plan(execution_plan)

            # Finalize and return results
            final_results = await self._finalize_results(results, start_time)

            self._update_metrics(start_time, True)
            logger.info(f"Blackboard execution completed successfully in {time.time() - start_time:.2f}s")

            return final_results

        except Exception as e:
            self._update_metrics(start_time, False)
            logger.error(f"Blackboard execution failed: {e}", exc_info=True)
            return await self._handle_execution_failure(e, start_time)

    async def _initialize_processing(self, user_input: str) -> None:
        """Initialize the blackboard with user input and preprocessing"""
        # Load themes and initialize data
        themes = await self._load_themes()

        # Write initial data to blackboard
        self.blackboard.write('user_input', user_input, 'ControlStrategy')
        self.blackboard.write('preprocessed_text', self._preprocess_text(user_input), 'ControlStrategy')
        self.blackboard.write('theme_candidates', themes, 'ControlStrategy')

        logger.info("Blackboard initialized with user input and themes")

    async def _load_themes(self) -> List[Dict]:
        """Load theme data from pre-loaded themes"""
        return self.themes_data

    def _preprocess_text(self, text: str) -> str:
        """Preprocess user input text"""
        # Basic preprocessing
        return text.strip().lower() if text else ""

    def _create_execution_plan(self, strategy: ExecutionStrategy) -> ExecutionPlan:
        """
        Create an execution plan based on strategy and agent dependencies

        Args:
            strategy: Execution strategy to use

        Returns:
            ExecutionPlan with parallel groups and phases
        """
        if strategy == ExecutionStrategy.SEQUENTIAL:
            return self._create_sequential_plan()
        elif strategy == ExecutionStrategy.PARALLEL:
            return self._create_parallel_plan()
        elif strategy == ExecutionStrategy.HYBRID:
            return self._create_hybrid_plan()
        else:  # ADAPTIVE
            return self._create_adaptive_plan()

    def _create_sequential_plan(self) -> ExecutionPlan:
        """Create a purely sequential execution plan"""
        sorted_agents = sorted(self.agents.values(), key=lambda a: a.priority, reverse=True)

        return ExecutionPlan(
            parallel_groups=[],
            sequential_phases=[[agent] for agent in sorted_agents],
            estimated_time=sum(agent.get_estimated_completion_time() for agent in sorted_agents),
            strategy=ExecutionStrategy.SEQUENTIAL
        )

    def _create_parallel_plan(self) -> ExecutionPlan:
        """Create a maximally parallel execution plan"""
        compatible_groups = self._find_parallel_groups()

        return ExecutionPlan(
            parallel_groups=compatible_groups,
            sequential_phases=[],
            estimated_time=max(
                sum(agent.get_estimated_completion_time() for agent in group)
                for group in compatible_groups
            ) if compatible_groups else 0.0,
            strategy=ExecutionStrategy.PARALLEL
        )

    def _create_hybrid_plan(self) -> ExecutionPlan:
        """Create a hybrid plan with both parallel and sequential phases"""
        # Phase 1: Theme analysis with Gemini (high-quality semantic understanding)
        phase1_agents = [
            agent for agent in self.agents.values()
            if agent.name in ['ThemeAnalysisAgent', 'StreamingAgent']
        ]

        # Phase 2: Excerpt retrieval (depends on selected_themes from Phase 1)
        phase2_agents = [
            agent for agent in self.agents.values()
            if agent.name == 'ExcerptRetrievalAgent'
        ]

        # Phase 3: Summary generation (depends on retrieved_excerpts from Phase 2)
        phase3_agents = [
            agent for agent in self.agents.values()
            if agent.name == 'SummaryGenerationAgent'
        ]

        # Phase 4: Quality assurance (depends on final_response from Phase 3)
        phase4_agents = [
            agent for agent in self.agents.values()
            if agent.name == 'QualityAssuranceAgent'
        ]

        parallel_groups = []
        if phase1_agents:
            parallel_groups.append(phase1_agents)

        sequential_phases = []
        if phase2_agents:
            sequential_phases.append(phase2_agents)
        if phase3_agents:
            sequential_phases.append(phase3_agents)
        if phase4_agents:
            sequential_phases.append(phase4_agents)

        estimated_time = (
            (max(agent.get_estimated_completion_time() for agent in phase1_agents) if phase1_agents else 0.0) +
            (sum(agent.get_estimated_completion_time() for agent in phase2_agents) if phase2_agents else 0.0) +
            (sum(agent.get_estimated_completion_time() for agent in phase3_agents) if phase3_agents else 0.0) +
            (sum(agent.get_estimated_completion_time() for agent in phase4_agents) if phase4_agents else 0.0)
        )

        return ExecutionPlan(
            parallel_groups=parallel_groups,
            sequential_phases=sequential_phases,
            estimated_time=estimated_time,
            strategy=ExecutionStrategy.HYBRID
        )

    def _create_adaptive_plan(self) -> ExecutionPlan:
        """Create an adaptive plan that changes based on runtime conditions"""
        # Start with hybrid plan, but allow for dynamic adjustment
        return self._create_hybrid_plan()

    def _find_parallel_groups(self) -> List[List[BaseAgent]]:
        """Find groups of agents that can run in parallel"""
        agents = list(self.agents.values())
        groups = []

        # Simple greedy algorithm to group compatible agents
        remaining_agents = agents.copy()

        while remaining_agents:
            current_group = [remaining_agents.pop(0)]

            # Find agents compatible with current group
            for agent in remaining_agents.copy():
                if all(agent.can_run_parallel_with(group_member) for group_member in current_group):
                    current_group.append(agent)
                    remaining_agents.remove(agent)

            groups.append(current_group)

        return groups

    async def _execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Execute the given execution plan

        Args:
            plan: ExecutionPlan to execute

        Returns:
            Execution results
        """
        results = {
            'parallel_results': [],
            'sequential_results': [],
            'total_agents_executed': 0,
            'successful_agents': 0
        }

        # Execute parallel groups
        for i, group in enumerate(plan.parallel_groups):
            logger.info(f"Executing parallel group {i + 1}/{len(plan.parallel_groups)} with {len(group)} agents")

            group_results = await self._execute_parallel_group(group)
            results['parallel_results'].append(group_results)

            successful = sum(1 for r in group_results if r.get('success', False))
            results['total_agents_executed'] += len(group)
            results['successful_agents'] += successful

        # Execute sequential phases
        for i, phase in enumerate(plan.sequential_phases):
            logger.info(f"Executing sequential phase {i + 1}/{len(plan.sequential_phases)} with {len(phase)} agents")

            phase_results = await self._execute_sequential_phase(phase)
            results['sequential_results'].append(phase_results)

            successful = sum(1 for r in phase_results if r.get('success', False))
            results['total_agents_executed'] += len(phase)
            results['successful_agents'] += successful

        return results

    async def _execute_parallel_group(self, agents: List[BaseAgent]) -> List[Dict[str, Any]]:
        """Execute a group of agents in parallel"""
        # Filter agents that can actually contribute
        ready_agents = [agent for agent in agents if agent.can_contribute()]

        if not ready_agents:
            logger.warning("No agents ready to contribute in parallel group")
            return []

        # Create tasks for parallel execution
        tasks = [agent.execute() for agent in ready_agents]

        try:
            # Execute with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.default_timeout
            )

            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {ready_agents[i].name} failed with exception: {result}")
                    processed_results.append({
                        'success': False,
                        'agent': ready_agents[i].name,
                        'error': str(result)
                    })
                else:
                    processed_results.append(result)

            return processed_results

        except asyncio.TimeoutError:
            logger.error(f"Parallel group execution timed out after {self.default_timeout}s")
            return [{'success': False, 'error': 'Timeout'} for _ in ready_agents]

    async def _execute_sequential_phase(self, agents: List[BaseAgent]) -> List[Dict[str, Any]]:
        """Execute agents sequentially within a phase"""
        results = []

        for agent in agents:
            if agent.can_contribute():
                try:
                    result = await asyncio.wait_for(agent.execute(), timeout=self.default_timeout)
                    results.append(result)

                    # Check if we should stop early
                    if not result.get('success', False):
                        logger.warning(f"Agent {agent.name} failed, considering early termination")

                except asyncio.TimeoutError:
                    logger.error(f"Agent {agent.name} timed out")
                    results.append({'success': False, 'agent': agent.name, 'error': 'Timeout'})

            else:
                logger.info(f"Agent {agent.name} not ready to contribute, skipping")

        return results

    async def _finalize_results(self, execution_results: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Finalize and format the results"""
        # Get final response from blackboard
        final_response = self.blackboard.read('final_response')
        selected_themes = self.blackboard.read('selected_themes')
        quality_score = self.blackboard.read('quality_score')
        processing_status = self.blackboard.get_processing_status()

        # Extract summary text from response object if needed
        summary_text = ''
        if final_response:
            if isinstance(final_response, dict) and 'summary' in final_response:
                summary_text = final_response['summary']
            elif isinstance(final_response, str):
                summary_text = final_response
            else:
                summary_text = str(final_response)

        # Compile comprehensive results with direct access to themes and summary
        results = {
            'themes': selected_themes or [],
            'summary': summary_text,
            'quality_score': quality_score,
            'processing_time': time.time() - start_time,
            'processing_status': processing_status,
            'execution_metrics': execution_results,
            'blackboard_metrics': self.blackboard.get_metrics(),
            'agent_status': {name: agent.get_status() for name, agent in self.agents.items()}
        }

        # Add streaming updates if available
        streaming_updates = self.blackboard.read('streaming_updates')
        if streaming_updates:
            results['streaming_updates'] = streaming_updates

        return results

    async def _handle_execution_failure(self, error: Exception, start_time: float) -> Dict[str, Any]:
        """Handle execution failure with graceful degradation"""
        logger.error(f"Execution failed, attempting graceful degradation: {error}")

        # Try to return partial results
        partial_response = self.blackboard.read('final_response')
        themes = self.blackboard.read('selected_themes')

        return {
            'success': False,
            'error': str(error),
            'partial_response': partial_response,
            'partial_themes': themes,
            'processing_time': time.time() - start_time,
            'blackboard_state': self.blackboard.get_state_summary()
        }

    def _update_metrics(self, start_time: float, success: bool) -> None:
        """Update control strategy metrics"""
        execution_time = time.time() - start_time

        self.metrics['total_executions'] += 1
        self.metrics['total_time'] += execution_time

        if success:
            self.metrics['successful_executions'] += 1

        # Calculate success rate
        self.metrics['success_rate'] = (
            self.metrics['successful_executions'] / self.metrics['total_executions']
        )

        # Update agent utilization
        for agent_name, agent in self.agents.items():
            if agent_name not in self.metrics['agent_utilization']:
                self.metrics['agent_utilization'][agent_name] = {
                    'executions': 0,
                    'total_time': 0.0,
                    'success_rate': 0.0
                }

            agent_metrics = agent.metrics
            self.metrics['agent_utilization'][agent_name] = {
                'executions': agent_metrics['total_executions'],
                'total_time': agent_metrics['total_time'],
                'success_rate': agent_metrics['success_rate']
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get control strategy metrics"""
        return self.metrics.copy()

    def reset(self) -> None:
        """Reset control strategy state"""
        self.execution_history.clear()
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'total_time': 0.0,
            'parallel_efficiency': 0.0,
            'agent_utilization': {}
        }

        # Reset all agents
        for agent in self.agents.values():
            agent.reset()

        logger.info("Control strategy reset completed")