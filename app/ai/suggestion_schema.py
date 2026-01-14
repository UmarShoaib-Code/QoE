"""
Adjustment Suggestion Schema - Phase 3 AI Scaffolding

Interfaces for AI-powered adjustment suggestions with confidence scoring.
This module provides the structure for generating intelligent suggestions
for EBITDA adjustments based on transaction analysis.

TODO: Implement actual suggestion generation using LLM/ML models to:
      - Analyze transaction patterns
      - Identify non-recurring or one-time expenses
      - Suggest appropriate adjustment categories
      - Provide confidence scores and reasoning
"""

import pandas as pd
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class SuggestionConfidence(str, Enum):
    """Confidence levels for adjustment suggestions"""

    HIGH = "high"  # 0.8 - 1.0: Very confident suggestion
    MEDIUM = "medium"  # 0.5 - 0.8: Moderately confident suggestion
    LOW = "low"  # 0.0 - 0.5: Low confidence, needs review
    VERY_LOW = "very_low"  # < 0.3: Very uncertain, likely not useful


class AdjustmentCategory(str, Enum):
    """Standard adjustment categories"""

    ONE_TIME_EXPENSE = "One-Time Expense"
    NON_RECURRING_REVENUE = "Non-Recurring Revenue"
    DISCRETIONARY_EXPENSE = "Discretionary Expense"
    OWNER_COMPENSATION = "Owner Compensation"
    DEPRECIATION_AMORTIZATION = "Depreciation & Amortization"
    INTEREST_EXPENSE = "Interest Expense"
    TAX_ADJUSTMENT = "Tax Adjustment"
    NORMALIZING_ADJUSTMENT = "Normalizing Adjustment"
    OTHER = "Other"


@dataclass
class AdjustmentSuggestion:
    """
    Represents an AI-generated suggestion for an EBITDA adjustment.

    Each suggestion includes:
    - Which transactions to adjust
    - What category the adjustment belongs to
    - Confidence score
    - Reasoning/explanation
    - Suggested adjustment amount
    """

    suggestion_id: str
    transaction_ids: List[int]  # row_id values from normalized_df
    adjustment_category: AdjustmentCategory
    suggested_amount: float
    add_back: bool  # True = add back to EBITDA, False = subtract
    confidence_score: float  # 0.0 to 1.0
    confidence_level: SuggestionConfidence
    reasoning: str  # AI-generated explanation
    supporting_evidence: List[str] = field(
        default_factory=list
    )  # Key phrases/patterns that support the suggestion
    alternative_categories: List[AdjustmentCategory] = field(
        default_factory=list
    )  # Other possible categories if confidence is low
    suggested_reasoning_template: str = ""  # Template for user-facing explanation
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary"""
        return {
            "suggestion_id": self.suggestion_id,
            "transaction_ids": self.transaction_ids,
            "adjustment_category": self.adjustment_category.value,
            "suggested_amount": self.suggested_amount,
            "add_back": self.add_back,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level.value,
            "reasoning": self.reasoning,
            "supporting_evidence": self.supporting_evidence,
            "alternative_categories": [
                cat.value for cat in self.alternative_categories
            ],
            "suggested_reasoning_template": self.suggested_reasoning_template,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdjustmentSuggestion":
        """Create suggestion from dictionary"""
        return cls(
            suggestion_id=data["suggestion_id"],
            transaction_ids=data["transaction_ids"],
            adjustment_category=AdjustmentCategory(data["adjustment_category"]),
            suggested_amount=data["suggested_amount"],
            add_back=data["add_back"],
            confidence_score=data["confidence_score"],
            confidence_level=SuggestionConfidence(data["confidence_level"]),
            reasoning=data["reasoning"],
            supporting_evidence=data.get("supporting_evidence", []),
            alternative_categories=[
                AdjustmentCategory(cat)
                for cat in data.get("alternative_categories", [])
            ],
            suggested_reasoning_template=data.get("suggested_reasoning_template", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
        )


@dataclass
class SuggestionBatch:
    """Batch of adjustment suggestions"""

    suggestions: List[AdjustmentSuggestion]
    total_suggested_adjustment: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary"""
        return {
            "suggestions": [s.to_dict() for s in self.suggestions],
            "total_suggested_adjustment": self.total_suggested_adjustment,
            "high_confidence_count": self.high_confidence_count,
            "medium_confidence_count": self.medium_confidence_count,
            "low_confidence_count": self.low_confidence_count,
            "metadata": self.metadata,
        }


class AdjustmentSuggestionEngine:
    """
    Interface for AI-powered adjustment suggestion generation.

    This class defines the interface for generating intelligent suggestions
    for EBITDA adjustments based on transaction analysis. The engine uses
    AI/ML to identify patterns, classify transactions, and suggest appropriate
    adjustments with confidence scores.

    TODO: Implement suggestion generation using:
          - LLM-based transaction analysis
          - Pattern recognition for non-recurring items
          - Classification models for adjustment categories
          - Confidence scoring based on model outputs
          - Reasoning generation for transparency
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.5,
        max_suggestions_per_category: Optional[int] = None,
        include_low_confidence: bool = False,
    ):
        """
        Initialize adjustment suggestion engine.

        Args:
            min_confidence_threshold: Minimum confidence score to include suggestion (0.0 to 1.0)
            max_suggestions_per_category: Maximum suggestions per category (None = no limit)
            include_low_confidence: Whether to include low-confidence suggestions
        """
        self.min_confidence_threshold = min_confidence_threshold
        self.max_suggestions_per_category = max_suggestions_per_category
        self.include_low_confidence = include_low_confidence

    def generate_suggestions(
        self,
        normalized_df: pd.DataFrame,
        transaction_clusters: Optional[List[Any]] = None,  # TransactionCluster objects
        account_column: str = "account_name_flat",
        description_column: str = "description",
        amount_column: str = "amount_net",
        date_column: str = "date",
    ) -> SuggestionBatch:
        """
        Generate adjustment suggestions for GL transactions.

        Analyzes transactions and generates suggestions for EBITDA adjustments
        based on AI/ML analysis of patterns, descriptions, and account structures.

        Args:
            normalized_df: Normalized GL DataFrame with transactions
            transaction_clusters: Optional pre-computed transaction clusters
            account_column: Column name for account names
            description_column: Column name for transaction descriptions
            amount_column: Column name for transaction amounts
            date_column: Column name for transaction dates

        Returns:
            SuggestionBatch with generated suggestions and metadata

        TODO: Implement suggestion generation:
              1. Analyze transaction descriptions using LLM for semantic understanding
              2. Identify patterns indicating non-recurring or one-time items
              3. Classify transactions into adjustment categories
              4. Calculate confidence scores based on model certainty
              5. Generate reasoning explanations for each suggestion
              6. Filter suggestions based on confidence thresholds
              7. Group related suggestions if using transaction clusters
        """
        # TODO: Implement suggestion generation logic
        # For now, return empty batch structure
        return SuggestionBatch(
            suggestions=[],
            total_suggested_adjustment=0.0,
            high_confidence_count=0,
            medium_confidence_count=0,
            low_confidence_count=0,
        )

    def suggest_one_time_expenses(
        self,
        normalized_df: pd.DataFrame,
        description_column: str = "description",
    ) -> List[AdjustmentSuggestion]:
        """
        Generate suggestions for one-time expenses.

        Identifies transactions that appear to be one-time or non-recurring
        expenses that should be added back to EBITDA.

        Args:
            normalized_df: Normalized GL DataFrame
            description_column: Column name for transaction descriptions

        Returns:
            List of AdjustmentSuggestion objects for one-time expenses

        TODO: Implement one-time expense detection:
              1. Use LLM to analyze descriptions for one-time indicators
              2. Check for keywords like "settlement", "one-time", "legal", etc.
              3. Compare against historical patterns
              4. Generate confidence scores
        """
        # TODO: Implement one-time expense detection
        return []

    def suggest_discretionary_expenses(
        self,
        normalized_df: pd.DataFrame,
        account_column: str = "account_name_flat",
        amount_column: str = "amount_net",
    ) -> List[AdjustmentSuggestion]:
        """
        Generate suggestions for discretionary expenses.

        Identifies expenses that are discretionary and could be normalized
        for EBITDA calculations (e.g., excessive marketing spend, owner perks).

        Args:
            normalized_df: Normalized GL DataFrame
            account_column: Column name for account names
            amount_column: Column name for transaction amounts

        Returns:
            List of AdjustmentSuggestion objects for discretionary expenses

        TODO: Implement discretionary expense detection:
              1. Analyze account categories for discretionary spending
              2. Compare amounts against industry benchmarks
              3. Use LLM to understand context and suggest normalization
        """
        # TODO: Implement discretionary expense detection
        return []

    def suggest_owner_compensation_adjustments(
        self,
        normalized_df: pd.DataFrame,
        account_column: str = "account_name_flat",
    ) -> List[AdjustmentSuggestion]:
        """
        Generate suggestions for owner compensation adjustments.

        Identifies owner-related compensation that should be normalized
        to market rates for EBITDA calculations.

        Args:
            normalized_df: Normalized GL DataFrame
            account_column: Column name for account names

        Returns:
            List of AdjustmentSuggestion objects for owner compensation

        TODO: Implement owner compensation detection:
              1. Identify owner-related accounts
              2. Compare against market rates
              3. Suggest normalization adjustments
        """
        # TODO: Implement owner compensation detection
        return []

    def _calculate_confidence_score(
        self,
        model_output: Dict[str, Any],
        transaction_context: Dict[str, Any],
    ) -> float:
        """
        Calculate confidence score for a suggestion.

        Args:
            model_output: Raw output from AI/ML model
            transaction_context: Context about the transaction(s)

        Returns:
            Confidence score between 0.0 and 1.0

        TODO: Implement confidence scoring logic based on:
              - Model prediction probability
              - Transaction pattern strength
              - Historical accuracy of similar suggestions
        """
        # TODO: Implement confidence scoring
        return 0.0

    def _generate_reasoning(
        self,
        transaction_ids: List[int],
        category: AdjustmentCategory,
        normalized_df: pd.DataFrame,
    ) -> str:
        """
        Generate human-readable reasoning for a suggestion.

        Args:
            transaction_ids: IDs of transactions being adjusted
            category: Adjustment category
            normalized_df: Normalized GL DataFrame

        Returns:
            Reasoning text explaining the suggestion

        TODO: Implement reasoning generation using LLM:
              - Summarize transaction details
              - Explain why adjustment is suggested
              - Reference patterns or evidence
        """
        # TODO: Implement reasoning generation
        return ""

