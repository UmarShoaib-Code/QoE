"""
GL Data Validation Module

Validates normalized GL data to ensure data quality before mapping and EBITDA calculations.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    """Result of GL data validation"""

    status: ValidationStatus = ValidationStatus.PASS
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    key_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            "status": self.status.value,
            "errors": self.errors,
            "warnings": self.warnings,
            "key_metrics": self.key_metrics,
        }

    def is_valid(self) -> bool:
        """Check if validation passed"""
        return self.status == ValidationStatus.PASS


class GLValidator:
    """Validator for normalized GL data"""

    def __init__(
        self,
        min_transactions: int = 1,
        max_date_parse_failure_rate: float = 0.1,
        debit_credit_tolerance: float = 0.01,
    ):
        """
        Initialize GL validator with configuration.

        Args:
            min_transactions: Minimum number of transactions required (default: 1)
            max_date_parse_failure_rate: Maximum allowed date parse failure rate (default: 0.1 = 10%)
            debit_credit_tolerance: Tolerance for debit/credit equality check (default: 0.01)
        """
        self.min_transactions = min_transactions
        self.max_date_parse_failure_rate = max_date_parse_failure_rate
        self.debit_credit_tolerance = debit_credit_tolerance

    def validate(
        self,
        normalized_df: pd.DataFrame,
        processing_report: Optional[Any] = None,
    ) -> ValidationResult:
        """
        Validate normalized GL data.

        Args:
            normalized_df: Normalized DataFrame from GL ingestion
            processing_report: Optional ProcessingReport from ingestion for additional context

        Returns:
            ValidationResult with status, errors, warnings, and key metrics
        """
        result = ValidationResult()

        if normalized_df.empty:
            result.status = ValidationStatus.FAIL
            result.errors.append(
                "❌ **No transactions found in your GL file**\n\n"
                "**What happened:** The file you uploaded appears to be empty or contains no valid transaction data.\n\n"
                "**Why this usually happens:**\n"
                "• The Excel file may be blank or contain only headers\n"
                "• The file format may not match QuickBooks Desktop or QuickBooks Online exports\n"
                "• All rows may have been filtered out during processing (e.g., totals, subtotals, or invalid dates)\n\n"
                "**What to do next:**\n"
                "• Verify the file contains actual transaction data\n"
                "• Ensure you exported the General Ledger report from QuickBooks\n"
                "• Check that the file includes date, account, debit, and credit columns\n"
                "• Try re-exporting the GL report from QuickBooks"
            )
            result.key_metrics = {
                "total_transactions": 0,
                "total_debits": 0.0,
                "total_credits": 0.0,
                "date_parse_failure_rate": 0.0,
            }
            return result

        # Collect key metrics
        total_transactions = len(normalized_df)
        total_debits = float(normalized_df["debit"].sum())
        total_credits = float(normalized_df["credit"].sum())

        # Calculate date parse failure rate from processing report if available
        # Exclude header row from calculation since it's expected to not have a date
        date_parse_failure_rate = 0.0
        if processing_report:
            total_rows_read = processing_report.total_rows_read
            rows_with_invalid_dates = processing_report.rows_with_invalid_dates
            
            # Exclude header row from total (if detected) for failure rate calculation
            rows_expected_to_have_dates = total_rows_read
            if processing_report.header_row_index is not None:
                rows_expected_to_have_dates = total_rows_read - 1  # Exclude header row
            
            if rows_expected_to_have_dates > 0:
                date_parse_failure_rate = rows_with_invalid_dates / rows_expected_to_have_dates

        result.key_metrics = {
            "total_transactions": total_transactions,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "debit_credit_difference": abs(total_debits - total_credits),
            "date_parse_failure_rate": date_parse_failure_rate,
        }

        # 1. Debit/Credit equality check
        self._validate_debit_credit_equality(
            total_debits, total_credits, result
        )

        # 2. Transaction validity checks
        self._validate_transaction_count(total_transactions, result)
        self._validate_date_parse_failure_rate(date_parse_failure_rate, result)

        # 3. Negative debit/credit warnings
        self._check_negative_amounts(normalized_df, result)

        # Update status based on errors
        if result.errors:
            result.status = ValidationStatus.FAIL

        return result

    def _validate_debit_credit_equality(
        self,
        total_debits: float,
        total_credits: float,
        result: ValidationResult,
    ) -> None:
        """
        Validate that total debits equal total credits.

        Args:
            total_debits: Sum of all debit amounts
            total_credits: Sum of all credit amounts
            result: ValidationResult to update
        """
        difference = abs(total_debits - total_credits)

        if difference > self.debit_credit_tolerance:
            error_msg = (
                f"❌ **Debits and Credits Don't Balance**\n\n"
                f"**What failed:** Your GL data shows total debits of ${total_debits:,.2f} and total credits of ${total_credits:,.2f}, "
                f"with a difference of ${difference:,.2f}. In accounting, debits must equal credits.\n\n"
                "**Why this usually happens:**\n"
                "• The GL export may be incomplete (missing some transactions or date ranges)\n"
                "• Some rows may have been filtered out during processing (totals, subtotals, or invalid dates)\n"
                "• The export may have been cut off or corrupted during download\n"
                "• You may have selected the wrong date range or account filters in QuickBooks\n\n"
                "**What to do next:**\n"
                "• Verify your QuickBooks GL report shows balanced debits and credits before exporting\n"
                "• Re-export the General Ledger report ensuring all transactions are included\n"
                "• Check that you selected the correct date range and account filters\n"
                "• Ensure the file wasn't modified after export (don't add/delete rows manually)\n"
                "• If the issue persists, contact your accounting team to verify the GL data integrity"
            )
            result.errors.append(error_msg)

    def _validate_transaction_count(
        self, total_transactions: int, result: ValidationResult
    ) -> None:
        """
        Validate minimum transaction count.

        Args:
            total_transactions: Number of transactions in the dataset
            result: ValidationResult to update
        """
        if total_transactions < self.min_transactions:
            error_msg = (
                f"❌ **Insufficient Transaction Data**\n\n"
                f"**What failed:** Your GL file contains only {total_transactions} transaction(s), "
                f"but at least {self.min_transactions} transaction(s) are required for processing.\n\n"
                "**Why this usually happens:**\n"
                "• The date range selected in QuickBooks may be too narrow\n"
                "• Account filters may have excluded most transactions\n"
                "• The file may have been filtered too aggressively during processing\n"
                "• You may have uploaded a summary report instead of detailed transactions\n\n"
                "**What to do next:**\n"
                "• Re-export the General Ledger report with a broader date range\n"
                "• Remove account filters or expand the account selection in QuickBooks\n"
                "• Ensure you're exporting detailed transactions, not summary totals\n"
                "• Verify the file contains actual transaction rows, not just headers or totals"
            )
            result.errors.append(error_msg)

    def _validate_date_parse_failure_rate(
        self, failure_rate: float, result: ValidationResult
    ) -> None:
        """
        Validate date parse failure rate is below threshold.

        Args:
            failure_rate: Rate of date parse failures (0.0 to 1.0)
            result: ValidationResult to update
        """
        if failure_rate > self.max_date_parse_failure_rate:
            error_msg = (
                f"❌ **Too Many Invalid Dates in Your GL File**\n\n"
                f"**What failed:** {failure_rate:.1%} of rows in your GL file have invalid or unreadable dates, "
                f"which exceeds the maximum allowed rate of {self.max_date_parse_failure_rate:.1%}.\n\n"
                "**Why this usually happens:**\n"
                "• Date columns may be formatted inconsistently in the Excel file\n"
                "• The file may contain header rows, totals, or subtotals mixed with transactions\n"
                "• Dates may be stored as text instead of date values in Excel\n"
                "• The QuickBooks export format may have changed or be corrupted\n\n"
                "**What to do next:**\n"
                "• Re-export the General Ledger report from QuickBooks using the standard format\n"
                "• Ensure dates are in a consistent format (MM/DD/YYYY or YYYY-MM-DD)\n"
                "• Remove any manual formatting or merged cells from the Excel file\n"
                "• Verify the file opens correctly in Excel and dates display properly\n"
                "• If using QuickBooks Desktop, try exporting to CSV first, then converting to Excel"
            )
            result.errors.append(error_msg)

    def _check_negative_amounts(
        self, df: pd.DataFrame, result: ValidationResult
    ) -> None:
        """
        Check for negative debits or credits and add warnings.

        Args:
            df: Normalized DataFrame
            result: ValidationResult to update
        """
        negative_debits = (df["debit"] < 0).sum()
        negative_credits = (df["credit"] < 0).sum()

        if negative_debits > 0:
            warning_msg = (
                f"⚠️ **Negative Debits Detected**\n\n"
                f"**What we found:** {negative_debits} transaction(s) have negative debit amounts.\n\n"
                "**Why this usually happens:**\n"
                "• Credit memos or refunds may be recorded as negative debits\n"
                "• Reversing entries may use negative amounts\n"
                "• Data entry errors where credits were entered in the debit column\n\n"
                "**What to do next:**\n"
                "• Review these transactions in QuickBooks to verify they're correct\n"
                "• If these are valid credit memos or reversals, no action needed\n"
                "• If these are errors, correct them in QuickBooks and re-export"
            )
            result.warnings.append(warning_msg)

        if negative_credits > 0:
            warning_msg = (
                f"⚠️ **Negative Credits Detected**\n\n"
                f"**What we found:** {negative_credits} transaction(s) have negative credit amounts.\n\n"
                "**Why this usually happens:**\n"
                "• Debit memos or adjustments may be recorded as negative credits\n"
                "• Reversing entries may use negative amounts\n"
                "• Data entry errors where debits were entered in the credit column\n\n"
                "**What to do next:**\n"
                "• Review these transactions in QuickBooks to verify they're correct\n"
                "• If these are valid debit memos or reversals, no action needed\n"
                "• If these are errors, correct them in QuickBooks and re-export"
            )
            result.warnings.append(warning_msg)

