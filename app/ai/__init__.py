"""
AI Module - Phase 3 Scaffolding

This module contains interfaces and schemas for AI-powered features:
- Transaction clustering and grouping
- Confidence-scored adjustment suggestions

Note: This is scaffolding for future implementation. No model calls are made yet.
"""

from app.ai.transaction_clustering import (
    TransactionCluster,
    TransactionClusterer,
    ClusteringResult,
)
from app.ai.suggestion_schema import (
    AdjustmentSuggestion,
    SuggestionConfidence,
    AdjustmentSuggestionEngine,
)

__all__ = [
    "TransactionCluster",
    "TransactionClusterer",
    "ClusteringResult",
    "AdjustmentSuggestion",
    "SuggestionConfidence",
    "AdjustmentSuggestionEngine",
]

