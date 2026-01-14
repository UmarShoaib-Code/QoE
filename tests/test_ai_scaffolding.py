"""
Tests for Phase 3 AI Scaffolding

These tests verify that the AI module interfaces are properly defined
and can be instantiated. No actual AI/ML functionality is tested yet.
"""

import pytest
import pandas as pd
from datetime import datetime

from app.ai.transaction_clustering import (
    TransactionCluster,
    TransactionClusterer,
    ClusteringResult,
    ClusteringMethod,
)
from app.ai.suggestion_schema import (
    AdjustmentSuggestion,
    AdjustmentSuggestionEngine,
    SuggestionBatch,
    SuggestionConfidence,
    AdjustmentCategory,
)


@pytest.mark.unit
class TestTransactionClusteringScaffolding:
    """Test transaction clustering interfaces"""

    def test_transaction_cluster_creation(self):
        """Test creating a TransactionCluster"""
        cluster = TransactionCluster(
            cluster_id="test_001",
            cluster_name="Monthly Recurring Expenses",
            transaction_ids=[1, 2, 3],
            total_amount=1500.0,
            transaction_count=3,
            confidence_score=0.85,
        )
        assert cluster.cluster_id == "test_001"
        assert cluster.transaction_count == 3
        assert cluster.confidence_score == 0.85

    def test_transaction_cluster_to_dict(self):
        """Test converting cluster to dictionary"""
        cluster = TransactionCluster(
            cluster_id="test_002",
            cluster_name="Test Cluster",
            transaction_ids=[1, 2],
            total_amount=100.0,
            transaction_count=2,
        )
        cluster_dict = cluster.to_dict()
        assert cluster_dict["cluster_id"] == "test_002"
        assert cluster_dict["transaction_ids"] == [1, 2]

    def test_clustering_result_creation(self):
        """Test creating a ClusteringResult"""
        clusters = [
            TransactionCluster(
                cluster_id="c1",
                cluster_name="Cluster 1",
                transaction_ids=[1, 2],
                total_amount=200.0,
                transaction_count=2,
            )
        ]
        result = ClusteringResult(
            clusters=clusters,
            unclustered_transaction_ids=[3, 4],
            total_transactions=4,
            clustered_transactions=2,
            clustering_method=ClusteringMethod.SEMANTIC_SIMILARITY,
        )
        assert result.total_transactions == 4
        assert result.clustering_coverage == 0.5  # 2/4

    def test_transaction_clusterer_initialization(self):
        """Test initializing TransactionClusterer"""
        clusterer = TransactionClusterer(
            method=ClusteringMethod.SEMANTIC_SIMILARITY,
            min_cluster_size=2,
            similarity_threshold=0.7,
        )
        assert clusterer.method == ClusteringMethod.SEMANTIC_SIMILARITY
        assert clusterer.min_cluster_size == 2
        assert clusterer.similarity_threshold == 0.7

    def test_cluster_transactions_interface(self):
        """Test that cluster_transactions method exists and returns ClusteringResult"""
        clusterer = TransactionClusterer()
        df = pd.DataFrame(
            {
                "row_id": [1, 2, 3],
                "account_name_flat": ["Expense A", "Expense B", "Expense C"],
                "description": ["Desc 1", "Desc 2", "Desc 3"],
                "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
                "amount_net": [100.0, 200.0, 300.0],
            }
        )
        result = clusterer.cluster_transactions(df)
        assert isinstance(result, ClusteringResult)
        assert result.total_transactions == 3
        # Should return empty clusters for now (scaffolding)
        assert len(result.clusters) == 0


@pytest.mark.unit
class TestAdjustmentSuggestionScaffolding:
    """Test adjustment suggestion interfaces"""

    def test_adjustment_suggestion_creation(self):
        """Test creating an AdjustmentSuggestion"""
        suggestion = AdjustmentSuggestion(
            suggestion_id="sug_001",
            transaction_ids=[1, 2, 3],
            adjustment_category=AdjustmentCategory.ONE_TIME_EXPENSE,
            suggested_amount=5000.0,
            add_back=True,
            confidence_score=0.85,
            confidence_level=SuggestionConfidence.HIGH,
            reasoning="One-time legal settlement expense",
        )
        assert suggestion.suggestion_id == "sug_001"
        assert suggestion.add_back is True
        assert suggestion.confidence_score == 0.85

    def test_adjustment_suggestion_to_dict(self):
        """Test converting suggestion to dictionary"""
        suggestion = AdjustmentSuggestion(
            suggestion_id="sug_002",
            transaction_ids=[1],
            adjustment_category=AdjustmentCategory.DISCRETIONARY_EXPENSE,
            suggested_amount=1000.0,
            add_back=False,
            confidence_score=0.6,
            confidence_level=SuggestionConfidence.MEDIUM,
            reasoning="Test reasoning",
        )
        suggestion_dict = suggestion.to_dict()
        assert suggestion_dict["suggestion_id"] == "sug_002"
        assert suggestion_dict["confidence_level"] == "medium"

    def test_adjustment_suggestion_from_dict(self):
        """Test creating suggestion from dictionary"""
        data = {
            "suggestion_id": "sug_003",
            "transaction_ids": [1, 2],
            "adjustment_category": "One-Time Expense",
            "suggested_amount": 2000.0,
            "add_back": True,
            "confidence_score": 0.75,
            "confidence_level": "medium",
            "reasoning": "Test reasoning",
            "supporting_evidence": [],
            "alternative_categories": [],
            "suggested_reasoning_template": "",
            "metadata": {},
            "created_at": datetime.now().isoformat(),
        }
        suggestion = AdjustmentSuggestion.from_dict(data)
        assert suggestion.suggestion_id == "sug_003"
        assert suggestion.adjustment_category == AdjustmentCategory.ONE_TIME_EXPENSE

    def test_suggestion_batch_creation(self):
        """Test creating a SuggestionBatch"""
        suggestions = [
            AdjustmentSuggestion(
                suggestion_id="s1",
                transaction_ids=[1],
                adjustment_category=AdjustmentCategory.ONE_TIME_EXPENSE,
                suggested_amount=1000.0,
                add_back=True,
                confidence_score=0.9,
                confidence_level=SuggestionConfidence.HIGH,
                reasoning="High confidence",
            ),
            AdjustmentSuggestion(
                suggestion_id="s2",
                transaction_ids=[2],
                adjustment_category=AdjustmentCategory.DISCRETIONARY_EXPENSE,
                suggested_amount=500.0,
                add_back=False,
                confidence_score=0.6,
                confidence_level=SuggestionConfidence.MEDIUM,
                reasoning="Medium confidence",
            ),
        ]
        batch = SuggestionBatch(
            suggestions=suggestions,
            total_suggested_adjustment=1500.0,
            high_confidence_count=1,
            medium_confidence_count=1,
            low_confidence_count=0,
        )
        assert len(batch.suggestions) == 2
        assert batch.high_confidence_count == 1

    def test_adjustment_suggestion_engine_initialization(self):
        """Test initializing AdjustmentSuggestionEngine"""
        engine = AdjustmentSuggestionEngine(
            min_confidence_threshold=0.6,
            max_suggestions_per_category=10,
            include_low_confidence=False,
        )
        assert engine.min_confidence_threshold == 0.6
        assert engine.max_suggestions_per_category == 10

    def test_generate_suggestions_interface(self):
        """Test that generate_suggestions method exists and returns SuggestionBatch"""
        engine = AdjustmentSuggestionEngine()
        df = pd.DataFrame(
            {
                "row_id": [1, 2],
                "account_name_flat": ["Expense A", "Expense B"],
                "description": ["Desc 1", "Desc 2"],
                "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                "amount_net": [100.0, 200.0],
            }
        )
        result = engine.generate_suggestions(df)
        assert isinstance(result, SuggestionBatch)
        # Should return empty suggestions for now (scaffolding)
        assert len(result.suggestions) == 0


@pytest.mark.unit
class TestAIModuleImports:
    """Test that AI module can be imported correctly"""

    def test_ai_module_imports(self):
        """Test importing from app.ai"""
        from app.ai import (
            TransactionClusterer,
            AdjustmentSuggestionEngine,
            TransactionCluster,
            AdjustmentSuggestion,
        )
        assert TransactionClusterer is not None
        assert AdjustmentSuggestionEngine is not None

