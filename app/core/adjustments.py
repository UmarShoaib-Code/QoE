"""
Adjustment Rules Engine

Applies configurable rules to GL transactions to identify and calculate adjustments.
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json


@dataclass
class AdjustmentRule:
    """Adjustment rule definition"""

    rule_name: str
    enabled: bool = True
    match_type: str = "keyword"  # keyword, account, regex, threshold
    match_value: Union[str, float] = ""
    adjustment_category: str = ""
    add_back: bool = False  # True = add back to EBITDA, False = subtract
    reasoning_template: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            "rule_name": self.rule_name,
            "enabled": self.enabled,
            "match_type": self.match_type,
            "match_value": self.match_value,
            "adjustment_category": self.adjustment_category,
            "add_back": self.add_back,
            "reasoning_template": self.reasoning_template,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdjustmentRule":
        """Create rule from dictionary"""
        return cls(
            rule_name=data.get("rule_name", ""),
            enabled=data.get("enabled", True),
            match_type=data.get("match_type", "keyword"),
            match_value=data.get("match_value", ""),
            adjustment_category=data.get("adjustment_category", ""),
            add_back=data.get("add_back", False),
            reasoning_template=data.get("reasoning_template", ""),
        )


class AdjustmentRulesEngine:
    """Engine for applying adjustment rules to GL transactions"""

    def __init__(self, rules: Optional[List[AdjustmentRule]] = None):
        """
        Initialize rules engine.

        Args:
            rules: List of AdjustmentRule objects (can be loaded from config later)
        """
        self.rules = rules or []

    def load_rules_from_yaml(self, config_path: str | Path) -> None:
        """
        Load rules from YAML configuration file.

        Args:
            config_path: Path to YAML config file
        """
        config_path = Path(config_path)
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.rules = []
        if "rules" in config:
            for rule_data in config["rules"]:
                self.rules.append(AdjustmentRule.from_dict(rule_data))

    def load_rules_from_json(self, config_path: str | Path) -> None:
        """
        Load rules from JSON configuration file.

        Args:
            config_path: Path to JSON config file
        """
        config_path = Path(config_path)
        with open(config_path, "r") as f:
            config = json.load(f)

        self.rules = []
        if "rules" in config:
            for rule_data in config["rules"]:
                self.rules.append(AdjustmentRule.from_dict(rule_data))

    def apply_rules(
        self, normalized_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Apply adjustment rules to normalized GL DataFrame.

        Args:
            normalized_df: Normalized GL DataFrame

        Returns:
            Tuple of (adjusted_df, adjustment_log_df)
            - adjusted_df: DataFrame with adjustment columns added
            - adjustment_log_df: DataFrame with adjustment details for each match
        """
        if normalized_df.empty:
            return normalized_df.copy(), pd.DataFrame()

        df = normalized_df.copy()

        # Initialize adjustment columns
        df["adjustment_flag"] = False
        df["adjustment_category"] = ""
        df["reasoning"] = ""
        df["adjustment_amount"] = 0.0

        # Track adjustments for log
        adjustment_log = []

        # Apply each enabled rule
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Find matching rows
            matches = self._find_matches(df, rule)

            if len(matches) > 0:
                # Apply rule to matching rows
                for idx in matches:
                    # Set adjustment flag
                    df.at[idx, "adjustment_flag"] = True
                    df.at[idx, "adjustment_category"] = rule.adjustment_category

                    # Generate reasoning
                    reasoning = self._generate_reasoning(df.loc[idx], rule)
                    df.at[idx, "reasoning"] = reasoning

                    # Calculate adjustment amount
                    adjustment_amount = self._calculate_adjustment_amount(
                        df.loc[idx], rule
                    )
                    df.at[idx, "adjustment_amount"] = adjustment_amount

                    # Log adjustment
                    adjustment_log.append(
                        {
                            "row_id": df.at[idx, "row_id"],
                            "date": df.at[idx, "date"],
                            "entity": df.at[idx, "entity"] if "entity" in df.columns else "",
                            "account_name_flat": df.at[idx, "account_name_flat"],
                            "description": df.at[idx, "description"],
                            "rule_name": rule.rule_name,
                            "adjustment_category": rule.adjustment_category,
                            "adjustment_amount": adjustment_amount,
                            "add_back": rule.add_back,
                            "reasoning": reasoning,
                        }
                    )

        # Create adjustment log DataFrame
        adjustment_log_df = pd.DataFrame(adjustment_log)

        return df, adjustment_log_df

    def _find_matches(self, df: pd.DataFrame, rule: AdjustmentRule) -> List[int]:
        """
        Find rows matching the rule criteria.

        Args:
            df: DataFrame to search
            rule: AdjustmentRule to apply

        Returns:
            List of row indices that match
        """
        matches = []

        if rule.match_type == "keyword":
            # Match against account name or description
            keyword = str(rule.match_value).lower()
            mask = (
                df["account_name_flat"].str.lower().str.contains(keyword, na=False)
                | df["description"].str.lower().str.contains(keyword, na=False)
            )
            matches = df[mask].index.tolist()

        elif rule.match_type == "account":
            # Exact match on account name
            account_match = df["account_name_flat"] == rule.match_value
            matches = df[account_match].index.tolist()

        elif rule.match_type == "regex":
            # Regex match on account name or description
            pattern = str(rule.match_value)
            try:
                mask = (
                    df["account_name_flat"].str.contains(pattern, regex=True, na=False)
                    | df["description"].str.contains(pattern, regex=True, na=False)
                )
                matches = df[mask].index.tolist()
            except re.error:
                # Invalid regex pattern
                pass

        elif rule.match_type == "threshold":
            # Match based on amount threshold
            threshold = float(rule.match_value)
            # Check if amount exceeds threshold (absolute value)
            mask = df["amount_net"].abs() >= threshold
            matches = df[mask].index.tolist()

        return matches

    def _generate_reasoning(
        self, row: pd.Series, rule: AdjustmentRule
    ) -> str:
        """
        Generate reasoning text for adjustment.

        Args:
            row: DataFrame row
            rule: AdjustmentRule applied

        Returns:
            Reasoning string
        """
        if rule.reasoning_template:
            # Replace template variables
            reasoning = rule.reasoning_template
            reasoning = reasoning.replace("{rule_name}", rule.rule_name)
            reasoning = reasoning.replace("{account}", str(row.get("account_name_flat", "")))
            reasoning = reasoning.replace("{description}", str(row.get("description", "")))
            reasoning = reasoning.replace("{amount}", f"${row.get('amount_net', 0):,.2f}")
            reasoning = reasoning.replace("{category}", rule.adjustment_category)
            return reasoning
        else:
            # Default reasoning
            return f"{rule.rule_name}: {rule.adjustment_category} adjustment"

    def _calculate_adjustment_amount(
        self, row: pd.Series, rule: AdjustmentRule
    ) -> float:
        """
        Calculate adjustment amount for a transaction.

        Args:
            row: DataFrame row
            rule: AdjustmentRule applied

        Returns:
            Adjustment amount (positive for add-back, negative for subtract)
        """
        # Base amount is the transaction amount_net
        base_amount = float(row.get("amount_net", 0))

        # If add_back, reverse the sign (add back to EBITDA)
        # If subtract, keep original sign (subtract from EBITDA)
        if rule.add_back:
            # Add back means reversing the sign
            adjustment = -base_amount
        else:
            # Subtract means keeping original sign
            adjustment = base_amount

        return adjustment

    def get_rules_summary(self) -> pd.DataFrame:
        """
        Get summary of all rules.

        Returns:
            DataFrame with rule information
        """
        rules_data = [rule.to_dict() for rule in self.rules]
        return pd.DataFrame(rules_data)

    def add_rule(self, rule: AdjustmentRule) -> None:
        """Add a rule to the engine"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove a rule by name.

        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.rules):
            if rule.rule_name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def enable_rule(self, rule_name: str) -> bool:
        """Enable a rule by name"""
        for rule in self.rules:
            if rule.rule_name == rule_name:
                rule.enabled = True
                return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Disable a rule by name"""
        for rule in self.rules:
            if rule.rule_name == rule_name:
                rule.enabled = False
                return True
        return False

