"""
Script to create sample GL Excel files for testing Phase 1
Creates sample QuickBooks Desktop and QuickBooks Online format files
"""
import pandas as pd
from datetime import datetime, timedelta
import os

def create_qb_desktop_sample(output_path="sample_data/sample_qbd_gl.xlsx"):
    """Create a sample QuickBooks Desktop format GL file"""
    
    # Create sample_data directory if it doesn't exist
    os.makedirs("sample_data", exist_ok=True)
    
    # Sample data with parent/subaccount structure
    data = {
        "Date": [
            "Date",  # Header row
            None,  # Parent account header (no date)
            "2024-01-15",
            "2024-01-16",
            "2024-01-20",
            None,  # Sub-account header
            "2024-01-18",
            "2024-01-19",
            None,  # Another parent account
            "2024-01-21",
            "2024-01-22",
            None,  # Another parent account
            "2024-01-23",
            "2024-01-24",
        ],
        "Account": [
            "Account",
            "Assets",  # Parent account
            "Cash",
            "Cash",
            "Cash",
            "  Accounts Receivable",  # Indented sub-account
            "  Accounts Receivable",
            "  Accounts Receivable",
            "Revenue",  # Another parent account
            "Sales",
            "Sales",
            "Operating Expenses",  # Another parent account
            "Rent Expense",
            "Utilities Expense",
        ],
        "Description": [
            "Description",
            "",  # Parent account header
            "Initial Deposit",
            "Customer Payment",
            "Bank Transfer",
            "",  # Sub-account header
            "Invoice #1001",
            "Invoice #1002",
            "",  # Parent account header
            "Product Sales",
            "Service Revenue",
            "",  # Parent account header
            "Office Rent",
            "Electric Bill",
        ],
        "Debit": [
            "Debit",
            "",
            50000.0,  # Cash deposit
            5000.0,   # Cash payment
            2000.0,   # Cash transfer
            "",
            10000.0,  # AR debit
            8000.0,   # AR debit
            "",
            0.0,      # Revenue (credit)
            0.0,      # Revenue (credit)
            "",
            3000.0,   # Rent expense
            500.0,    # Utilities expense
        ],
        "Credit": [
            "Credit",
            "",
            0.0,
            0.0,
            0.0,
            "",
            0.0,
            0.0,
            "",
            15000.0,  # Sales credit
            12000.0,  # Service revenue credit
            "",
            0.0,
            0.0,
        ],
    }
    
    df = pd.DataFrame(data)
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    
    print(f"[OK] Created QuickBooks Desktop sample: {output_path}")
    print(f"   Total rows: {len(df)}")
    print(f"   Expected transactions: 11 (after removing headers and totals)")
    return output_path


def create_qb_online_sample(output_path="sample_data/sample_qbo_gl.xlsx"):
    """Create a sample QuickBooks Online format GL file"""
    
    # Create sample_data directory if it doesn't exist
    os.makedirs("sample_data", exist_ok=True)
    
    # Sample data - QBO format is flatter
    data = {
        "Date": [
            "Date",
            "2024-01-15",
            "2024-01-16",
            "2024-01-17",
            "2024-01-18",
            "2024-01-19",
            "2024-01-20",
            "2024-01-21",
            "2024-01-22",
        ],
        "Account": [
            "Account",
            "Cash",
            "Accounts Receivable",
            "Accounts Receivable",
            "Sales",
            "Service Revenue",
            "Rent Expense",
            "Utilities Expense",
            "Office Supplies",
        ],
        "Description": [
            "Description",
            "Initial Deposit",
            "Invoice #1001",
            "Invoice #1002",
            "Product Sales",
            "Consulting Services",
            "Office Rent",
            "Electric Bill",
            "Printer Paper",
        ],
        "Debit": [
            "Debit",
            40000.0,
            12000.0,
            9000.0,
            0.0,
            0.0,
            2500.0,
            400.0,
            150.0,
        ],
        "Credit": [
            "Credit",
            0.0,
            0.0,
            0.0,
            18000.0,
            15000.0,
            0.0,
            0.0,
            0.0,
        ],
    }
    
    df = pd.DataFrame(data)
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    
    print(f"[OK] Created QuickBooks Online sample: {output_path}")
    print(f"   Total rows: {len(df)}")
    print(f"   Expected transactions: 8 (after removing header)")
    return output_path


def create_balanced_gl_sample(output_path="sample_data/sample_balanced_gl.xlsx"):
    """Create a balanced GL file (debits = credits) for testing"""
    
    os.makedirs("sample_data", exist_ok=True)
    
    # Create balanced transactions (no header row - QuickBooks exports don't always have explicit headers)
    # But include a header row that will be detected and skipped
    data = {
        "Date": [
            "Date",  # Header row (will be detected and skipped)
            "2024-01-15",
            "2024-01-16",
            "2024-01-17",
            "2024-01-18",
            "2024-01-19",
            "2024-01-20",
        ],
        "Account": [
            "Account",  # Header
            "Cash",
            "Accounts Receivable",
            "Sales",
            "Rent Expense",
            "Cash",
            "Accounts Payable",
        ],
        "Description": [
            "Description",  # Header
            "Initial Deposit",
            "Invoice Payment",
            "Product Sales",
            "Office Rent",
            "Customer Payment",
            "Vendor Invoice",
        ],
        "Debit": [
            "Debit",  # Header
            10000.0,  # Cash debit
            5000.0,   # AR debit
            0.0,      # Sales (credit)
            2000.0,   # Rent expense (debit)
            3000.0,   # Cash debit
            0.0,      # AP (credit)
        ],
        "Credit": [
            "Credit",  # Header
            0.0,
            0.0,
            15000.0,  # Sales credit
            0.0,
            0.0,
            5000.0,  # AP credit
        ],
    }
    
    df = pd.DataFrame(data)
    
    # Write to Excel WITHOUT header (since we're including it in the data)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, header=False, sheet_name="Sheet1")
    
    print(f"[OK] Created balanced GL sample: {output_path}")
    print(f"   Total Debits: $20,000.00")
    print(f"   Total Credits: $20,000.00")
    print(f"   [OK] Balanced!")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("Creating Sample GL Files for Phase 1 Testing")
    print("=" * 60)
    print()
    
    # Create sample files
    qbd_file = create_qb_desktop_sample()
    print()
    
    qbo_file = create_qb_online_sample()
    print()
    
    balanced_file = create_balanced_gl_sample()
    print()
    
    print("=" * 60)
    print("[OK] Sample files created successfully!")
    print("=" * 60)
    print()
    print("Files created:")
    print(f"  1. {qbd_file} - QuickBooks Desktop format (with parent/subaccounts)")
    print(f"  2. {qbo_file} - QuickBooks Online format (flat structure)")
    print(f"  3. {balanced_file} - Balanced GL (debits = credits)")
    print()
    print("You can now use these files to test Phase 1 features!")

