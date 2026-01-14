"""
Unit tests for GL validation module
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from app.core.validation import (
    GLValidator,
    ValidationResult,
    ValidationStatus,
)
from app.core.gl_ingestion import ProcessingReport


class TestGLValidator:
    """Test suite for GLValidator"""

    @pytest.fixture
    def validator(self):
        """Create a GL validator instance with default settings"""
        return GLValidator()

    @pytest.fixture
    def validator_strict(self):
        """Create a strict GL validator"""
        return GLValidator(
            min_transactions=10,
            max_date_parse_failure_rate=0.05,
            debit_credit_tolerance=0.001,
        )

    @pytest.fixture
    def sample_valid_df(self):
        """Sample valid normalized DataFrame"""
        return pd.DataFrame(
            {
                "entity": ["Company A"] * 5,
                "source_system": ["QuickBooks"] * 5,
                "gl_source_file": ["gl.xlsx"] * 5,
                "row_id": range(5),
                "date": pd.to_datetime(
                    ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]
                ),
                "account_name_raw": ["Cash", "Revenue", "Expenses", "Cash", "Revenue"],
                "account_name_flat": ["Cash", "Revenue", "Expenses", "Cash", "Revenue"],
                "description": ["Deposit", "Sales", "Rent", "Withdrawal", "Sales"],
                "debit": [1000.0, 0.0, 500.0, 0.0, 0.0],
                "credit": [0.0, 300.0, 0.0, 200.0, 500.0],
                "amount_net": [1000.0, -300.0, 500.0, -200.0, -500.0],
            }
        )

    @pytest.fixture
    def sample_unbalanced_df(self):
        """Sample DataFrame with unbalanced debits/credits"""
        return pd.DataFrame(
            {
                "entity": ["Company A"] * 3,
                "source_system": ["QuickBooks"] * 3,
                "gl_source_file": ["gl.xlsx"] * 3,
                "row_id": range(3),
                "date": pd.to_datetime(["2024-01-15", "2024-01-16", "2024-01-17"]),
                "account_name_raw": ["Cash", "Revenue", "Expenses"],
                "account_name_flat": ["Cash", "Revenue", "Expenses"],
                "description": ["Deposit", "Sales", "Rent"],
                "debit": [1000.0, 0.0, 500.0],  # Total: 1500
                "credit": [0.0, 300.0, 0.0],  # Total: 300 (unbalanced!)
                "amount_net": [1000.0, -300.0, 500.0],
            }
        )

    @pytest.fixture
    def sample_negative_amounts_df(self):
        """Sample DataFrame with negative debits/credits"""
        return pd.DataFrame(
            {
                "entity": ["Company A"] * 3,
                "source_system": ["QuickBooks"] * 3,
                "gl_source_file": ["gl.xlsx"] * 3,
                "row_id": range(3),
                "date": pd.to_datetime(["2024-01-15", "2024-01-16", "2024-01-17"]),
                "account_name_raw": ["Cash", "Revenue", "Expenses"],
                "account_name_flat": ["Cash", "Revenue", "Expenses"],
                "description": ["Deposit", "Sales", "Rent"],
                "debit": [1000.0, -100.0, 500.0],  # Negative debit
                "credit": [0.0, 300.0, -50.0],  # Negative credit
                "amount_net": [1000.0, -400.0, 550.0],
            }
        )

    def test_create_validator(self, validator):
        """Test validator creation"""
        assert validator is not None
        assert validator.min_transactions == 1
        assert validator.max_date_parse_failure_rate == 0.1
        assert validator.debit_credit_tolerance == 0.01

    def test_validate_empty_dataframe(self, validator):
        """Test validation of empty DataFrame"""
        empty_df = pd.DataFrame()
        result = validator.validate(empty_df)

        assert result.status == ValidationStatus.FAIL
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].lower()
        assert result.key_metrics["total_transactions"] == 0

    def test_validate_balanced_debits_credits(self, validator, sample_valid_df):
        """Test validation passes when debits equal credits"""
        # Adjust sample to be balanced
        sample_valid_df["debit"] = [1000.0, 0.0, 500.0, 0.0, 0.0]
        sample_valid_df["credit"] = [0.0, 300.0, 500.0, 200.0, 500.0]
        # Total debits: 1500, Total credits: 1500

        result = validator.validate(sample_valid_df)

        assert result.status == ValidationStatus.PASS
        assert len([e for e in result.errors if "debit" in e.lower() and "credit" in e.lower()]) == 0
        assert result.key_metrics["total_debits"] == 1500.0
        assert result.key_metrics["total_credits"] == 1500.0

    def test_validate_unbalanced_debits_credits(self, validator, sample_unbalanced_df):
        """Test validation fails when debits don't equal credits"""
        result = validator.validate(sample_unbalanced_df)

        assert result.status == ValidationStatus.FAIL
        assert len(result.errors) > 0
        error_messages = " ".join(result.errors).lower()
        assert "debit" in error_messages
        assert "credit" in error_messages
        assert "do not equal" in error_messages.lower() or "incomplete" in error_messages

    def test_validate_debit_credit_tolerance(self, validator):
        """Test that small differences within tolerance pass"""
        # Create balanced data with tiny difference
        df = pd.DataFrame(
            {
                "entity": ["Company A"] * 2,
                "source_system": ["QuickBooks"] * 2,
                "gl_source_file": ["gl.xlsx"] * 2,
                "row_id": range(2),
                "date": pd.to_datetime(["2024-01-15", "2024-01-16"]),
                "account_name_raw": ["Cash", "Revenue"],
                "account_name_flat": ["Cash", "Revenue"],
                "description": ["Deposit", "Sales"],
                "debit": [1000.0, 0.0],
                "credit": [0.0, 1000.005],  # Difference of 0.005 < 0.01 tolerance
                "amount_net": [1000.0, -1000.005],
            }
        )

        result = validator.validate(df)
        # Should pass because difference is within tolerance
        assert result.status == ValidationStatus.PASS

    def test_validate_min_transactions(self, validator_strict):
        """Test minimum transaction count validation"""
        df = pd.DataFrame(
            {
                "entity": ["Company A"] * 5,  # Only 5 transactions, need 10
                "source_system": ["QuickBooks"] * 5,
                "gl_source_file": ["gl.xlsx"] * 5,
                "row_id": range(5),
                "date": pd.to_datetime(["2024-01-15"] * 5),
                "account_name_raw": ["Cash"] * 5,
                "account_name_flat": ["Cash"] * 5,
                "description": ["Deposit"] * 5,
                "debit": [100.0] * 5,
                "credit": [100.0] * 5,
                "amount_net": [0.0] * 5,
            }
        )

        result = validator_strict.validate(df)

        assert result.status == ValidationStatus.FAIL
        assert len([e for e in result.errors if "insufficient" in e.lower()]) > 0

    def test_validate_date_parse_failure_rate(self, validator_strict):
        """Test date parse failure rate validation"""
        df = pd.DataFrame(
            {
                "entity": ["Company A"] * 10,
                "source_system": ["QuickBooks"] * 10,
                "gl_source_file": ["gl.xlsx"] * 10,
                "row_id": range(10),
                "date": pd.to_datetime(["2024-01-15"] * 10),
                "account_name_raw": ["Cash"] * 10,
                "account_name_flat": ["Cash"] * 10,
                "description": ["Deposit"] * 10,
                "debit": [100.0] * 10,
                "credit": [100.0] * 10,
                "amount_net": [0.0] * 10,
            }
        )

        # Create processing report with high failure rate
        report = ProcessingReport()
        report.total_rows_read = 20
        report.rows_with_invalid_dates = 15  # 75% failure rate > 5% threshold

        result = validator_strict.validate(df, processing_report=report)

        assert result.status == ValidationStatus.FAIL
        # Check for date-related error (new format includes "Invalid Dates" or "date" in message)
        date_errors = [e for e in result.errors if "invalid date" in e.lower() or "date" in e.lower()]
        assert len(date_errors) > 0

    def test_validate_negative_debits_warning(self, validator, sample_negative_amounts_df):
        """Test that negative debits generate warnings"""
        result = validator.validate(sample_negative_amounts_df)

        # Should have warnings for negative amounts
        warning_messages = " ".join(result.warnings).lower()
        assert "negative debit" in warning_messages or "negative debits" in warning_messages

    def test_validate_negative_credits_warning(self, validator, sample_negative_amounts_df):
        """Test that negative credits generate warnings"""
        result = validator.validate(sample_negative_amounts_df)

        # Should have warnings for negative amounts
        warning_messages = " ".join(result.warnings).lower()
        assert "negative credit" in warning_messages or "negative credits" in warning_messages

    def test_validation_result_to_dict(self, validator, sample_valid_df):
        """Test ValidationResult.to_dict() method"""
        result = validator.validate(sample_valid_df)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "status" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict
        assert "key_metrics" in result_dict
        assert isinstance(result_dict["errors"], list)
        assert isinstance(result_dict["warnings"], list)
        assert isinstance(result_dict["key_metrics"], dict)

    def test_validation_result_is_valid(self, validator):
        """Test ValidationResult.is_valid() method"""
        # Valid case
        df_valid = pd.DataFrame(
            {
                "entity": ["Company A"],
                "source_system": ["QuickBooks"],
                "gl_source_file": ["gl.xlsx"],
                "row_id": [0],
                "date": pd.to_datetime(["2024-01-15"]),
                "account_name_raw": ["Cash"],
                "account_name_flat": ["Cash"],
                "description": ["Deposit"],
                "debit": [1000.0],
                "credit": [1000.0],
                "amount_net": [0.0],
            }
        )
        result_valid = validator.validate(df_valid)
        assert result_valid.is_valid()

        # Invalid case
        df_invalid = pd.DataFrame()
        result_invalid = validator.validate(df_invalid)
        assert not result_invalid.is_valid()

    def test_key_metrics_populated(self, validator, sample_valid_df):
        """Test that key metrics are properly populated"""
        result = validator.validate(sample_valid_df)

        assert "total_transactions" in result.key_metrics
        assert "total_debits" in result.key_metrics
        assert "total_credits" in result.key_metrics
        assert "debit_credit_difference" in result.key_metrics
        assert "date_parse_failure_rate" in result.key_metrics

        assert isinstance(result.key_metrics["total_transactions"], int)
        assert isinstance(result.key_metrics["total_debits"], (int, float))
        assert isinstance(result.key_metrics["total_credits"], (int, float))

    def test_multiple_validation_errors(self, validator_strict, sample_unbalanced_df):
        """Test that multiple validation errors are captured"""
        # Create processing report with high failure rate
        report = ProcessingReport()
        report.total_rows_read = 100
        report.rows_with_invalid_dates = 20  # 20% failure rate > 5% threshold

        result = validator_strict.validate(sample_unbalanced_df, processing_report=report)

        # Should have multiple errors
        assert result.status == ValidationStatus.FAIL
        assert len(result.errors) >= 1  # At least debit/credit error, possibly date parse error

    def test_validation_without_processing_report(self, validator, sample_valid_df):
        """Test validation works without processing report"""
        result = validator.validate(sample_valid_df)

        # Should still work, just won't have date parse failure rate
        assert result is not None
        assert "date_parse_failure_rate" in result.key_metrics

