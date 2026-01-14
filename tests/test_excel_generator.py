"""
Unit tests for Excel databook generator
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from datetime import datetime

from app.excel.databook_generator import DatabookGenerator
from app.excel.styles import ExcelStyles
from app.core.validation import ValidationResult, ValidationStatus
from app.core.gl_ingestion import ProcessingReport


class TestDatabookGenerator:
    """Test suite for DatabookGenerator"""

    @pytest.fixture
    def sample_normalized_df(self):
        """Sample normalized DataFrame"""
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
    def sample_validation_result(self):
        """Sample validation result"""
        result = ValidationResult()
        result.status = ValidationStatus.PASS
        result.key_metrics = {
            "total_transactions": 5,
            "total_debits": 1500.0,
            "total_credits": 1000.0,
            "debit_credit_difference": 500.0,
            "date_parse_failure_rate": 0.0,
        }
        return result

    @pytest.fixture
    def sample_processing_report(self):
        """Sample processing report"""
        report = ProcessingReport()
        report.total_rows_read = 10
        report.rows_with_invalid_dates = 2
        report.rows_removed_totals = 1
        report.rows_removed_subtotals = 1
        report.rows_removed_opening_balance = 1
        report.final_transaction_rows = 5
        return report

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        return DatabookGenerator()

    @pytest.fixture
    def generator_break_formulas(self):
        """Create generator with break_formulas=True"""
        return DatabookGenerator(break_formulas=True)

    def test_create_generator(self, generator):
        """Test generator creation"""
        assert generator is not None
        assert generator.break_formulas is False

    def test_generate_databook_basic(
        self,
        generator,
        sample_normalized_df,
        sample_validation_result,
        sample_processing_report,
    ):
        """Test basic databook generation"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            result_path = generator.generate_databook(
                output_path=output_path,
                normalized_df=sample_normalized_df,
                validation_result=sample_validation_result,
                processing_report=sample_processing_report,
                source_files=["test.xlsx"],
                entity="Test Company",
            )

            assert Path(result_path).exists()
            assert Path(result_path).suffix == ".xlsx"

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_generate_databook_with_break_formulas(
        self,
        generator_break_formulas,
        sample_normalized_df,
        sample_validation_result,
        sample_processing_report,
    ):
        """Test databook generation with formulas broken"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            result_path = generator_break_formulas.generate_databook(
                output_path=output_path,
                normalized_df=sample_normalized_df,
                validation_result=sample_validation_result,
                processing_report=sample_processing_report,
            )

            assert Path(result_path).exists()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_generate_databook_empty_dataframe(
        self,
        generator,
        sample_validation_result,
        sample_processing_report,
    ):
        """Test databook generation with empty DataFrame"""
        empty_df = pd.DataFrame()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            result_path = generator.generate_databook(
                output_path=output_path,
                normalized_df=empty_df,
                validation_result=sample_validation_result,
                processing_report=sample_processing_report,
            )

            assert Path(result_path).exists()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_generate_databook_validation_fail(
        self,
        generator,
        sample_normalized_df,
        sample_processing_report,
    ):
        """Test databook generation with validation failure"""
        validation_result = ValidationResult()
        validation_result.status = ValidationStatus.FAIL
        validation_result.errors = ["Test error"]
        validation_result.key_metrics = {
            "total_transactions": 5,
            "total_debits": 1500.0,
            "total_credits": 1000.0,
        }

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Should still generate file even with validation failure
            result_path = generator.generate_databook(
                output_path=output_path,
                normalized_df=sample_normalized_df,
                validation_result=validation_result,
                processing_report=sample_processing_report,
            )

            assert Path(result_path).exists()

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestExcelStyles:
    """Test suite for ExcelStyles"""

    def test_get_header_format(self):
        """Test header format generation"""
        format_dict = ExcelStyles.get_header_format()
        assert "bg_color" in format_dict
        assert "font_color" in format_dict
        assert "font_name" in format_dict
        assert "bold" in format_dict

    def test_get_table_banding_format(self):
        """Test table banding format generation"""
        format_dict = ExcelStyles.get_table_banding_format(is_even=False)
        assert "bg_color" in format_dict
        assert "font_name" in format_dict

        format_dict_even = ExcelStyles.get_table_banding_format(is_even=True)
        assert "bg_color" in format_dict_even

    def test_get_status_format(self):
        """Test status format generation"""
        pass_format = ExcelStyles.get_status_format("PASS")
        assert "bg_color" in pass_format
        assert "font_color" in pass_format

        fail_format = ExcelStyles.get_status_format("FAIL")
        assert "bg_color" in fail_format

    def test_rgb_to_hex(self):
        """Test RGB to hex conversion"""
        hex_color = ExcelStyles._rgb_to_hex((255, 0, 0))
        assert hex_color == "#ff0000"
        assert hex_color.startswith("#")

    def test_get_currency_format_dict(self):
        """Test currency format dictionary"""
        format_dict = ExcelStyles.get_currency_format_dict()
        assert "num_format" in format_dict
        assert "$" in format_dict["num_format"]

    def test_get_date_format_dict(self):
        """Test date format dictionary"""
        format_dict = ExcelStyles.get_date_format_dict()
        assert "num_format" in format_dict

    def test_get_percentage_format_dict(self):
        """Test percentage format dictionary"""
        format_dict = ExcelStyles.get_percentage_format_dict()
        assert "num_format" in format_dict
        assert "%" in format_dict["num_format"]

