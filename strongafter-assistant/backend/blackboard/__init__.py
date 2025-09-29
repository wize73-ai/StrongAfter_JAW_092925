"""
StrongAfter Blackboard Architecture Package
==========================================

Multi-agent blackboard system for trauma recovery assistance processing.

Author: JAWilson
Created: September 2025
License: Proprietary - StrongAfter Systems

This package implements the blackboard architectural pattern for
coordinating multiple specialized AI agents in therapeutic content processing.
"""
from .blackboard import TherapyBlackboard
from .control_strategy import BlackboardControlStrategy
from .knowledge_sources import (
    ThemeAnalysisAgent,
    ExcerptRetrievalAgent,
    SummaryGenerationAgent,
    QualityAssuranceAgent,
    StreamingAgent
)

__all__ = [
    'TherapyBlackboard',
    'BlackboardControlStrategy',
    'ThemeAnalysisAgent',
    'ExcerptRetrievalAgent',
    'SummaryGenerationAgent',
    'QualityAssuranceAgent',
    'StreamingAgent'
]