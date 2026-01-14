"""
GL Account Mapping Module

Handles account mapping workflow: extraction, categorization, and application.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from app.core.validation import ValidationResult, ValidationStatus
from app.core.gl_ingestion import ProcessingReport


# Default chart-of-accounts categories
DEFAULT_CATEGORIES = [
    "Revenue",
    "COGS",
    "OpEx",
    "Other Income/Expense",
    "Taxes",
    "Interest",
    "D&A",
    "Balance Sheet",
]


@dataclass
class AccountMapping:
    """Account mapping configuration"""

    account_name_flat: str
    main_category: str = ""
    sub1: str = ""
    sub2: str = ""
    client_specific: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            "account_name_flat": self.account_name_flat,
            "main_category": self.main_category,
            "sub1": self.sub1,
            "sub2": self.sub2,
            "client_specific": self.client_specific,
            "notes": self.notes,
        }


class GLAccountMapper:
    """Mapper for GL account categorization"""

    def __init__(self, default_categories: Optional[List[str]] = None):
        """
        Initialize account mapper.

        Args:
            default_categories: List of default main categories (uses DEFAULT_CATEGORIES if None)
        """
        self.default_categories = default_categories or DEFAULT_CATEGORIES.copy()

    def extract_unique_accounts(
        self, normalized_df: pd.DataFrame, entity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract unique account list from normalized GL data.

        Args:
            normalized_df: Normalized GL DataFrame
            entity: Optional entity filter (if None, includes all entities)

        Returns:
            DataFrame with unique accounts and entity information
        """
        if normalized_df.empty:
            return pd.DataFrame(
                columns=[
                    "account_name_flat",
                    "account_name_raw",
                    "entity",
                    "transaction_count",
                ]
            )

        # Filter by entity if specified
        df_filtered = normalized_df.copy()
        if entity:
            df_filtered = df_filtered[df_filtered["entity"] == entity]

        # Get account column
        account_col = (
            "account_name_flat"
            if "account_name_flat" in df_filtered.columns
            else "account_name_raw"
        )

        # Group by account and entity to get unique accounts
        account_summary = (
            df_filtered.groupby([account_col, "entity"])
            .agg(
                {
                    "account_name_raw": "first",
                    "row_id": "count",  # Count transactions
                }
            )
            .reset_index()
        )

        account_summary.columns = [
            "account_name_flat",
            "entity",
            "account_name_raw",
            "transaction_count",
        ]

        # Sort by entity and account name
        account_summary = account_summary.sort_values(
            ["entity", "account_name_flat"]
        ).reset_index(drop=True)

        return account_summary

    def create_mapping_template(
        self,
        unique_accounts_df: pd.DataFrame,
        existing_mapping: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Create mapping template DataFrame with required columns.

        Args:
            unique_accounts_df: DataFrame with unique accounts (from extract_unique_accounts)
            existing_mapping: Optional existing mapping DataFrame to merge with

        Returns:
            Mapping DataFrame with columns: account_name_flat, main_category, sub1, sub2,
            client_specific, notes
        """
        if unique_accounts_df.empty:
            return pd.DataFrame(
                columns=[
                    "account_name_flat",
                    "account_name_raw",
                    "entity",
                    "main_category",
                    "sub1",
                    "sub2",
                    "client_specific",
                    "notes",
                ]
            )

        # Create base mapping DataFrame
        mapping_df = unique_accounts_df[
            ["account_name_flat", "account_name_raw", "entity"]
        ].copy()

        # Add mapping columns
        mapping_df["main_category"] = ""
        mapping_df["sub1"] = ""
        mapping_df["sub2"] = ""
        mapping_df["client_specific"] = ""
        mapping_df["notes"] = ""

        # Merge with existing mapping if provided
        if existing_mapping is not None and not existing_mapping.empty:
            # Merge on account_name_flat and entity (if entity column exists)
            merge_cols = ["account_name_flat"]
            if "entity" in existing_mapping.columns and "entity" in mapping_df.columns:
                merge_cols.append("entity")

            mapping_df = mapping_df.merge(
                existing_mapping,
                on=merge_cols,
                how="left",
                suffixes=("", "_existing"),
            )

            # Fill in mapping columns from existing mapping
            for col in ["main_category", "sub1", "sub2", "client_specific", "notes"]:
                if f"{col}_existing" in mapping_df.columns:
                    # Use existing value if available, otherwise keep empty string
                    mapping_df[col] = mapping_df[f"{col}_existing"].fillna("")
                    mapping_df = mapping_df.drop(columns=[f"{col}_existing"])

        return mapping_df

    def apply_mapping(
        self,
        normalized_df: pd.DataFrame,
        mapping_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Apply mapping to normalized GL DataFrame.

        Args:
            normalized_df: Normalized GL DataFrame
            mapping_df: Mapping DataFrame with account_name_flat and mapping columns

        Returns:
            DataFrame with mapping columns added
        """
        if normalized_df.empty:
            return normalized_df.copy()

        # Merge mapping onto normalized data
        merge_cols = ["account_name_flat"]
        if "entity" in mapping_df.columns and "entity" in normalized_df.columns:
            merge_cols.append("entity")

        # Select only mapping columns to merge
        mapping_cols = [
            "account_name_flat",
            "main_category",
            "sub1",
            "sub2",
            "client_specific",
            "notes",
        ]
        if "entity" in mapping_df.columns:
            mapping_cols.insert(1, "entity")

        mapping_to_merge = mapping_df[mapping_cols].copy()

        # Merge
        result_df = normalized_df.merge(
            mapping_to_merge,
            on=merge_cols,
            how="left",
        )

        # Fill empty mapping values with empty strings
        for col in ["main_category", "sub1", "sub2", "client_specific", "notes"]:
            if col in result_df.columns:
                result_df[col] = result_df[col].fillna("")

        return result_df

    def suggest_category(
        self, account_name: str, mapping_df: Optional[pd.DataFrame] = None
    ) -> Optional[str]:
        """
        Suggest main category based on account name patterns.

        Args:
            account_name: Account name to categorize
            mapping_df: Optional existing mapping to check for similar accounts

        Returns:
            Suggested category or None
        """
        account_lower = account_name.lower()

        # Pattern matching for category suggestions
        patterns = {
            "Revenue": [
                "revenue",
                "sales",
                "income",
                "fees",
                "service",
                "product",
            ],
            "COGS": [
                "cost of goods",
                "cogs",
                "cost of sales",
                "direct cost",
                "material",
            ],
            "OpEx": [
                "expense",
                "operating",
                "admin",
                "general",
                "salary",
                "rent",
                "utilities",
            ],
            "Interest": ["interest", "financing", "loan"],
            "Taxes": ["tax", "taxes"],
            "D&A": ["depreciation", "amortization", "d&a", "d and a"],
            "Balance Sheet": [
                "asset",
                "liability",
                "equity",
                "cash",
                "account receivable",
                "account payable",
            ],
        }

        # Check patterns
        for category, pattern_list in patterns.items():
            if any(pattern in account_lower for pattern in pattern_list):
                return category

        # Check existing mapping for similar accounts
        if mapping_df is not None and not mapping_df.empty:
            # Find accounts with similar names
            similar = mapping_df[
                mapping_df["account_name_flat"].str.contains(
                    account_name[:10], case=False, na=False
                )
            ]
            if not similar.empty and "main_category" in similar.columns:
                # Return most common category for similar accounts
                categories = similar["main_category"].value_counts()
                if not categories.empty:
                    return categories.index[0]

        return None

    def get_default_categories(self) -> List[str]:
        """Get list of default categories"""
        return self.default_categories.copy()
    
    def auto_map_accounts(
        self, normalized_df: pd.DataFrame, entity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Automatically generate mapping for all accounts based on pattern matching.
        
        Args:
            normalized_df: Normalized GL DataFrame
            entity: Optional entity filter (if None, includes all entities)
            
        Returns:
            DataFrame with automatic mapping applied (main_category filled based on patterns)
        """
        if normalized_df.empty:
            return normalized_df.copy()
        
        # Extract unique accounts
        unique_accounts_df = self.extract_unique_accounts(normalized_df, entity)
        
        if unique_accounts_df.empty:
            return normalized_df.copy()
        
        # Create mapping with automatic category suggestions
        mapping_df = self.create_mapping_template(unique_accounts_df)
        
        # Apply automatic category suggestions
        for idx, row in mapping_df.iterrows():
            account_name = row["account_name_flat"]
            if pd.isna(account_name) or account_name == "":
                continue
                
            # Get automatic suggestion
            suggested_category = self.suggest_category(account_name, mapping_df)
            if suggested_category:
                mapping_df.at[idx, "main_category"] = suggested_category
        
        # Apply mapping to normalized data
        mapped_df = self.apply_mapping(normalized_df, mapping_df)
        
        return mapped_df
    
    def generate_auto_mapping_df(
        self, normalized_df: pd.DataFrame, entity: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generate a mapping DataFrame with automatic category suggestions.
        This can be used separately from applying the mapping.
        
        Args:
            normalized_df: Normalized GL DataFrame
            entity: Optional entity filter
            
        Returns:
            Mapping DataFrame with automatic main_category suggestions
        """
        # Extract unique accounts
        unique_accounts_df = self.extract_unique_accounts(normalized_df, entity)
        
        if unique_accounts_df.empty:
            return pd.DataFrame(columns=[
                "account_name_flat", "main_category", "sub1", "sub2", 
                "client_specific", "notes"
            ])
        
        # Create mapping template
        mapping_df = self.create_mapping_template(unique_accounts_df)
        
        # Apply automatic category suggestions
        for idx, row in mapping_df.iterrows():
            account_name = row["account_name_flat"]
            if pd.isna(account_name) or account_name == "":
                continue
                
            # Get automatic suggestion
            suggested_category = self.suggest_category(account_name, mapping_df)
            if suggested_category:
                mapping_df.at[idx, "main_category"] = suggested_category
        
        return mapping_df


class MultiEntityProcessor:
    """Processor for handling multiple GL files from different entities"""

    def __init__(self):
        """Initialize multi-entity processor"""
        pass

    def process_multiple_files(
        self,
        file_entity_pairs: List[Tuple[str, str]],
        source_system: str = "QuickBooks",
    ) -> Tuple[pd.DataFrame, List[ProcessingReport], ValidationResult]:
        """
        Process multiple GL files, one per entity.

        Args:
            file_entity_pairs: List of (file_path, entity_name) tuples
            source_system: Source system identifier

        Returns:
            Tuple of (consolidated_normalized_df, list_of_processing_reports, consolidated_validation_result)
        """
        from app.core.gl_pipeline import GLPipeline

        pipeline = GLPipeline()
        all_dfs = []
        all_reports = []
        all_validation_results = []

        for file_path, entity in file_entity_pairs:
            # Process each file
            normalized_df, processing_report, validation_result = (
                pipeline.process_gl_file(
                    file_path=file_path,
                    entity=entity,
                    source_system=source_system,
                )
            )

            all_dfs.append(normalized_df)
            all_reports.append(processing_report)
            all_validation_results.append(validation_result)

        # Consolidate DataFrames
        if all_dfs:
            consolidated_df = pd.concat(all_dfs, ignore_index=True)
        else:
            consolidated_df = pd.DataFrame()

        # Consolidate validation results
        consolidated_validation = self._consolidate_validation_results(
            all_validation_results
        )

        return consolidated_df, all_reports, consolidated_validation

    def _consolidate_validation_results(
        self, validation_results: List[ValidationResult]
    ) -> ValidationResult:
        """
        Consolidate multiple validation results into one.

        Args:
            validation_results: List of ValidationResult objects

        Returns:
            Consolidated ValidationResult
        """
        consolidated = ValidationResult()

        # Aggregate metrics
        total_transactions = sum(
            vr.key_metrics.get("total_transactions", 0) for vr in validation_results
        )
        total_debits = sum(
            vr.key_metrics.get("total_debits", 0) for vr in validation_results
        )
        total_credits = sum(
            vr.key_metrics.get("total_credits", 0) for vr in validation_results
        )

        consolidated.key_metrics = {
            "total_transactions": total_transactions,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "debit_credit_difference": abs(total_debits - total_credits),
            "date_parse_failure_rate": 0.0,  # Would need to aggregate from reports
        }

        # Collect all errors and warnings
        for vr in validation_results:
            consolidated.errors.extend(vr.errors)
            consolidated.warnings.extend(vr.warnings)

        # Set status: FAIL if any validation failed
        if any(not vr.is_valid() for vr in validation_results):
            consolidated.status = ValidationStatus.FAIL
        else:
            consolidated.status = ValidationStatus.PASS

        return consolidated

