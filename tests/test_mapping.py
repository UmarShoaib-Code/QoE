"""
Unit tests for GL account mapping module
"""

import pytest
import pandas as pd
from datetime import datetime

from app.core.mapping import (
    GLAccountMapper,
    MultiEntityProcessor,
    AccountMapping,
    DEFAULT_CATEGORIES,
)
from app.core.validation import ValidationResult, ValidationStatus
from app.core.gl_ingestion import ProcessingReport


class TestGLAccountMapper:
    """Test suite for GLAccountMapper"""

    @pytest.fixture
    def mapper(self):
        """Create mapper instance"""
        return GLAccountMapper()

    @pytest.fixture
    def sample_normalized_df(self):
        """Sample normalized DataFrame"""
        return pd.DataFrame(
            {
                "entity": ["Company A", "Company A", "Company B", "Company B"],
                "source_system": ["QuickBooks"] * 4,
                "gl_source_file": ["gl.xlsx"] * 4,
                "row_id": range(4),
                "date": pd.to_datetime(["2024-01-15"] * 4),
                "account_name_raw": ["Cash", "Revenue", "Cash", "Expenses"],
                "account_name_flat": ["Cash", "Revenue", "Cash", "Expenses"],
                "description": ["Deposit", "Sales", "Withdrawal", "Rent"],
                "debit": [1000.0, 0.0, 500.0, 200.0],
                "credit": [0.0, 300.0, 0.0, 0.0],
                "amount_net": [1000.0, -300.0, 500.0, 200.0],
            }
        )

    def test_create_mapper(self, mapper):
        """Test mapper creation"""
        assert mapper is not None
        assert isinstance(mapper, GLAccountMapper)

    def test_extract_unique_accounts(self, mapper, sample_normalized_df):
        """Test unique account extraction"""
        unique_accounts = mapper.extract_unique_accounts(sample_normalized_df)

        assert not unique_accounts.empty
        assert "account_name_flat" in unique_accounts.columns
        assert "entity" in unique_accounts.columns
        assert "transaction_count" in unique_accounts.columns

        # Should have unique accounts per entity
        assert len(unique_accounts) > 0

    def test_extract_unique_accounts_filtered_by_entity(
        self, mapper, sample_normalized_df
    ):
        """Test unique account extraction filtered by entity"""
        unique_accounts = mapper.extract_unique_accounts(
            sample_normalized_df, entity="Company A"
        )

        assert not unique_accounts.empty
        assert all(unique_accounts["entity"] == "Company A")

    def test_create_mapping_template(self, mapper, sample_normalized_df):
        """Test mapping template creation"""
        unique_accounts = mapper.extract_unique_accounts(sample_normalized_df)
        mapping_template = mapper.create_mapping_template(unique_accounts)

        assert not mapping_template.empty
        assert "account_name_flat" in mapping_template.columns
        assert "main_category" in mapping_template.columns
        assert "sub1" in mapping_template.columns
        assert "sub2" in mapping_template.columns
        assert "client_specific" in mapping_template.columns
        assert "notes" in mapping_template.columns

    def test_create_mapping_template_with_existing(
        self, mapper, sample_normalized_df
    ):
        """Test mapping template creation with existing mapping"""
        unique_accounts = mapper.extract_unique_accounts(sample_normalized_df)

        # Create existing mapping
        existing_mapping = pd.DataFrame(
            {
                "account_name_flat": ["Cash"],
                "main_category": ["Balance Sheet"],
                "sub1": ["Current Assets"],
                "sub2": [""],
                "client_specific": [""],
                "notes": ["Cash account"],
            }
        )

        mapping_template = mapper.create_mapping_template(
            unique_accounts, existing_mapping
        )

        # Check that existing mapping was merged
        cash_row = mapping_template[
            mapping_template["account_name_flat"] == "Cash"
        ]
        if not cash_row.empty:
            assert cash_row.iloc[0]["main_category"] == "Balance Sheet"

    def test_apply_mapping(self, mapper, sample_normalized_df):
        """Test applying mapping to normalized DataFrame"""
        # Create mapping
        mapping_df = pd.DataFrame(
            {
                "account_name_flat": ["Cash", "Revenue", "Expenses"],
                "main_category": ["Balance Sheet", "Revenue", "OpEx"],
                "sub1": ["Current Assets", "Sales", "Operating"],
                "sub2": ["", "", ""],
                "client_specific": ["", "", ""],
                "notes": ["", "", ""],
            }
        )

        result_df = mapper.apply_mapping(sample_normalized_df, mapping_df)

        assert "main_category" in result_df.columns
        assert "sub1" in result_df.columns
        assert len(result_df) == len(sample_normalized_df)

        # Check that mapping was applied
        cash_rows = result_df[result_df["account_name_flat"] == "Cash"]
        if not cash_rows.empty:
            assert cash_rows.iloc[0]["main_category"] == "Balance Sheet"

    def test_apply_mapping_multi_entity(self, mapper):
        """Test applying mapping with multiple entities"""
        df = pd.DataFrame(
            {
                "entity": ["Entity A", "Entity B"],
                "account_name_flat": ["Cash", "Cash"],
                "account_name_raw": ["Cash", "Cash"],
                "date": pd.to_datetime(["2024-01-15"] * 2),
                "debit": [1000.0, 500.0],
                "credit": [0.0, 0.0],
            }
        )

        mapping_df = pd.DataFrame(
            {
                "entity": ["Entity A", "Entity B"],
                "account_name_flat": ["Cash", "Cash"],
                "main_category": ["Balance Sheet", "Balance Sheet"],
                "sub1": ["", ""],
                "sub2": ["", ""],
                "client_specific": ["", ""],
                "notes": ["", ""],
            }
        )

        result_df = mapper.apply_mapping(df, mapping_df)

        assert "main_category" in result_df.columns
        assert len(result_df) == 2

    def test_suggest_category(self, mapper):
        """Test category suggestion"""
        # Test revenue pattern
        suggestion = mapper.suggest_category("Sales Revenue")
        assert suggestion == "Revenue"

        # Test expense pattern
        suggestion = mapper.suggest_category("Operating Expenses")
        assert suggestion == "OpEx"

        # Test COGS pattern
        suggestion = mapper.suggest_category("Cost of Goods Sold")
        assert suggestion == "COGS"

    def test_suggest_category_with_mapping(self, mapper):
        """Test category suggestion with existing mapping"""
        mapping_df = pd.DataFrame(
            {
                "account_name_flat": ["Sales Revenue", "Product Sales"],
                "main_category": ["Revenue", "Revenue"],
                "sub1": ["", ""],
                "sub2": ["", ""],
                "client_specific": ["", ""],
                "notes": ["", ""],
            }
        )

        # Should suggest Revenue based on similar accounts
        suggestion = mapper.suggest_category("Service Sales", mapping_df)
        assert suggestion == "Revenue"

    def test_get_default_categories(self, mapper):
        """Test getting default categories"""
        categories = mapper.get_default_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "Revenue" in categories
        assert "COGS" in categories


class TestMultiEntityProcessor:
    """Test suite for MultiEntityProcessor"""

    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        return MultiEntityProcessor()

    def test_create_processor(self, processor):
        """Test processor creation"""
        assert processor is not None
        assert isinstance(processor, MultiEntityProcessor)

    def test_consolidate_validation_results(self, processor):
        """Test validation result consolidation"""
        result1 = ValidationResult()
        result1.status = ValidationStatus.PASS
        result1.key_metrics = {
            "total_transactions": 10,
            "total_debits": 1000.0,
            "total_credits": 1000.0,
        }

        result2 = ValidationResult()
        result2.status = ValidationStatus.PASS
        result2.key_metrics = {
            "total_transactions": 5,
            "total_debits": 500.0,
            "total_credits": 500.0,
        }

        consolidated = processor._consolidate_validation_results([result1, result2])

        assert consolidated.key_metrics["total_transactions"] == 15
        assert consolidated.key_metrics["total_debits"] == 1500.0
        assert consolidated.key_metrics["total_credits"] == 1500.0
        assert consolidated.status == ValidationStatus.PASS

    def test_consolidate_validation_results_with_failure(self, processor):
        """Test consolidation when one validation fails"""
        result1 = ValidationResult()
        result1.status = ValidationStatus.PASS

        result2 = ValidationResult()
        result2.status = ValidationStatus.FAIL
        result2.errors = ["Test error"]

        consolidated = processor._consolidate_validation_results([result1, result2])

        assert consolidated.status == ValidationStatus.FAIL
        assert len(consolidated.errors) > 0


class TestDefaultCategories:
    """Test default categories constant"""

    def test_default_categories_exist(self):
        """Test that default categories are defined"""
        assert DEFAULT_CATEGORIES is not None
        assert isinstance(DEFAULT_CATEGORIES, list)
        assert len(DEFAULT_CATEGORIES) > 0

    def test_default_categories_content(self):
        """Test default categories content"""
        expected_categories = [
            "Revenue",
            "COGS",
            "OpEx",
            "Other Income/Expense",
            "Taxes",
            "Interest",
            "D&A",
            "Balance Sheet",
        ]

        for category in expected_categories:
            assert category in DEFAULT_CATEGORIES

