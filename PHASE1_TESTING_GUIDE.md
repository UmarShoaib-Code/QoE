# Phase 1 Testing Guide

## Overview
This guide walks you through testing all Phase 1 MVP features:
- ✅ Upload and ingest raw GL Excel files
- ✅ Normalize inconsistent formats
- ✅ Standardize chart of accounts using rules-based mapping
- ✅ Calculate Net Income, EBITDA, and Adjusted EBITDA
- ✅ Generate a professional, formula-based Excel databook

---

## Step 1: Create Sample Test Data

First, create sample GL Excel files for testing:

```powershell
python create_sample_gl.py
```

This creates three sample files in `sample_data/`:
1. `sample_qbd_gl.xlsx` - QuickBooks Desktop format (with parent/subaccount headers)
2. `sample_qbo_gl.xlsx` - QuickBooks Online format (flat structure)
3. `sample_balanced_gl.xlsx` - Balanced GL (debits = credits)

---

## Step 2: Start the Streamlit UI

```powershell
python -m streamlit run app/ui/app.py
```

The UI will open at: **http://localhost:8501**

---

## Step 3: Test Feature by Feature

### ✅ Test 1: Upload and Ingest Raw GL Excel Files

**What to test:**
- File upload works
- Both QBD and QBO formats are accepted
- Multiple files can be uploaded

**Steps:**
1. In the Streamlit UI, click "Upload Excel GL File(s)"
2. Upload `sample_data/sample_qbd_gl.xlsx`
3. Enter entity name (e.g., "Test Company")
4. Select "QuickBooks Desktop" as source system
5. Click "🚀 Process Files"

**Expected Result:**
- ✅ File uploads successfully
- ✅ Processing spinner appears
- ✅ Validation results appear

---

### ✅ Test 2: Normalize Inconsistent Formats

**What to test:**
- QBD parent/subaccount headers are flattened correctly
- Dates are parsed correctly
- Non-transaction rows (headers, totals) are removed
- Account names are flattened (e.g., "Assets : Cash")

**Steps:**
1. Upload `sample_data/sample_qbd_gl.xlsx`
2. Process the file
3. Check the validation results

**Expected Result:**
- ✅ Validation shows transaction count
- ✅ Account names should be flattened (check logs or Excel output)
- ✅ No header rows or totals in final data

**Verify in Excel output:**
- Open the downloaded Excel file
- Check `GL_Clean` tab
- Verify account names are flattened (e.g., "Assets : Cash" or "Assets : Accounts Receivable")

---

### ✅ Test 3: Validation (Debit/Credit Balance Check)

**What to test:**
- Validation runs automatically
- Unbalanced GL files are rejected
- Balanced GL files pass validation

**Test 3A: Balanced File (Should PASS)**
1. Upload `sample_data/sample_balanced_gl.xlsx`
2. Process the file
3. Check validation status

**Expected Result:**
- ✅ **VALIDATION PASSED** banner appears
- ✅ Total Debits = Total Credits
- ✅ Difference = $0.00
- ✅ Download button appears

**Test 3B: Unbalanced File (Should FAIL)**
1. Upload `sample_data/sample_qbd_gl.xlsx` (this one is unbalanced)
2. Process the file
3. Check validation status

**Expected Result:**
- ❌ **VALIDATION FAILED** banner appears
- ❌ Error message explains why it failed
- ❌ Download button does NOT appear
- ✅ Clear error message: "Debits and Credits Don't Balance"

---

### ✅ Test 4: Standardize Chart of Accounts (Mapping)

**What to test:**
- Mapping template is generated
- Accounts can be mapped to categories
- Mapping is applied to GL data

**Steps:**
1. Upload a balanced GL file (or use `sample_balanced_gl.xlsx`)
2. Process the file
3. Download the Excel databook
4. Open the Excel file

**Check the `Mapping` tab:**
- ✅ Unique accounts are listed in `account_name_flat` column
- ✅ `main_category` column is empty (ready for mapping)
- ✅ Default categories are available: Revenue, COGS, OpEx, Other Income/Expense, Taxes, Interest, D&A, Balance Sheet
- ✅ Table format with filters enabled

**To test mapping:**
1. Fill in `main_category` for some accounts (e.g., "Sales" → "Revenue")
2. Save the Excel file
3. (Future: Re-upload to apply mapping - Phase 2 feature)

---

### ✅ Test 5: Calculate Net Income, EBITDA, and Adjusted EBITDA

**What to test:**
- EBITDA calculations use formulas
- Formulas recalculate correctly
- All financial metrics are calculated

**Steps:**
1. Process a balanced GL file
2. Download the Excel databook
3. Open the Excel file
4. Go to the `EBITDA` tab

**Check the EBITDA tab:**
- ✅ **Net Income** calculation (formula-based)
- ✅ **EBITDA** calculation (Net Income + Interest + Taxes + D&A)
- ✅ **Adjusted EBITDA** calculation (EBITDA + Adjustments)
- ✅ Formulas are present (not hardcoded values)
- ✅ Professional formatting (blue headers, white background)

**Test formula recalculation:**
1. Go to `GL_Clean` tab
2. Change a transaction amount
3. Go back to `EBITDA` tab
4. Press F9 (recalculate) or save and reopen
5. ✅ Values should update automatically

---

### ✅ Test 6: Generate Professional Excel Databook

**What to test:**
- All tabs are present
- Professional styling (blue/white theme)
- Excel Tables with filters
- Freeze panes
- File opens without warnings

**Steps:**
1. Process a balanced GL file
2. Download the Excel databook
3. Open in Microsoft Excel

**Check all tabs:**

**✅ README Tab:**
- Instructions on how to use the databook
- Timestamp and source file information
- Professional formatting

**✅ Validation Tab:**
- Summary section at top:
  - Validation Status (PASS/FAIL)
  - Generated Timestamp
  - Source File(s)
  - Entity Name(s)
  - Transaction Count
  - Date Range
  - Total Debits, Total Credits, Difference
- Error messages (if any) formatted clearly

**✅ GL_Clean Tab:**
- All transactions listed
- Excel Table format (with filters)
- Freeze panes on top row
- Blue header (#4472C4), white text
- Light blue table banding (#D9E1F2)
- Proper date and currency formatting

**✅ Mapping Tab:**
- Unique accounts listed
- Excel Table format
- Mapping columns ready for input
- Filters enabled

**✅ EBITDA Tab:**
- Formula-based calculations
- Professional formatting
- Clear labels and structure

**✅ Pivots_Inputs Tab:**
- Pivot-ready data structure
- Excel Table format
- Filters enabled

**Visual Checks:**
- ✅ Blue headers (#4472C4) with white text
- ✅ White background for data
- ✅ Light blue table banding (#D9E1F2)
- ✅ Top row frozen on all tabs
- ✅ Filters enabled on all tables
- ✅ File opens without Excel warnings
- ✅ Formulas recalculate correctly

---

## Step 4: Test Multi-Entity Processing

**What to test:**
- Multiple GL files can be processed together
- Each file is tagged with its entity name
- Consolidated output includes entity column

**Steps:**
1. Upload multiple files:
   - `sample_data/sample_qbd_gl.xlsx` → Entity: "Company A"
   - `sample_data/sample_qbo_gl.xlsx` → Entity: "Company B"
2. Enter different entity names for each file
3. Select source system
4. Process files

**Expected Result:**
- ✅ Both files processed
- ✅ Validation shows combined results
- ✅ Excel output includes `entity` column
- ✅ `GL_Clean` tab shows transactions from both entities
- ✅ Can filter by entity in Excel

---

## Step 5: Test Error Handling

**Test various error scenarios:**

### Test 5A: Empty File
1. Create an empty Excel file
2. Upload and process
3. ✅ Should show validation error

### Test 5B: Invalid Date Format
1. Create a GL file with invalid dates
2. Upload and process
3. ✅ Should show date parsing warnings/errors

### Test 5C: Missing Required Columns
1. Create a GL file missing "Account" or "Date" column
2. Upload and process
3. ✅ Should show clear error message

### Test 5D: Wrong File Format
1. Upload a non-Excel file (e.g., .txt, .pdf)
2. ✅ Should show file type error

---

## Step 6: Verify Logging

**What to test:**
- Logging is present for each pipeline step
- Logs are informative

**Steps:**
1. Process a file
2. Check the terminal/console where Streamlit is running

**Expected Logs:**
- ✅ "Reading GL file: ..."
- ✅ "Detected QuickBooks Desktop format"
- ✅ "Normalizing GL data..."
- ✅ "Flattening account names..."
- ✅ "Validating GL data..."
- ✅ "Generating Excel databook..."

---

## Quick Test Checklist

Use this checklist to verify Phase 1 is complete:

- [ ] **File Upload**: Can upload Excel GL files
- [ ] **Format Detection**: Detects QBD vs QBO formats
- [ ] **Normalization**: Removes headers, totals, invalid dates
- [ ] **Account Flattening**: QBD parent/subaccounts flattened correctly
- [ ] **Validation**: Debit/credit balance check works
- [ ] **Validation Failure**: Unbalanced files are rejected
- [ ] **Validation Success**: Balanced files pass validation
- [ ] **Excel Generation**: Databook generated on validation pass
- [ ] **Excel Tabs**: All tabs present (README, Validation, GL_Clean, Mapping, EBITDA, Pivots_Inputs)
- [ ] **Excel Styling**: Blue/white theme, tables, filters, freeze panes
- [ ] **EBITDA Calculations**: Formulas work and recalculate
- [ ] **Mapping Template**: Unique accounts extracted, mapping columns ready
- [ ] **Multi-Entity**: Multiple files can be processed together
- [ ] **Error Messages**: Clear, client-facing error messages
- [ ] **Logging**: Logs present for each pipeline step

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution:** Make sure you're running from the project root:
```powershell
cd D:\QoE\qoe_tool
python -m streamlit run app/ui/app.py
```

### Issue: "StreamlitDuplicateElementKey"
**Solution:** Restart Streamlit (Ctrl+C, then restart)

### Issue: Excel file won't open
**Solution:** Check that the file was fully generated. Try processing again.

### Issue: Formulas don't recalculate
**Solution:** In Excel, go to File → Options → Formulas → Enable "Automatic" calculation

---

## Next Steps

Once Phase 1 testing is complete:
- ✅ All features working as expected
- ✅ Excel output is professional and usable
- ✅ Validation catches errors correctly
- ✅ Ready to move to Phase 2 (Rules-Based Adjustments)

---

## Need Help?

If you encounter issues:
1. Check the terminal logs for error messages
2. Review the validation errors in the UI
3. Check the Excel Validation tab for detailed information
4. Run tests: `python -m pytest tests/test_integration.py -v`

