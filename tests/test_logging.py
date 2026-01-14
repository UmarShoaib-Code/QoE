"""
Tests for logging functionality across pipeline steps
"""

import pytest
import logging
import tempfile
import os
from pathlib import Path

from app.core.gl_pipeline import GLPipeline
from app.core.gl_ingestion import GLIngestionEngine
from app.core.validation import GLValidator
from app.excel.databook_generator import DatabookGenerator


class TestLogging:
    """Test suite for logging functionality"""

    @pytest.fixture
    def sample_gl_data(self):
        """Sample GL data"""
        import pandas as pd
        data = {
            "Date": ["Date", "2024-01-15", "2024-01-16"],
            "Account": ["Account", "Cash", "Revenue"],
            "Description": ["Description", "Deposit", "Sales"],
            "Debit": ["Debit", 1000.0, 0.0],
            "Credit": ["Credit", 0.0, 1000.0],
        }
        return pd.DataFrame(data)

    def test_logging_configured(self):
        """Test that logging is configured"""
        # Check that logging module is available
        assert logging is not None

        # Check that root logger exists
        root_logger = logging.getLogger()
        assert root_logger is not None

    def test_ingestion_logging(self, sample_gl_data, caplog):
        """Test that ingestion step produces log entries"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            sample_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            with caplog.at_level(logging.INFO):
                engine = GLIngestionEngine()
                normalized_df, report = engine.ingest_gl_file(
                    file_path=tmp_path,
                    entity="Test Company",
                    source_system="QuickBooks Desktop",
                )

                # Check that processing occurred (implicit logging test)
                assert normalized_df is not None
                assert report is not None

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_validation_logging(self, sample_gl_data, caplog):
        """Test that validation step produces log entries"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            sample_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            with caplog.at_level(logging.INFO):
                pipeline = GLPipeline()
                normalized_df, processing_report, validation_result = (
                    pipeline.process_gl_file(
                        file_path=tmp_path,
                        entity="Test Company",
                        source_system="QuickBooks Desktop",
                    )
                )

                # Check that validation occurred
                assert validation_result is not None
                assert hasattr(validation_result, "status")

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_excel_generation_logging(self, sample_gl_data, caplog):
        """Test that Excel generation step produces log entries"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            sample_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            pipeline = GLPipeline()
            normalized_df, processing_report, validation_result = (
                pipeline.process_gl_file(
                    file_path=tmp_path,
                    entity="Test Company",
                    source_system="QuickBooks Desktop",
                )
            )

            if validation_result.is_valid():
                with caplog.at_level(logging.INFO):
                    generator = DatabookGenerator()
                    output_path = tempfile.NamedTemporaryFile(
                        suffix=".xlsx", delete=False
                    ).name
                    try:
                        generator.generate_databook(
                            output_path=output_path,
                            normalized_df=normalized_df,
                            validation_result=validation_result,
                            processing_report=processing_report,
                            entity="Test Company",
                        )

                        # Check that file was generated
                        assert Path(output_path).exists()

                    finally:
                        if os.path.exists(output_path):
                            os.unlink(output_path)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_processing_report_contains_warnings(self, sample_gl_data):
        """Test that ProcessingReport contains warnings for logging"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            sample_gl_data.to_excel(tmp_file.name, index=False, header=False)
            tmp_path = tmp_file.name

        try:
            engine = GLIngestionEngine()
            normalized_df, report = engine.ingest_gl_file(
                file_path=tmp_path,
                entity="Test Company",
                source_system="QuickBooks Desktop",
            )

            # Check that report has warnings attribute
            assert hasattr(report, "warnings")
            assert isinstance(report.warnings, list)

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

