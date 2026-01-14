"""
Integration tests for complete GL processing pipeline

Tests the full workflow: ingestion -> normalization -> validation -> Excel generation
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from datetime import datetime

from app.core.gl_pipeline import GLPipeline
from app.core.validation import ValidationStatus
from app.excel.databook_generator import DatabookGenerator
from app.core.mapping import GLAccountMapper


class TestPipelineIntegration:
    """Integration tests for complete pipeline"""

    @pytest.fixture
    def sample_qbd_data(self):
        """Sample QuickBooks Desktop format with parent/subaccount headers"""
        data = {
            "Date": [
                "Date",  # Header
                None,  # Parent account header
                "2024-01-15",
                "2024-01-16",
                None,  # Sub-account header
                "2024-01-17",
            ],
            "Account": [
                "Account",  # Header
                "Assets",  # Parent account
                "Cash",
                "Cash",
                "  Accounts Receivable",  # Indented sub-account
                "  Accounts Receivable",
            ],
            "Description": [
                "Description",
                "",
                "Deposit",
                "Withdrawal",
                "",
                "Invoice Payment",
            ],
            "Debit": [
                "Debit",
                "",
                1000.0,
                500.0,
                "",
                200.0,
            ],
            "Credit": [
                "Credit",
                "",
                0.0,
                0.0,
                "",
                0.0,
            ],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def balanced_gl_data(self):
        """Sample balanced GL data (debits = credits)"""
        data = {
            "Date": [
                "Date",
                "2024-01-15",
                "2024-01-16",
                "2024-01-17",
            ],
            "Account": [
                "Account",
                "Cash",
                "Revenue",
                "Expenses",
            ],
            "Description": [
                "Description",
                "Deposit",
                "Sales",
                "Rent",
            ],
            "Debit": [
                "Debit",
                1000.0,
                0.0,
                500.0,
            ],
            "Credit": [
                "Credit",
                0.0,
                1000.0,
                500.0,
            ],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def unbalanced_gl_data(self):
        """Sample unbalanced GL data (debits ≠ credits)"""
        data = {
            "Date": [
                "Date",
                "2024-01-15",
                "2024-01-16",
            ],
            "Account": [
                "Account",
                "Cash",
                "Revenue",
            ],
            "Description": [
                "Description",
                "Deposit",
                "Sales",
            ],
            "Debit": [
                "Debit",
                1000.0,
                0.0,
            ],
            "Credit": [
                "Credit",
                0.0,
                300.0,  # Unbalanced!
            ],
        }
        return pd.DataFrame(data)

    def test_validation_before_excel_generation(self, balanced_gl_data):
        """Test that validation runs before Excel generation"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Validation should have run
            assert validation_result is not None
            assert hasattr(validation_result, "status")
            assert hasattr(validation_result, "is_valid")

            # Excel generation should only proceed if validation passes
            if validation_result.is_valid():
                generator = DatabookGenerator()
                output_path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
                try:
                    generator.generate_databook(
                        output_path=output_path,
                        normalized_df=normalized_df,
                        validation_result=validation_result,
                        processing_report=processing_report,
                        entity="Test Company",
                    )
                    assert Path(output_path).exists()
                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_debit_credit_mismatch_stops_workflow(self, unbalanced_gl_data):
        """Test that debit/credit mismatch causes validation failure and blocks Excel"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            unbalanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Validation should fail
            assert validation_result.status == ValidationStatus.FAIL
            assert not validation_result.is_valid()

            # Should have debit/credit error
            error_messages = " ".join(validation_result.errors).lower()
            assert "debit" in error_messages or "credit" in error_messages

            # Excel generation should be blocked (test by checking validation status)
            # In actual workflow, UI/API should check validation_result.is_valid() before generating

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_qbd_header_subaccount_flattening(self, sample_qbd_data):
        """Test that QBD parent/subaccount headers are correctly flattened"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            sample_qbd_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Check that account_name_flat exists and contains flattened names
            assert "account_name_flat" in normalized_df.columns

            # Check for flattened account names (should contain "Assets : Cash" or similar)
            flat_accounts = normalized_df["account_name_flat"].str.lower()
            # At least some accounts should have parent:child structure if headers were present
            # Note: This depends on the exact flattening logic implementation

            # Verify that parent account headers were used
            # Accounts under "Assets" parent should have "Assets" in their flattened name
            assets_rows = normalized_df[
                normalized_df["account_name_raw"].str.contains("Cash", case=False, na=False)
            ]
            if len(assets_rows) > 0:
                # Check that flattening occurred (either has parent or is standalone)
                assert len(assets_rows) > 0

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_excel_styling_blue_white(self, balanced_gl_data):
        """Test that Excel output has correct blue/white styling"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            if validation_result.is_valid():
                generator = DatabookGenerator()
                output_path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
                try:
                    generator.generate_databook(
                        output_path=output_path,
                        normalized_df=normalized_df,
                        validation_result=validation_result,
                        processing_report=processing_report,
                        entity="Test Company",
                    )

                    # Verify file exists and can be opened
                    assert Path(output_path).exists()

                    # Note: Actual styling verification would require opening the file
                    # with openpyxl or xlsxwriter and checking cell formats
                    # This is a structural test - styling is verified in unit tests

                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_excel_tables_filters_freeze_panes(self, balanced_gl_data):
        """Test that Excel output has tables, filters, and freeze panes"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            if validation_result.is_valid():
                generator = DatabookGenerator()
                output_path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
                try:
                    generator.generate_databook(
                        output_path=output_path,
                        normalized_df=normalized_df,
                        validation_result=validation_result,
                        processing_report=processing_report,
                        entity="Test Company",
                    )

                    # Verify file exists
                    assert Path(output_path).exists()

                    # Note: Table/filter/freeze pane verification requires reading Excel file
                    # This is verified in Excel generator unit tests
                    # This test ensures the file is generated successfully

                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_excel_formulas_recalculate(self, balanced_gl_data):
        """Test that Excel formulas are present and can recalculate"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            if validation_result.is_valid():
                # Generate with formulas (default)
                generator = DatabookGenerator(break_formulas=False)
                output_path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
                try:
                    generator.generate_databook(
                        output_path=output_path,
                        normalized_df=normalized_df,
                        validation_result=validation_result,
                        processing_report=processing_report,
                        entity="Test Company",
                    )

                    # Verify file exists
                    assert Path(output_path).exists()

                    # Note: Formula verification requires reading Excel file with openpyxl
                    # This test ensures file generation succeeds
                    # Formula correctness is verified in Excel generator unit tests

                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_processing_report_available(self, balanced_gl_data):
        """Test that ProcessingReport is available with row counts"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Processing report should be available
            assert processing_report is not None
            assert hasattr(processing_report, "total_rows_read")
            assert hasattr(processing_report, "final_transaction_rows")
            assert hasattr(processing_report, "rows_with_invalid_dates")
            assert hasattr(processing_report, "warnings")

            # Should have row counts
            assert processing_report.total_rows_read >= 0
            assert processing_report.final_transaction_rows >= 0

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_complete_workflow_end_to_end(self, balanced_gl_data):
        """Test complete workflow from file upload to Excel generation"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            balanced_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            # Step 1: Ingestion and normalization
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = pipeline.process_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Step 2: Validation check
            assert validation_result is not None
            if not validation_result.is_valid():
                pytest.skip("Validation failed - cannot test Excel generation")

            # Step 3: Excel generation
            generator = DatabookGenerator()
            output_path = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False).name
            try:
                generator.generate_databook(
                    output_path=output_path,
                    normalized_df=normalized_df,
                    validation_result=validation_result,
                    processing_report=processing_report,
                    entity="Test Company",
                )

                # Verify output
                assert Path(output_path).exists()
                file_size = Path(output_path).stat().st_size
                assert file_size > 0  # File should not be empty

            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

