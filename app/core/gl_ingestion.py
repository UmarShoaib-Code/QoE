"""
GL (General Ledger) Ingestion and Normalization Engine

Processes raw Excel GL exports from QuickBooks Desktop and QuickBooks Online,
normalizing them into a standardized format.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcessingReport:
    """Report of GL processing operations"""

    total_rows_read: int = 0
    header_row_index: Optional[int] = None  # Track detected header row
    rows_with_invalid_dates: int = 0
    rows_removed_totals: int = 0
    rows_removed_subtotals: int = 0
    rows_removed_opening_balance: int = 0
    final_transaction_rows: int = 0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "total_rows_read": self.total_rows_read,
            "rows_with_invalid_dates": self.rows_with_invalid_dates,
            "rows_removed_totals": self.rows_removed_totals,
            "rows_removed_subtotals": self.rows_removed_subtotals,
            "rows_removed_opening_balance": self.rows_removed_opening_balance,
            "final_transaction_rows": self.final_transaction_rows,
            "warnings": self.warnings,
        }


class GLIngestionEngine:
    """Engine for ingesting and normalizing GL data from Excel exports"""

    # Common patterns for totals/subtotals/opening balances
    TOTAL_PATTERNS = [
        "total",
        "totals",
        "grand total",
        "period total",
        "period totals",
    ]
    SUBTOTAL_PATTERNS = ["subtotal", "subtotals"]
    OPENING_BALANCE_PATTERNS = [
        "opening balance",
        "opening balances",
        "beginning balance",
        "beginning balances",
    ]

    def __init__(self):
        """Initialize the GL ingestion engine"""
        pass

    def ingest_gl_file(
        self,
        file_path: str | Path,
        entity: str,
        source_system: str = "QuickBooks",
        sheet_name: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, ProcessingReport]:
        """
        Ingest and normalize a GL Excel file.

        Args:
            file_path: Path to the Excel file
            entity: Entity name (e.g., company name)
            source_system: Source system identifier (default: "QuickBooks")
            sheet_name: Specific sheet name to read (None = first sheet)

        Returns:
            Tuple of (normalized_df, processing_report)
        """
        file_path = Path(file_path)
        report = ProcessingReport()

        # Read Excel file
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            else:
                df = pd.read_excel(file_path, sheet_name=0, header=None)
        except Exception as e:
            report.warnings.append(f"Error reading Excel file: {str(e)}")
            return pd.DataFrame(), report

        report.total_rows_read = len(df)

        # Detect column structure (QuickBooks Desktop vs Online)
        df_normalized = self._detect_and_parse_structure(df, file_path.name, report)

        # Normalize the data
        df_normalized = self._normalize_data(
            df_normalized, entity, source_system, file_path.name, report
        )

        report.final_transaction_rows = len(df_normalized)

        return df_normalized, report

    def _detect_and_parse_structure(
        self, df: pd.DataFrame, filename: str, report: ProcessingReport
    ) -> pd.DataFrame:
        """
        Detect QuickBooks format and parse into standard structure.

        QuickBooks Desktop typically has:
        - Date, Account, Description, Debit, Credit columns
        - Account headers on separate rows

        QuickBooks Online typically has:
        - Date, Account, Description, Debit, Credit columns
        - More structured format

        Returns DataFrame with columns: date, account_name_raw, description, debit, credit
        """
        # Handle empty DataFrame
        if df.empty or len(df) == 0:
            return pd.DataFrame()

        # Try to find header row (look for "Date" or "Account" in first few rows)
        header_row_idx = None
        for idx in range(min(5, len(df))):
            row_values = df.iloc[idx].astype(str).str.lower().values
            if any("date" in str(val) for val in row_values) or any(
                "account" in str(val) for val in row_values
            ):
                header_row_idx = idx
                break

        if header_row_idx is None:
            # Assume first row is header
            header_row_idx = 0
            report.warnings.append("Could not detect header row, assuming first row")

        # Track header row index for validation
        report.header_row_index = header_row_idx

        # Extract column mappings
        header_row = df.iloc[header_row_idx].astype(str).str.lower()

        # Find column indices
        date_col = None
        account_col = None
        desc_col = None
        debit_col = None
        credit_col = None

        for idx, val in enumerate(header_row):
            val_lower = str(val).lower()
            if "date" in val_lower and date_col is None:
                date_col = idx
            elif "account" in val_lower and account_col is None:
                account_col = idx
            elif ("description" in val_lower or "memo" in val_lower or "name" in val_lower) and desc_col is None:
                desc_col = idx
            elif "debit" in val_lower and debit_col is None:
                debit_col = idx
            elif "credit" in val_lower and credit_col is None:
                credit_col = idx

        # If columns not found, try common positions
        if date_col is None:
            date_col = 0
        if account_col is None:
            account_col = 1
        if desc_col is None:
            desc_col = 2
        if debit_col is None:
            debit_col = 3
        if credit_col is None:
            credit_col = 4

        # Extract data rows (skip header)
        data_start = header_row_idx + 1
        result_df = pd.DataFrame()

        if len(df) > data_start:
            result_df["date"] = df.iloc[data_start:, date_col].reset_index(drop=True)
            result_df["account_name_raw"] = (
                df.iloc[data_start:, account_col].astype(str).reset_index(drop=True)
            )
            if desc_col < len(df.columns):
                result_df["description"] = (
                    df.iloc[data_start:, desc_col].astype(str).reset_index(drop=True)
                )
            else:
                result_df["description"] = ""
            if debit_col < len(df.columns):
                result_df["debit"] = df.iloc[data_start:, debit_col].reset_index(drop=True)
            else:
                result_df["debit"] = 0
            if credit_col < len(df.columns):
                result_df["credit"] = df.iloc[data_start:, credit_col].reset_index(drop=True)
            else:
                result_df["credit"] = 0

        return result_df

    def _normalize_data(
        self,
        df: pd.DataFrame,
        entity: str,
        source_system: str,
        gl_source_file: str,
        report: ProcessingReport,
    ) -> pd.DataFrame:
        """
        Normalize the GL data according to specifications.

        Steps:
        1. Add metadata columns
        2. Parse and validate dates
        3. Forward-fill account names and build flattened account names
        4. Remove non-transaction rows
        5. Standardize numeric columns
        6. Compute amount_net
        """
        if df.empty:
            return self._create_empty_normalized_df()

        # Add metadata columns
        df["entity"] = entity
        df["source_system"] = source_system
        df["gl_source_file"] = gl_source_file
        df["row_id"] = range(len(df))

        # Parse dates (but don't remove invalid dates yet - we need headers for hierarchy)
        df["date"] = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True)

        # Forward-fill account names (for QuickBooks Desktop parent/subaccount structure)
        df["account_name_raw"] = df["account_name_raw"].fillna("")
        df["account_name_raw"] = df["account_name_raw"].astype(str)

        # Build account hierarchy by forward-filling BEFORE removing invalid dates
        # QuickBooks Desktop often has parent accounts on separate rows before transactions
        account_hierarchy = []
        current_hierarchy = []
        is_transaction_row = []

        for idx, row in df.iterrows():
            account_raw = str(row["account_name_raw"]).strip()
            has_valid_date = not pd.isna(row["date"])

            # Check if this is an account header (no valid date or no debit/credit)
            is_header = False
            if not has_valid_date:
                is_header = True
            else:
                # Check if debit and credit are both empty/zero
                debit_val = self._safe_numeric(row.get("debit", 0))
                credit_val = self._safe_numeric(row.get("credit", 0))
                if debit_val == 0 and credit_val == 0 and account_raw:
                    # Likely a header row (parent account)
                    is_header = True

            if is_header and account_raw:
                # This is a parent account header - update hierarchy
                level = self._detect_account_level(account_raw, current_hierarchy)
                # Update current hierarchy at the detected level
                current_hierarchy = current_hierarchy[:level] + [account_raw]
                # Headers don't get added to account_hierarchy (they're not transactions)
                account_hierarchy.append("")
                is_transaction_row.append(False)
            elif account_raw and has_valid_date:
                # This is a transaction row - use current hierarchy + this account
                if current_hierarchy:
                    # Build flattened name: Parent : Sub : Account
                    full_hierarchy = current_hierarchy + [account_raw]
                    account_flat = " : ".join([a.strip() for a in full_hierarchy if a.strip()])
                else:
                    # No parent hierarchy, just use the account name
                    account_flat = account_raw
                account_hierarchy.append(account_flat)
                is_transaction_row.append(True)
                # Don't update hierarchy with transaction accounts - they're leaf nodes
            else:
                # Empty account or invalid row
                account_hierarchy.append("")
                is_transaction_row.append(False)
                # Reset hierarchy if we hit an empty row
                if not account_raw:
                    current_hierarchy = []

        df["account_name_flat"] = account_hierarchy
        df["_is_transaction"] = is_transaction_row

        # If account_name_flat is empty, use account_name_raw
        df["account_name_flat"] = df["account_name_flat"].replace("", np.nan)
        df["account_name_flat"] = df["account_name_flat"].fillna(df["account_name_raw"])

        # Now remove rows with invalid dates (non-transaction rows)
        # Keep transaction rows with valid dates, remove everything else
        invalid_date_mask = ~df["_is_transaction"] | df["date"].isna()
        report.rows_with_invalid_dates = invalid_date_mask.sum()
        df = df[df["_is_transaction"] & df["date"].notna()].copy()

        # Drop the helper column
        if "_is_transaction" in df.columns:
            df = df.drop(columns=["_is_transaction"])

        if df.empty:
            return self._create_empty_normalized_df()

        # Remove totals, subtotals, and opening balances
        df = self._remove_summary_rows(df, report)

        # Standardize numeric columns
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)

        # Compute amount_net
        df["amount_net"] = df["debit"] - df["credit"]

        # Ensure description is string
        df["description"] = df["description"].fillna("").astype(str)

        # Reorder columns to match specification
        column_order = [
            "entity",
            "source_system",
            "gl_source_file",
            "row_id",
            "date",
            "account_name_raw",
            "account_name_flat",
            "description",
            "debit",
            "credit",
            "amount_net",
        ]

        # Select only columns that exist
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]

        return df.reset_index(drop=True)

    def _detect_account_level(self, account_name: str, current_hierarchy: List[str]) -> int:
        """
        Detect the hierarchy level of an account name.
        Returns the level (0 = top level, 1 = sub-account, etc.)
        """
        # Simple heuristic: check for indentation (leading spaces/tabs)
        stripped = account_name.strip()
        leading_spaces = len(account_name) - len(stripped)

        # If significantly indented, it's likely a sub-account
        if leading_spaces > 2:
            # Determine level based on indentation
            level = min(leading_spaces // 4, len(current_hierarchy))
            return level

        # Check for common parent account indicators
        account_lower = account_name.lower()
        if any(
            indicator in account_lower
            for indicator in ["assets", "liabilities", "equity", "income", "expenses", "revenue"]
        ):
            return 0

        # Default: assume it's at the next level
        return len(current_hierarchy)

    def _remove_summary_rows(
        self, df: pd.DataFrame, report: ProcessingReport
    ) -> pd.DataFrame:
        """Remove totals, subtotals, and opening balance rows"""
        if df.empty:
            return df

        original_len = len(df)

        # Check account names for summary patterns
        account_lower = df["account_name_raw"].str.lower().fillna("")
        desc_lower = df["description"].str.lower().fillna("")

        # Remove totals
        total_mask = account_lower.str.contains("|".join(self.TOTAL_PATTERNS), case=False, na=False)
        total_mask |= desc_lower.str.contains("|".join(self.TOTAL_PATTERNS), case=False, na=False)
        report.rows_removed_totals = total_mask.sum()
        df = df[~total_mask].copy()

        # Remove subtotals
        subtotal_mask = account_lower.str.contains(
            "|".join(self.SUBTOTAL_PATTERNS), case=False, na=False
        )
        subtotal_mask |= desc_lower.str.contains(
            "|".join(self.SUBTOTAL_PATTERNS), case=False, na=False
        )
        report.rows_removed_subtotals = subtotal_mask.sum()
        df = df[~subtotal_mask].copy()

        # Remove opening balances
        opening_mask = account_lower.str.contains(
            "|".join(self.OPENING_BALANCE_PATTERNS), case=False, na=False
        )
        opening_mask |= desc_lower.str.contains(
            "|".join(self.OPENING_BALANCE_PATTERNS), case=False, na=False
        )
        report.rows_removed_opening_balance = opening_mask.sum()
        df = df[~opening_mask].copy()

        return df

    def _safe_numeric(self, value: Any) -> float:
        """Safely convert value to numeric"""
        if pd.isna(value):
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _create_empty_normalized_df(self) -> pd.DataFrame:
        """Create an empty DataFrame with the correct column structure"""
        return pd.DataFrame(
            columns=[
                "entity",
                "source_system",
                "gl_source_file",
                "row_id",
                "date",
                "account_name_raw",
                "account_name_flat",
                "description",
                "debit",
                "credit",
                "amount_net",
            ]
        )

