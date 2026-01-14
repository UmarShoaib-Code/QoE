"""
GL Processing Pipeline

Combines ingestion, normalization, and validation into a single pipeline.
"""

from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

from app.core.gl_ingestion import GLIngestionEngine, ProcessingReport
from app.core.validation import GLValidator, ValidationResult


class GLPipeline:
    """Complete pipeline for GL processing: ingestion -> normalization -> validation"""

    def __init__(
        self,
        min_transactions: int = 1,
        max_date_parse_failure_rate: float = 0.1,
        debit_credit_tolerance: float = 0.01,
    ):
        """
        Initialize GL pipeline.

        Args:
            min_transactions: Minimum number of transactions required
            max_date_parse_failure_rate: Maximum allowed date parse failure rate
            debit_credit_tolerance: Tolerance for debit/credit equality check
        """
        self.ingestion_engine = GLIngestionEngine()
        self.validator = GLValidator(
            min_transactions=min_transactions,
            max_date_parse_failure_rate=max_date_parse_failure_rate,
            debit_credit_tolerance=debit_credit_tolerance,
        )

    def process_gl_file(
        self,
        file_path: str | Path,
        entity: str,
        source_system: str = "QuickBooks",
        sheet_name: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, ProcessingReport, ValidationResult]:
        """
        Process GL file through complete pipeline.

        Args:
            file_path: Path to the Excel file
            entity: Entity name
            source_system: Source system identifier
            sheet_name: Specific sheet name to read (None = first sheet)

        Returns:
            Tuple of (normalized_df, processing_report, validation_result)
        """
        # Step 1: Ingestion and normalization
        normalized_df, processing_report = self.ingestion_engine.ingest_gl_file(
            file_path=file_path,
            entity=entity,
            source_system=source_system,
            sheet_name=sheet_name,
        )

        # Step 2: Validation (runs immediately after normalization)
        validation_result = self.validator.validate(
            normalized_df=normalized_df,
            processing_report=processing_report,
        )

        return normalized_df, processing_report, validation_result

