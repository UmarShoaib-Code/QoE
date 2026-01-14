"""
Unit tests for adjustment rules engine
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from app.core.adjustments import (
    AdjustmentRulesEngine,
    AdjustmentRule,
)


class TestAdjustmentRule:
    """Test suite for AdjustmentRule"""

    def test_create_rule(self):
        """Test rule creation"""
        rule = AdjustmentRule(
            rule_name="Test Rule",
            enabled=True,
            match_type="keyword",
            match_value="test",
            adjustment_category="Test Category",
            add_back=True,
            reasoning_template="Test: {description}",
        )

        assert rule.rule_name == "Test Rule"
        assert rule.enabled is True
        assert rule.match_type == "keyword"
        assert rule.add_back is True

    def test_rule_to_dict(self):
        """Test rule to dictionary conversion"""
        rule = AdjustmentRule(
            rule_name="Test Rule",
            match_type="keyword",
            match_value="test",
        )
        rule_dict = rule.to_dict()

        assert isinstance(rule_dict, dict)
        assert rule_dict["rule_name"] == "Test Rule"
        assert rule_dict["match_type"] == "keyword"

    def test_rule_from_dict(self):
        """Test rule creation from dictionary"""
        rule_data = {
            "rule_name": "Test Rule",
            "enabled": True,
            "match_type": "account",
            "match_value": "Cash",
            "adjustment_category": "Test",
            "add_back": False,
            "reasoning_template": "Test template",
        }

        rule = AdjustmentRule.from_dict(rule_data)

        assert rule.rule_name == "Test Rule"
        assert rule.match_type == "account"
        assert rule.match_value == "Cash"


class TestAdjustmentRulesEngine:
    """Test suite for AdjustmentRulesEngine"""

    @pytest.fixture
    def engine(self):
        """Create engine instance"""
        return AdjustmentRulesEngine()

    @pytest.fixture
    def sample_normalized_df(self):
        """Sample normalized DataFrame"""
        return pd.DataFrame(
            {
                "entity": ["Company A"] * 5,
                "source_system": ["QuickBooks"] * 5,
                "gl_source_file": ["gl.xlsx"] * 5,
                "row_id": range(5),
                "date": pd.to_datetime(["2024-01-15"] * 5),
                "account_name_raw": ["Cash", "Legal Expense", "Revenue", "Depreciation", "Cash"],
                "account_name_flat": ["Cash", "Legal Expense", "Revenue", "Depreciation Expense", "Cash"],
                "description": [
                    "Deposit",
                    "Legal settlement payment",
                    "Sales revenue",
                    "Monthly depreciation",
                    "Withdrawal",
                ],
                "debit": [1000.0, 50000.0, 0.0, 10000.0, 0.0],
                "credit": [0.0, 0.0, 30000.0, 0.0, 500.0],
                "amount_net": [1000.0, 50000.0, -30000.0, 10000.0, -500.0],
            }
        )

    def test_create_engine(self, engine):
        """Test engine creation"""
        assert engine is not None
        assert isinstance(engine, AdjustmentRulesEngine)
        assert len(engine.rules) == 0

    def test_add_rule(self, engine):
        """Test adding a rule"""
        rule = AdjustmentRule(rule_name="Test Rule", match_type="keyword", match_value="test")
        engine.add_rule(rule)

        assert len(engine.rules) == 1
        assert engine.rules[0].rule_name == "Test Rule"

    def test_apply_rules_keyword_match(self, engine, sample_normalized_df):
        """Test applying keyword-based rule"""
        rule = AdjustmentRule(
            rule_name="Legal Expenses",
            enabled=True,
            match_type="keyword",
            match_value="legal",
            adjustment_category="One-Time Expenses",
            add_back=True,
            reasoning_template="Legal expense: {description}",
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # Should find legal expense row
        legal_rows = adjusted_df[adjusted_df["adjustment_flag"] == True]
        assert len(legal_rows) > 0
        assert "legal" in legal_rows.iloc[0]["description"].lower()

    def test_apply_rules_account_match(self, engine, sample_normalized_df):
        """Test applying account-based rule"""
        rule = AdjustmentRule(
            rule_name="Depreciation",
            enabled=True,
            match_type="account",
            match_value="Depreciation Expense",
            adjustment_category="D&A",
            add_back=True,
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # Should find depreciation row
        dep_rows = adjusted_df[
            (adjusted_df["adjustment_flag"] == True)
            & (adjusted_df["account_name_flat"] == "Depreciation Expense")
        ]
        assert len(dep_rows) > 0

    def test_apply_rules_regex_match(self, engine, sample_normalized_df):
        """Test applying regex-based rule"""
        rule = AdjustmentRule(
            rule_name="Legal Pattern",
            enabled=True,
            match_type="regex",
            match_value="(?i)(legal|settlement)",
            adjustment_category="Legal",
            add_back=True,
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # Should find legal settlement row
        matches = adjusted_df[adjusted_df["adjustment_flag"] == True]
        assert len(matches) > 0

    def test_apply_rules_threshold_match(self, engine, sample_normalized_df):
        """Test applying threshold-based rule"""
        rule = AdjustmentRule(
            rule_name="Large Items",
            enabled=True,
            match_type="threshold",
            match_value=20000.0,
            adjustment_category="Large Items",
            add_back=True,
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # Should find items with amount >= 20000
        matches = adjusted_df[adjusted_df["adjustment_flag"] == True]
        assert len(matches) > 0
        assert all(matches["amount_net"].abs() >= 20000.0)

    def test_apply_rules_disabled(self, engine, sample_normalized_df):
        """Test that disabled rules are not applied"""
        rule = AdjustmentRule(
            rule_name="Test Rule",
            enabled=False,  # Disabled
            match_type="keyword",
            match_value="legal",
            adjustment_category="Test",
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # Should not find any matches
        matches = adjusted_df[adjusted_df["adjustment_flag"] == True]
        assert len(matches) == 0

    def test_adjustment_amount_calculation_add_back(self, engine, sample_normalized_df):
        """Test adjustment amount calculation for add-back"""
        rule = AdjustmentRule(
            rule_name="Test",
            enabled=True,
            match_type="keyword",
            match_value="legal",
            adjustment_category="Test",
            add_back=True,  # Add back
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        # For add_back=True, adjustment should reverse the sign
        matches = adjusted_df[adjusted_df["adjustment_flag"] == True]
        if len(matches) > 0:
            row = matches.iloc[0]
            # If amount_net is positive, adjustment should be negative (add back)
            if row["amount_net"] > 0:
                assert row["adjustment_amount"] < 0

    def test_adjustment_log_creation(self, engine, sample_normalized_df):
        """Test that adjustment log is created"""
        rule = AdjustmentRule(
            rule_name="Test Rule",
            enabled=True,
            match_type="keyword",
            match_value="legal",
            adjustment_category="Test",
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        assert isinstance(log_df, pd.DataFrame)
        if not log_df.empty:
            assert "rule_name" in log_df.columns
            assert "adjustment_amount" in log_df.columns
            assert "reasoning" in log_df.columns

    def test_reasoning_template_substitution(self, engine, sample_normalized_df):
        """Test reasoning template variable substitution"""
        rule = AdjustmentRule(
            rule_name="Test Rule",
            enabled=True,
            match_type="keyword",
            match_value="legal",
            adjustment_category="Test",
            reasoning_template="Found {rule_name} in {account}: {description} (${amount})",
        )

        engine.add_rule(rule)
        adjusted_df, log_df = engine.apply_rules(sample_normalized_df)

        matches = adjusted_df[adjusted_df["adjustment_flag"] == True]
        if len(matches) > 0:
            reasoning = matches.iloc[0]["reasoning"]
            assert "Test Rule" in reasoning
            assert "legal" in reasoning.lower()

    def test_load_rules_from_yaml(self, engine):
        """Test loading rules from YAML file"""
        # Create temporary YAML file
        yaml_content = """
rules:
  - rule_name: "Test Rule"
    enabled: true
    match_type: "keyword"
    match_value: "test"
    adjustment_category: "Test"
    add_back: true
    reasoning_template: "Test template"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            tmp_path = f.name

        try:
            engine.load_rules_from_yaml(tmp_path)
            assert len(engine.rules) == 1
            assert engine.rules[0].rule_name == "Test Rule"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_rules_from_json(self, engine):
        """Test loading rules from JSON file"""
        json_content = """
{
  "rules": [
    {
      "rule_name": "Test Rule",
      "enabled": true,
      "match_type": "keyword",
      "match_value": "test",
      "adjustment_category": "Test",
      "add_back": false,
      "reasoning_template": "Test template"
    }
  ]
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            tmp_path = f.name

        try:
            engine.load_rules_from_json(tmp_path)
            assert len(engine.rules) == 1
            assert engine.rules[0].rule_name == "Test Rule"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_enable_disable_rule(self, engine):
        """Test enabling and disabling rules"""
        rule = AdjustmentRule(rule_name="Test Rule", enabled=True)
        engine.add_rule(rule)

        engine.disable_rule("Test Rule")
        assert engine.rules[0].enabled is False

        engine.enable_rule("Test Rule")
        assert engine.rules[0].enabled is True

    def test_remove_rule(self, engine):
        """Test removing a rule"""
        rule1 = AdjustmentRule(rule_name="Rule 1")
        rule2 = AdjustmentRule(rule_name="Rule 2")
        engine.add_rule(rule1)
        engine.add_rule(rule2)

        assert len(engine.rules) == 2

        result = engine.remove_rule("Rule 1")
        assert result is True
        assert len(engine.rules) == 1
        assert engine.rules[0].rule_name == "Rule 2"

    def test_get_rules_summary(self, engine):
        """Test getting rules summary"""
        rule = AdjustmentRule(rule_name="Test Rule", match_type="keyword")
        engine.add_rule(rule)

        summary = engine.get_rules_summary()
        assert isinstance(summary, pd.DataFrame)
        assert len(summary) == 1
        assert summary.iloc[0]["rule_name"] == "Test Rule"

