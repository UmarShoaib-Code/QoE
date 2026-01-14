"""
Excel Databook Generator

Creates analyst-ready Excel workbooks with multiple tabs for GL analysis.
"""

import pandas as pd
import xlsxwriter
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.excel.styles import ExcelStyles
from app.core.validation import ValidationResult
from app.core.gl_ingestion import ProcessingReport


class DatabookGenerator:
    """Generator for Excel databook with multiple formatted tabs"""

    def __init__(self, break_formulas: bool = False):
        """
        Initialize databook generator.

        Args:
            break_formulas: If True, replace formulas with calculated values for performance
        """
        self.break_formulas = break_formulas
        self.workbook = None
        self.workbook_path = None

    def generate_databook(
        self,
        output_path: str | Path,
        normalized_df: pd.DataFrame,
        validation_result: ValidationResult,
        processing_report: ProcessingReport,
        source_files: Optional[List[str]] = None,
        entity: Optional[str] = None,
        mapping_df: Optional[pd.DataFrame] = None,
        adjustment_df: Optional[pd.DataFrame] = None,
        adjustment_log_df: Optional[pd.DataFrame] = None,
    ) -> Path:
        """
        Generate complete Excel databook.

        Args:
            output_path: Path where Excel file will be saved
            normalized_df: Normalized GL DataFrame
            validation_result: Validation result object
            processing_report: Processing report from ingestion
            source_files: List of source file names (optional)
            entity: Entity name (optional)

        Returns:
            Path to generated Excel file
        """
        output_path = Path(output_path)
        self.workbook_path = output_path

        # Create workbook
        self.workbook = xlsxwriter.Workbook(str(output_path))

        # Create formats
        self._create_formats()

        # Apply mapping if provided
        gl_df_with_mapping = normalized_df.copy()
        if mapping_df is not None and not mapping_df.empty:
            from app.core.mapping import GLAccountMapper
            mapper = GLAccountMapper()
            gl_df_with_mapping = mapper.apply_mapping(normalized_df, mapping_df)

        # Create tabs in order
        self._create_readme_tab(source_files or [], entity)
        self._create_validation_tab(
            validation_result, 
            processing_report, 
            normalized_df, 
            source_files or [], 
            entity
        )
        self._create_gl_clean_tab(gl_df_with_mapping)
        self._create_mapping_tab(normalized_df, mapping_df)
        self._create_ebitda_tab(gl_df_with_mapping)
        self._create_pivots_inputs_tab(gl_df_with_mapping)
        
        # Adjustment tabs (if adjustment data provided)
        if adjustment_df is not None and not adjustment_df.empty:
            self._create_adjustments_tab(adjustment_df)
        if adjustment_log_df is not None and not adjustment_log_df.empty:
            self._create_adjustment_log_tab(adjustment_log_df)

        # Close workbook
        self.workbook.close()

        return output_path

    def _create_formats(self):
        """Create reusable cell formats"""
        # Header format
        self.header_format = self.workbook.add_format(ExcelStyles.get_header_format())

        # Body formats
        self.body_format = self.workbook.add_format(
            ExcelStyles.get_table_banding_format(is_even=False)
        )
        self.body_format_even = self.workbook.add_format(
            ExcelStyles.get_table_banding_format(is_even=True)
        )

        # Status formats
        self.pass_format = self.workbook.add_format(
            ExcelStyles.get_status_format("PASS")
        )
        self.fail_format = self.workbook.add_format(
            ExcelStyles.get_status_format("FAIL")
        )

        # Number formats
        self.currency_format = self.workbook.add_format(
            ExcelStyles.get_currency_format_dict()
        )
        self.date_format = self.workbook.add_format(
            ExcelStyles.get_date_format_dict()
        )
        self.integer_format = self.workbook.add_format(
            {"num_format": ExcelStyles.INTEGER_FORMAT}
        )
        self.decimal_format = self.workbook.add_format(
            {"num_format": ExcelStyles.DECIMAL_FORMAT}
        )

        # Title format
        self.title_format = self.workbook.add_format(
            {
                "font_name": ExcelStyles.HEADER_FONT,
                "font_size": 14,
                "bold": True,
                "align": "left",
            }
        )

    def _create_readme_tab(
        self, source_files: List[str], entity: Optional[str]
    ):
        """Create README tab with instructions and metadata"""
        worksheet = self.workbook.add_worksheet("README")

        row = 0

        # Title
        worksheet.write(row, 0, "GL Databook - User Guide", self.title_format)
        row += 2

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet.write(row, 0, f"Generated: {timestamp}")
        row += 1

        # Entity
        if entity:
            worksheet.write(row, 0, f"Entity: {entity}")
            row += 1

        # Source files
        if source_files:
            worksheet.write(row, 0, "Source Files:")
            row += 1
            for source_file in source_files:
                worksheet.write(row, 1, f"- {source_file}")
                row += 1
            row += 1

        # Instructions
        instructions = [
            "TAB DESCRIPTIONS:",
            "",
            "1. README - This tab. Contains metadata and instructions.",
            "",
            "2. Validation - Shows validation results including PASS/FAIL status, "
            "debit/credit totals, and row counts removed during processing.",
            "",
            "3. GL_Clean - Clean transaction table with all normalized GL entries. "
            "Formatted as Excel Table with filters enabled.",
            "",
            "4. Mapping - Unique account list with mapping columns for categorization. "
            "Use this tab to map accounts to standard categories.",
            "",
            "5. EBITDA - Financial calculations including Net Income, EBITDA, "
            "and Adjusted EBITDA. Formulas are used for calculations.",
            "",
            "6. Pivots_Inputs - Pivot-ready table for creating custom pivot tables "
            "and analysis.",
            "",
            "USAGE NOTES:",
            "",
            "- All tabs have frozen top rows and filters enabled where applicable.",
            "- Use Excel Tables (GL_Clean, Mapping) for easy sorting and filtering.",
            "- EBITDA calculations use formulas - recalculate if data changes.",
            "- For better performance with large files, formulas can be broken "
            "(converted to values) using the break_formulas option.",
        ]

        for instruction in instructions:
            worksheet.write(row, 0, instruction)
            row += 1

        # Set column widths
        worksheet.set_column(0, 0, 80)

    def _create_validation_tab(
        self,
        validation_result: ValidationResult,
        processing_report: ProcessingReport,
        normalized_df: pd.DataFrame,
        source_files: List[str],
        entity: Optional[str] = None,
    ):
        """Create Validation tab with PASS/FAIL and metrics"""
        worksheet = self.workbook.add_worksheet("Validation")

        row = 0

        # Title
        worksheet.write(row, 0, "Validation Results", self.title_format)
        row += 2

        # ========================================================================
        # SUMMARY SECTION
        # ========================================================================
        worksheet.write(row, 0, "Summary", self.title_format)
        row += 1

        # Create summary data
        summary_data = []
        
        # Validation Status
        status_format = (
            self.pass_format if validation_result.is_valid() else self.fail_format
        )
        summary_data.append(("Validation Status", validation_result.status.value, status_format))
        
        # Generated Timestamp
        generated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_data.append(("Generated Timestamp", generated_time, self.body_format))
        
        # Source Files
        if source_files:
            source_files_str = ", ".join(source_files) if len(source_files) <= 3 else f"{len(source_files)} files"
            summary_data.append(("Source File(s)", source_files_str, self.body_format))
        else:
            summary_data.append(("Source File(s)", "Not specified", self.body_format))
        
        # Entity Names
        if not normalized_df.empty and "entity" in normalized_df.columns:
            entities = normalized_df["entity"].unique().tolist()
            if len(entities) == 1:
                entity_name = entities[0]
            else:
                entity_name = ", ".join(entities) if len(entities) <= 3 else f"{len(entities)} entities"
            summary_data.append(("Entity Name(s)", entity_name, self.body_format))
        elif entity:
            summary_data.append(("Entity Name(s)", entity, self.body_format))
        else:
            summary_data.append(("Entity Name(s)", "Not specified", self.body_format))
        
        # Transaction Count
        transaction_count = len(normalized_df) if not normalized_df.empty else 0
        summary_data.append(("Transaction Count", transaction_count, self.integer_format))
        
        # Date Range
        if not normalized_df.empty and "date" in normalized_df.columns:
            date_col = normalized_df["date"]
            valid_dates = date_col.dropna()
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                date_range_str = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
                summary_data.append(("Date Range", date_range_str, self.body_format))
            else:
                summary_data.append(("Date Range", "No valid dates", self.body_format))
        else:
            summary_data.append(("Date Range", "N/A", self.body_format))
        
        # Total Debits
        metrics = validation_result.key_metrics
        total_debits = metrics.get("total_debits", 0.0)
        summary_data.append(("Total Debits", total_debits, self.currency_format))
        
        # Total Credits
        total_credits = metrics.get("total_credits", 0.0)
        summary_data.append(("Total Credits", total_credits, self.currency_format))
        
        # Difference
        difference = metrics.get("debit_credit_difference", 0.0)
        diff_format = self.currency_format
        if difference > 0.01:  # Highlight if not balanced
            diff_format = self.workbook.add_format({
                **ExcelStyles.get_currency_format_dict(),
                "font_color": ExcelStyles._rgb_to_hex(ExcelStyles.ERROR_RED),
                "bold": True,
            })
        summary_data.append(("Debit/Credit Difference", difference, diff_format))
        
        # Write summary data
        summary_headers = ["Field", "Value"]
        for col, header in enumerate(summary_headers):
            worksheet.write(row, col, header, self.header_format)
        row += 1
        
        for summary_row in summary_data:
            worksheet.write(row, 0, summary_row[0], self.body_format)
            if len(summary_row) > 2:
                worksheet.write(row, 1, summary_row[1], summary_row[2])
            else:
                worksheet.write(row, 1, summary_row[1], self.body_format)
            row += 1
        
        row += 2

        # Key Metrics
        worksheet.write(row, 0, "Key Metrics", self.title_format)
        row += 1

        # Headers
        headers = ["Metric", "Value"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.header_format)
        row += 1

        # Metrics data
        metrics = validation_result.key_metrics
        metrics_data = [
            ("Total Transactions", metrics.get("total_transactions", 0)),
            (
                "Total Debits",
                metrics.get("total_debits", 0),
                self.currency_format,
            ),
            (
                "Total Credits",
                metrics.get("total_credits", 0),
                self.currency_format,
            ),
            (
                "Debit/Credit Difference",
                metrics.get("debit_credit_difference", 0),
                self.currency_format,
            ),
            (
                "Date Parse Failure Rate",
                metrics.get("date_parse_failure_rate", 0),
                self.workbook.add_format(ExcelStyles.get_percentage_format_dict()),
            ),
        ]

        for metric_row in metrics_data:
            worksheet.write(row, 0, metric_row[0], self.body_format)
            if len(metric_row) > 2:
                worksheet.write(row, 1, metric_row[1], metric_row[2])
            else:
                worksheet.write(row, 1, metric_row[1], self.body_format)
            row += 1

        row += 1

        # Processing Report
        worksheet.write(row, 0, "Processing Report", self.title_format)
        row += 1

        # Headers
        headers = ["Item", "Count"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.header_format)
        row += 1

        # Processing data
        processing_data = [
            ("Total Rows Read", processing_report.total_rows_read),
            (
                "Rows with Invalid Dates",
                processing_report.rows_with_invalid_dates,
            ),
            ("Rows Removed (Totals)", processing_report.rows_removed_totals),
            (
                "Rows Removed (Subtotals)",
                processing_report.rows_removed_subtotals,
            ),
            (
                "Rows Removed (Opening Balance)",
                processing_report.rows_removed_opening_balance,
            ),
            ("Final Transaction Rows", processing_report.final_transaction_rows),
        ]

        for proc_row in processing_data:
            worksheet.write(row, 0, proc_row[0], self.body_format)
            worksheet.write(row, 1, proc_row[1], self.integer_format)
            row += 1

        row += 1

        # Errors
        if validation_result.errors:
            worksheet.write(row, 0, "Errors", self.title_format)
            row += 1
            for error in validation_result.errors:
                error_format = self.workbook.add_format(
                    {
                        "font_color": ExcelStyles._rgb_to_hex(ExcelStyles.ERROR_RED),
                        "text_wrap": True,  # Enable text wrapping for multi-line messages
                        "valign": "top",  # Align to top for multi-line text
                    }
                )
                worksheet.write(row, 0, error, error_format)  # Remove bullet, already in message
                worksheet.set_row(row, None, None, {"hidden": False, "height": None})  # Auto-height
                row += 1
            row += 1

        # Warnings
        if validation_result.warnings:
            worksheet.write(row, 0, "Warnings", self.title_format)
            row += 1
            for warning in validation_result.warnings:
                warning_format = self.workbook.add_format(
                    {
                        "font_color": ExcelStyles._rgb_to_hex(
                            ExcelStyles.WARNING_YELLOW
                        ),
                        "text_wrap": True,  # Enable text wrapping for multi-line messages
                        "valign": "top",  # Align to top for multi-line text
                    }
                )
                worksheet.write(row, 0, warning, warning_format)  # Remove bullet, already in message
                worksheet.set_row(row, None, None, {"hidden": False, "height": None})  # Auto-height
                row += 1

        # Set column widths
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 20)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_gl_clean_tab(self, normalized_df: pd.DataFrame):
        """Create GL_Clean tab with Excel Table formatting"""
        worksheet = self.workbook.add_worksheet("GL_Clean")

        if normalized_df.empty:
            worksheet.write(0, 0, "No data available")
            return

        # Write headers
        headers = list(normalized_df.columns)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, self.header_format)

        # Write data
        for row_idx, (_, df_row) in enumerate(normalized_df.iterrows(), start=1):
            is_even = row_idx % 2 == 0
            row_format = self.body_format_even if is_even else self.body_format

            for col_idx, value in enumerate(df_row):
                # Apply appropriate format based on column type
                cell_format = row_format
                if headers[col_idx] == "date":
                    if pd.notna(value):
                        worksheet.write_datetime(
                            row_idx, col_idx, value, self.date_format
                        )
                    else:
                        worksheet.write(row_idx, col_idx, "", cell_format)
                elif headers[col_idx] in ["debit", "credit", "amount_net"]:
                    worksheet.write(row_idx, col_idx, float(value), self.currency_format)
                elif headers[col_idx] == "row_id":
                    worksheet.write(row_idx, col_idx, int(value), self.integer_format)
                else:
                    worksheet.write(row_idx, col_idx, str(value), cell_format)

        # Create Excel Table
        table_range = f"A1:{self._get_column_letter(len(headers))}{len(normalized_df) + 1}"
        worksheet.add_table(
            0,
            0,
            len(normalized_df),
            len(headers) - 1,
            {
                "columns": [{"header": header} for header in headers],
                "style": "Table Style Medium 9",  # Light blue banding style
                "first_column": False,
                "banded_rows": True,
                "banded_columns": False,
            },
        )

        # Set column widths
        worksheet.set_column(0, len(headers) - 1, 15)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_mapping_tab(
        self,
        normalized_df: pd.DataFrame,
        existing_mapping_df: Optional[pd.DataFrame] = None,
    ):
        """Create Mapping tab with unique accounts and mapping columns"""
        worksheet = self.workbook.add_worksheet("Mapping")

        if normalized_df.empty:
            worksheet.write(0, 0, "No data available")
            return

        # Extract unique accounts using mapper
        from app.core.mapping import GLAccountMapper

        mapper = GLAccountMapper()
        unique_accounts_df = mapper.extract_unique_accounts(normalized_df)

        # Create mapping template
        mapping_df = mapper.create_mapping_template(
            unique_accounts_df, existing_mapping_df
        )

        # Prepare columns for Excel
        # Include entity if present
        excel_columns = ["account_name_flat"]
        if "entity" in mapping_df.columns:
            excel_columns.append("entity")
        excel_columns.extend(
            ["account_name_raw", "main_category", "sub1", "sub2", "client_specific", "notes"]
        )

        # Select and reorder columns
        mapping_df_display = mapping_df[excel_columns].copy()

        # Rename for display
        display_names = {
            "account_name_flat": "Account Name (Flat)",
            "account_name_raw": "Account Name (Raw)",
            "main_category": "Main Category",
            "sub1": "Sub1",
            "sub2": "Sub2",
            "client_specific": "Client Specific",
            "notes": "Notes",
        }
        if "entity" in mapping_df_display.columns:
            display_names["entity"] = "Entity"

        mapping_df_display = mapping_df_display.rename(columns=display_names)

        # Write headers
        headers = list(mapping_df_display.columns)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, self.header_format)

        # Write data
        for row_idx, (_, df_row) in enumerate(mapping_df_display.iterrows(), start=1):
            is_even = row_idx % 2 == 0
            row_format = self.body_format_even if is_even else self.body_format

            for col_idx, value in enumerate(df_row):
                worksheet.write(row_idx, col_idx, str(value), row_format)

        # Create Excel Table
        worksheet.add_table(
            0,
            0,
            len(mapping_df_display),
            len(headers) - 1,
            {
                "columns": [{"header": header} for header in headers],
                "style": "Table Style Medium 9",
                "first_column": False,
                "banded_rows": True,
                "banded_columns": False,
            },
        )

        # Set column widths
        col_widths = {
            "Account Name (Flat)": 40,
            "Entity": 20,
            "Account Name (Raw)": 40,
            "Main Category": 20,
            "Sub1": 20,
            "Sub2": 20,
            "Client Specific": 25,
            "Notes": 30,
        }

        for col_idx, header in enumerate(headers):
            width = col_widths.get(header, 15)
            worksheet.set_column(col_idx, col_idx, width)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_ebitda_tab(self, normalized_df: pd.DataFrame):
        """Create EBITDA tab with formula-based calculations using mapped categories"""
        worksheet = self.workbook.add_worksheet("EBITDA")

        row = 0

        # Title
        worksheet.write(row, 0, "EBITDA Calculations", self.title_format)
        row += 2

        # Headers
        headers = ["Item", "Amount"]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.header_format)
        row += 1

        # Find column indices in GL_Clean tab
        # Standard columns: date, account_name_raw, account_name_flat, description, debit, credit, amount_net
        # Plus metadata: entity, source_system, gl_source_file, row_id
        # Plus mapping columns if applied: main_category, sub1, sub2, client_specific, notes
        
        # Determine if mapping is available
        has_mapping = "main_category" in normalized_df.columns if not normalized_df.empty else False
        
        # Find column letters for key columns
        # We'll use a helper to find the column index
        def find_column_index(df, column_name):
            """Find 0-based column index, returns None if not found"""
            if column_name in df.columns:
                return list(df.columns).index(column_name)
            return None
        
        # Get column indices
        main_category_col_idx = find_column_index(normalized_df, "main_category") if not normalized_df.empty else None
        debit_col_idx = find_column_index(normalized_df, "debit") if not normalized_df.empty else None
        amount_net_col_idx = find_column_index(normalized_df, "amount_net") if not normalized_df.empty else None
        
        # Convert to Excel column letters (1-based)
        def col_letter(idx):
            """Convert 0-based index to Excel column letter (1-based)"""
            if idx is None:
                return None
            return self._get_column_letter(idx + 1)  # +1 because Excel is 1-based
        
        main_category_col = col_letter(main_category_col_idx)
        debit_col = col_letter(debit_col_idx) if debit_col_idx is not None else "I"  # Default to I if not found
        amount_col = col_letter(amount_net_col_idx) if amount_net_col_idx is not None else debit_col
        
        # Calculate values if breaking formulas
        revenue_value = 0.0
        cogs_value = 0.0
        op_exp_value = 0.0
        interest_value = 0.0
        tax_value = 0.0
        da_value = 0.0

        if self.break_formulas or normalized_df.empty:
            # Calculate actual values from DataFrame using mapped categories if available
            if not normalized_df.empty:
                if has_mapping and "main_category" in normalized_df.columns:
                    # Use mapped categories
                    # Revenue: Credits - Debits (income increases credit side)
                    revenue_df = normalized_df[normalized_df["main_category"] == "Revenue"]
                    revenue_value = float(revenue_df["credit"].sum() - revenue_df["debit"].sum()) if not revenue_df.empty else 0.0
                    
                    # COGS: Debits - Credits (expenses increase debit side)
                    cogs_df = normalized_df[normalized_df["main_category"] == "COGS"]
                    cogs_value = float(cogs_df["debit"].sum() - cogs_df["credit"].sum()) if not cogs_df.empty else 0.0
                    
                    # OpEx: Debits - Credits
                    op_exp_df = normalized_df[normalized_df["main_category"] == "OpEx"]
                    op_exp_value = float(op_exp_df["debit"].sum() - op_exp_df["credit"].sum()) if not op_exp_df.empty else 0.0
                    
                    # Interest: Debits - Credits
                    interest_df = normalized_df[normalized_df["main_category"] == "Interest"]
                    interest_value = float(interest_df["debit"].sum() - interest_df["credit"].sum()) if not interest_df.empty else 0.0
                    
                    # Taxes: Debits - Credits
                    tax_df = normalized_df[normalized_df["main_category"] == "Taxes"]
                    tax_value = float(tax_df["debit"].sum() - tax_df["credit"].sum()) if not tax_df.empty else 0.0
                    
                    # D&A: Debits - Credits
                    da_df = normalized_df[normalized_df["main_category"] == "D&A"]
                    da_value = float(da_df["debit"].sum() - da_df["credit"].sum()) if not da_df.empty else 0.0
                else:
                    # Fallback to text matching if no mapping
                    # Revenue: Credits - Debits
                    revenue_df = normalized_df[
                        normalized_df["account_name_flat"].str.contains("Revenue", case=False, na=False)
                    ] if "account_name_flat" in normalized_df.columns else pd.DataFrame()
                    revenue_value = float(revenue_df["credit"].sum() - revenue_df["debit"].sum()) if not revenue_df.empty else 0.0
                    
                    # COGS: Debits - Credits
                    cogs_df = normalized_df[
                        normalized_df["account_name_flat"].str.contains("COGS", case=False, na=False)
                    ] if "account_name_flat" in normalized_df.columns else pd.DataFrame()
                    cogs_value = float(cogs_df["debit"].sum() - cogs_df["credit"].sum()) if not cogs_df.empty else 0.0
                    
                    # OpEx: Debits - Credits
                    op_exp_df = normalized_df[
                        normalized_df["account_name_flat"].str.contains("Expense", case=False, na=False)
                    ] if "account_name_flat" in normalized_df.columns else pd.DataFrame()
                    op_exp_value = float(op_exp_df["debit"].sum() - op_exp_df["credit"].sum()) if not op_exp_df.empty else 0.0

        # Revenue - use mapped category if available, otherwise fallback to text matching
        # Revenue is typically credits, so we use credit - debit (or negative amount_net)
        credit_col = col_letter(find_column_index(normalized_df, "credit")) if not normalized_df.empty else "H"
        debit_col_for_rev = col_letter(find_column_index(normalized_df, "debit")) if not normalized_df.empty else "G"
        
        if has_mapping and main_category_col:
            # Use SUMIFS: Revenue = Credits - Debits for revenue accounts
            revenue_formula = f'=SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"Revenue")-SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"Revenue")'
        else:
            # Fallback to text matching on account name
            account_col = col_letter(find_column_index(normalized_df, "account_name_flat")) if not normalized_df.empty else "G"
            revenue_formula = f'=SUMIF(GL_Clean!{account_col}:{account_col},"*Revenue*",GL_Clean!{credit_col}:{credit_col})-SUMIF(GL_Clean!{account_col}:{account_col},"*Revenue*",GL_Clean!{debit_col_for_rev}:{debit_col_for_rev})'
        
        worksheet.write(row, 0, "Revenue", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, revenue_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, revenue_formula, self.currency_format)
        revenue_row = row
        row += 1

        # COGS (Cost of Goods Sold) - typically debits
        if has_mapping and main_category_col:
            cogs_formula = f'=SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"COGS")-SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"COGS")'
        else:
            account_col = col_letter(find_column_index(normalized_df, "account_name_flat")) if not normalized_df.empty else "G"
            cogs_formula = f'=SUMIF(GL_Clean!{account_col}:{account_col},"*COGS*",GL_Clean!{debit_col_for_rev}:{debit_col_for_rev})-SUMIF(GL_Clean!{account_col}:{account_col},"*COGS*",GL_Clean!{credit_col}:{credit_col})'
        
        worksheet.write(row, 0, "Cost of Goods Sold", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, cogs_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, cogs_formula, self.currency_format)
        cogs_row = row
        row += 1

        # Gross Profit
        gross_profit_formula = f"=B{revenue_row + 1}-B{cogs_row + 1}"
        worksheet.write(row, 0, "Gross Profit", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, revenue_value - cogs_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, gross_profit_formula, self.currency_format)
        gp_row = row
        row += 1

        # Operating Expenses - typically debits
        if has_mapping and main_category_col:
            op_exp_formula = f'=SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"OpEx")-SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"OpEx")'
        else:
            account_col = col_letter(find_column_index(normalized_df, "account_name_flat")) if not normalized_df.empty else "G"
            op_exp_formula = f'=SUMIF(GL_Clean!{account_col}:{account_col},"*Expense*",GL_Clean!{debit_col_for_rev}:{debit_col_for_rev})-SUMIF(GL_Clean!{account_col}:{account_col},"*Expense*",GL_Clean!{credit_col}:{credit_col})'
        
        worksheet.write(row, 0, "Operating Expenses", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, op_exp_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, op_exp_formula, self.currency_format)
        op_exp_row = row
        row += 1

        # EBITDA
        ebitda_formula = f"=B{gp_row + 1}-B{op_exp_row + 1}"
        worksheet.write(row, 0, "EBITDA", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, (revenue_value - cogs_value) - op_exp_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, ebitda_formula, self.currency_format)
        ebitda_row = row
        row += 1

        # Interest Expense (if mapped) - typically debits
        if has_mapping and main_category_col:
            interest_formula = f'=SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"Interest")-SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"Interest")'
            worksheet.write(row, 0, "Interest Expense", self.body_format)
            if self.break_formulas:
                worksheet.write(row, 1, interest_value, self.currency_format)
            else:
                worksheet.write_formula(row, 1, interest_formula, self.currency_format)
            interest_row = row
            row += 1

        # Taxes (if mapped) - typically debits
        if has_mapping and main_category_col:
            tax_formula = f'=SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"Taxes")-SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"Taxes")'
            worksheet.write(row, 0, "Taxes", self.body_format)
            if self.break_formulas:
                worksheet.write(row, 1, tax_value, self.currency_format)
            else:
                worksheet.write_formula(row, 1, tax_formula, self.currency_format)
            tax_row = row
            row += 1

        # D&A (Depreciation & Amortization, if mapped) - typically debits
        if has_mapping and main_category_col:
            da_formula = f'=SUMIFS(GL_Clean!{debit_col_for_rev}:{debit_col_for_rev},GL_Clean!{main_category_col}:{main_category_col},"D&A")-SUMIFS(GL_Clean!{credit_col}:{credit_col},GL_Clean!{main_category_col}:{main_category_col},"D&A")'
            worksheet.write(row, 0, "Depreciation & Amortization", self.body_format)
            if self.break_formulas:
                worksheet.write(row, 1, da_value, self.currency_format)
            else:
                worksheet.write_formula(row, 1, da_formula, self.currency_format)
            da_row = row
            row += 1

        # Net Income
        if has_mapping and main_category_col and 'interest_row' in locals():
            # Net Income = Revenue - COGS - OpEx - Interest - Taxes
            net_income_formula = f"=B{revenue_row + 1}-B{cogs_row + 1}-B{op_exp_row + 1}-B{interest_row + 1}-B{tax_row + 1}"
            net_income_calc = revenue_value - cogs_value - op_exp_value - interest_value - tax_value
        else:
            # Simplified: Revenue - Expenses
            net_income_formula = f"=B{revenue_row + 1}-B{op_exp_row + 1}"
            net_income_calc = revenue_value - op_exp_value
        
        worksheet.write(row, 0, "Net Income", self.body_format)
        if self.break_formulas:
            worksheet.write(row, 1, net_income_calc, self.currency_format)
        else:
            worksheet.write_formula(row, 1, net_income_formula, self.currency_format)
        net_income_row = row
        row += 1

        # Adjusted EBITDA (EBITDA + adjustments, placeholder for now)
        adj_ebitda_formula = f"=B{ebitda_row + 1}"
        worksheet.write(row, 0, "Adjusted EBITDA", self.body_format)
        if self.break_formulas:
            adj_ebitda_value = (revenue_value - cogs_value) - op_exp_value
            worksheet.write(row, 1, adj_ebitda_value, self.currency_format)
        else:
            worksheet.write_formula(row, 1, adj_ebitda_formula, self.currency_format)

        # Set column widths
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 20)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_pivots_inputs_tab(self, normalized_df: pd.DataFrame):
        """Create Pivots_Inputs tab with pivot-ready data"""
        worksheet = self.workbook.add_worksheet("Pivots_Inputs")

        if normalized_df.empty:
            worksheet.write(0, 0, "No data available")
            return

        # Create pivot-ready DataFrame (add calculated columns if needed)
        pivot_df = normalized_df.copy()

        # Add month/year columns for easier pivoting
        if "date" in pivot_df.columns:
            pivot_df["Year"] = pivot_df["date"].dt.year
            pivot_df["Month"] = pivot_df["date"].dt.month
            pivot_df["Month_Name"] = pivot_df["date"].dt.strftime("%B")
            pivot_df["Quarter"] = pivot_df["date"].dt.quarter

        # Write headers
        headers = list(pivot_df.columns)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, self.header_format)

        # Write data
        for row_idx, (_, df_row) in enumerate(pivot_df.iterrows(), start=1):
            is_even = row_idx % 2 == 0
            row_format = self.body_format_even if is_even else self.body_format

            for col_idx, value in enumerate(df_row):
                if pd.isna(value):
                    worksheet.write(row_idx, col_idx, "", row_format)
                elif headers[col_idx] == "date":
                    worksheet.write_datetime(row_idx, col_idx, value, self.date_format)
                elif headers[col_idx] in ["debit", "credit", "amount_net"]:
                    worksheet.write(row_idx, col_idx, float(value), self.currency_format)
                elif headers[col_idx] in ["Year", "Month", "Quarter"]:
                    worksheet.write(row_idx, col_idx, int(value), self.integer_format)
                else:
                    worksheet.write(row_idx, col_idx, str(value), row_format)

        # Create Excel Table
        worksheet.add_table(
            0,
            0,
            len(pivot_df),
            len(headers) - 1,
            {
                "columns": [{"header": header} for header in headers],
                "style": "Table Style Medium 9",
                "first_column": False,
                "banded_rows": True,
                "banded_columns": False,
            },
        )

        # Set column widths
        for col_idx in range(len(headers)):
            worksheet.set_column(col_idx, col_idx, 15)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_adjustments_tab(self, adjustment_df: pd.DataFrame):
        """Create Adjustments tab with transactions that have adjustments"""
        worksheet = self.workbook.add_worksheet("Adjustments")

        if adjustment_df.empty:
            worksheet.write(0, 0, "No adjustments found")
            return

        # Filter to only rows with adjustments
        adjusted_rows = adjustment_df[adjustment_df["adjustment_flag"] == True].copy()

        if adjusted_rows.empty:
            worksheet.write(0, 0, "No adjustments found")
            return

        # Select relevant columns for display
        display_cols = [
            "date",
            "entity",
            "account_name_flat",
            "description",
            "debit",
            "credit",
            "amount_net",
            "adjustment_category",
            "adjustment_amount",
            "add_back",
            "reasoning",
        ]

        # Filter to columns that exist
        available_cols = [col for col in display_cols if col in adjusted_rows.columns]
        display_df = adjusted_rows[available_cols].copy()

        # Rename for display
        display_names = {
            "date": "Date",
            "entity": "Entity",
            "account_name_flat": "Account",
            "description": "Description",
            "debit": "Debit",
            "credit": "Credit",
            "amount_net": "Amount",
            "adjustment_category": "Adjustment Category",
            "adjustment_amount": "Adjustment Amount",
            "add_back": "Add Back",
            "reasoning": "Reasoning",
        }
        display_df = display_df.rename(columns=display_names)

        # Write headers
        headers = list(display_df.columns)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, self.header_format)

        # Write data
        for row_idx, (_, df_row) in enumerate(display_df.iterrows(), start=1):
            is_even = row_idx % 2 == 0
            row_format = self.body_format_even if is_even else self.body_format

            for col_idx, value in enumerate(df_row):
                header_name = headers[col_idx]
                if header_name == "Date":
                    if pd.notna(value):
                        worksheet.write_datetime(
                            row_idx, col_idx, value, self.date_format
                        )
                    else:
                        worksheet.write(row_idx, col_idx, "", row_format)
                elif header_name in ["Debit", "Credit", "Amount", "Adjustment Amount"]:
                    worksheet.write(row_idx, col_idx, float(value), self.currency_format)
                elif header_name == "Add Back":
                    worksheet.write(row_idx, col_idx, "Yes" if value else "No", row_format)
                else:
                    worksheet.write(row_idx, col_idx, str(value), row_format)

        # Create Excel Table
        worksheet.add_table(
            0,
            0,
            len(display_df),
            len(headers) - 1,
            {
                "columns": [{"header": header} for header in headers],
                "style": "Table Style Medium 9",
                "first_column": False,
                "banded_rows": True,
                "banded_columns": False,
            },
        )

        # Set column widths
        col_widths = {
            "Date": 12,
            "Entity": 20,
            "Account": 30,
            "Description": 40,
            "Debit": 15,
            "Credit": 15,
            "Amount": 15,
            "Adjustment Category": 25,
            "Adjustment Amount": 20,
            "Add Back": 12,
            "Reasoning": 50,
        }

        for col_idx, header in enumerate(headers):
            width = col_widths.get(header, 15)
            worksheet.set_column(col_idx, col_idx, width)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _create_adjustment_log_tab(self, adjustment_log_df: pd.DataFrame):
        """Create Adjustment_Log tab with detailed adjustment information"""
        worksheet = self.workbook.add_worksheet("Adjustment_Log")

        if adjustment_log_df.empty:
            worksheet.write(0, 0, "No adjustment log entries")
            return

        # Write headers
        headers = list(adjustment_log_df.columns)
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, self.header_format)

        # Write data
        for row_idx, (_, df_row) in enumerate(adjustment_log_df.iterrows(), start=1):
            is_even = row_idx % 2 == 0
            row_format = self.body_format_even if is_even else self.body_format

            for col_idx, value in enumerate(df_row):
                header_name = headers[col_idx]
                if header_name == "date":
                    if pd.notna(value):
                        worksheet.write_datetime(
                            row_idx, col_idx, value, self.date_format
                        )
                    else:
                        worksheet.write(row_idx, col_idx, "", row_format)
                elif header_name == "adjustment_amount":
                    worksheet.write(row_idx, col_idx, float(value), self.currency_format)
                elif header_name == "add_back":
                    worksheet.write(row_idx, col_idx, "Yes" if value else "No", row_format)
                elif header_name == "row_id":
                    worksheet.write(row_idx, col_idx, int(value), self.integer_format)
                else:
                    worksheet.write(row_idx, col_idx, str(value), row_format)

        # Create Excel Table
        worksheet.add_table(
            0,
            0,
            len(adjustment_log_df),
            len(headers) - 1,
            {
                "columns": [{"header": header} for header in headers],
                "style": "Table Style Medium 9",
                "first_column": False,
                "banded_rows": True,
                "banded_columns": False,
            },
        )

        # Set column widths
        for col_idx in range(len(headers)):
            worksheet.set_column(col_idx, col_idx, 20)

        # Freeze top row
        worksheet.freeze_panes(1, 0)

    def _get_column_letter(self, col_num: int) -> str:
        """Convert column number to Excel column letter (1-based)"""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + (col_num % 26)) + result
            col_num //= 26
        return result

