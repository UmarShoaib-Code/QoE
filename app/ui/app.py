"""
Streamlit UI entrypoint for QoE Tool - Production Level
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime
import tempfile
import os
import pandas as pd

# Import all modules at the top to avoid re-execution issues
from app.core.mapping import MultiEntityProcessor
from app.core.gl_pipeline import GLPipeline
from app.excel.databook_generator import DatabookGenerator

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="QoE Tool - GL Processing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# ============================================================================
# INJECT CSS FIRST - BEFORE ANY CONTENT (using components.html for better injection)
# ============================================================================
# Note: JavaScript injection moved to CSS section for better compatibility

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #4472C4;
        --success-color: #28a745;
        --danger-color: #dc3545;
        --warning-color: #ffc107;
        --info-color: #17a2b8;
        --light-bg: #f8f9fa;
        --dark-text: #212529;
        --border-color: #dee2e6;
    }
    
    /* Custom header styling */
    .main-header {
        background: linear-gradient(135deg, #1f77b4 0%, #4472C4 100%);
        padding: 1.5rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        margin-top: 0 !important;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid var(--primary-color);
        margin-bottom: 1rem;
    }
    
    .metric-card.success {
        border-left-color: var(--success-color);
    }
    
    .metric-card.danger {
        border-left-color: var(--danger-color);
    }
    
    .metric-card.warning {
        border-left-color: var(--warning-color);
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge.pass {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-badge.fail {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* File upload area */
    .upload-area {
        border: 2px dashed var(--border-color);
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: var(--light-bg);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: var(--primary-color);
        background-color: #e7f3ff;
    }
    
    /* Section containers */
    .section-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: var(--primary-color);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Info boxes */
    .info-box {
        background: #e7f3ff;
        border-left: 4px solid var(--info-color);
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    /* Stats grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 3rem;
        border-top: 1px solid var(--border-color);
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom divider */
    .divider {
        height: 2px;
        background: linear-gradient(to right, transparent, var(--border-color), transparent);
        margin: 2rem 0;
    }
    
    /* Remove ALL top spacing - aggressive override */
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    .main {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Fix side padding and top space - control main content area */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem;
        padding-left: 5%;
        padding-right: 5%;
        max-width: 1400px;
        margin-top: -2rem !important;
    }
    
    /* Adjust for smaller screens */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 2%;
            padding-right: 2%;
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
    }
    
    /* Header spacing - full width with proper padding, no top margin */
    .main-header {
        margin-left: -5%;
        margin-right: -5%;
        padding-left: 5%;
        padding-right: 5%;
        margin-top: -2rem !important;
        margin-bottom: 1.5rem;
        padding-top: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .main-header {
            margin-left: -2%;
            margin-right: -2%;
            padding-left: 2%;
            padding-right: 2%;
        }
    }
    
    /* Remove ALL extra top spacing from Streamlit elements */
    .stApp > header {
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    #MainMenu {
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Remove top margin from ALL first elements */
    .main .block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    .main .block-container > div:first-child > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove spacing from markdown elements at top */
    .main .block-container > div:first-child > div > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Target the header markdown specifically */
    .main .block-container > div:first-child .main-header {
        margin-top: 0 !important;
        padding-top: 1.5rem;
    }
    
    /* Remove any spacing from Streamlit's root elements */
    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    [data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
    }
    
    /* Remove spacing from first markdown block */
    .main .block-container > div:first-child [data-testid="stMarkdownContainer"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Reduce top spacing for sections */
    h3 {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Better spacing for file upload section */
    .element-container {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None
if "validation_result" not in st.session_state:
    st.session_state.validation_result = None
if "processing_report" not in st.session_state:
    st.session_state.processing_report = None
if "source_files" not in st.session_state:
    st.session_state.source_files = []
if "excel_file_path" not in st.session_state:
    st.session_state.excel_file_path = None
if "processing_status" not in st.session_state:
    st.session_state.processing_status = "idle"  # idle, processing, completed, error

# ============================================================================
# HEADER SECTION
# ============================================================================
# Add negative margin container to pull header up
st.markdown("""
<div style="margin-top: -2rem !important; padding-top: 0 !important;">
    <div class="main-header" style="margin-top: 0 !important; padding-top: 1.5rem;">
        <h1>📊 QoE Tool</h1>
        <p>Quality of Earnings Analysis - General Ledger Processing Platform</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - Quick Stats & Info
# ============================================================================
with st.sidebar:
    st.markdown("### 📈 Quick Stats")
    
    if st.session_state.processed_data is not None:
        df = st.session_state.processed_data
        st.metric("Total Transactions", f"{len(df):,}")
        
        if "date" in df.columns:
            try:
                df['date'] = pd.to_datetime(df['date'])
                date_range = f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
                st.caption(f"📅 Date Range: {date_range}")
            except:
                pass
        
        if "entity" in df.columns:
            entities = df["entity"].unique()
            st.metric("Entities", len(entities))
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption("""
    **QoE Tool** processes General Ledger exports from QuickBooks to generate analyst-ready databooks.
    
    **Features:**
    - Multi-format GL ingestion
    - Data validation & quality checks
    - Account mapping & categorization
    - EBITDA calculations
    - Professional Excel output
    """)
    
    st.markdown("---")
    st.caption("Version 1.0.0 | Internal Use Only")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# ============================================================================
# SECTION 1: FILE UPLOAD
# ============================================================================
st.markdown("### 📁 Step 1: Upload GL Files")

upload_container = st.container()
with upload_container:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Upload Excel GL File(s)",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            help="Upload one or multiple QuickBooks GL export files (QuickBooks Desktop or QuickBooks Online)",
            key="gl_file_uploader"
        )
    
    with col2:
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s)")

entity_configs = {}
source_system = None

if uploaded_files:
    st.markdown("---")
    
    # File details section
    with st.expander("📋 Uploaded Files Details", expanded=True):
        file_cols = st.columns(min(len(uploaded_files), 3))
        for idx, uploaded_file in enumerate(uploaded_files):
            with file_cols[idx % len(file_cols)]:
                file_size = len(uploaded_file.getvalue()) / 1024  # KB
                st.info(f"""
                **{uploaded_file.name}**  
                📦 {file_size:.1f} KB  
                📄 {uploaded_file.type}
                """)
    
    # Entity configuration
    st.markdown("### 🏢 Entity Configuration")
    
    entity_cols = st.columns(min(len(uploaded_files), 2))
    for idx, uploaded_file in enumerate(uploaded_files):
        with entity_cols[idx % len(entity_cols)]:
            # Infer entity name from filename
            default_entity = Path(uploaded_file.name).stem.replace("_GL", "").replace("_", " ").title()
            entity_name = st.text_input(
                f"Entity name for: `{uploaded_file.name}`",
                value=default_entity,
                key=f"entity_{idx}",
                help="Enter the entity name for this GL file",
                placeholder="Enter entity name..."
            )
            entity_configs[uploaded_file.name] = entity_name
    
    # Source system selection
    st.markdown("### ⚙️ Processing Configuration")
    source_col1, source_col2 = st.columns([2, 1])
    
    with source_col1:
        source_system = st.selectbox(
            "Select source system",
            ["QuickBooks Online", "QuickBooks Desktop"],
            help="Choose the accounting system that generated these GL exports",
            key="source_system_selectbox"
        )
    
    with source_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if source_system == "QuickBooks Desktop":
            st.info("🔧 QBD Format")
        else:
            st.info("☁️ QBO Format")

# ============================================================================
# SECTION 2: PROCESS BUTTON
# ============================================================================
if uploaded_files and source_system:
    # Validate entity names
    missing_entities = [fname for fname, entity in entity_configs.items() if not entity.strip()]
    
    if missing_entities:
        st.warning(f"⚠️ Please provide entity names for: {', '.join(missing_entities)}")
    else:
        st.markdown("---")
        
        # Process button with enhanced styling
        process_col1, process_col2, process_col3 = st.columns([1, 2, 1])
        with process_col2:
            process_button = st.button(
                "🚀 Process GL Files",
                type="primary",
                use_container_width=True,
                key="process_button"
            )
        
        if process_button:
            st.session_state.processing_status = "processing"
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: File preparation
                status_text.info("📦 Preparing files...")
                progress_bar.progress(10)
                
                if len(uploaded_files) == 1:
                    # Single file processing
                    uploaded_file = uploaded_files[0]
                    entity_name = entity_configs[uploaded_file.name]
                    
                    # Save file temporarily
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file.close()
                    tmp_path = tmp_file.name
                    
                    try:
                        # Step 2: Ingestion
                        status_text.info("📥 Ingesting GL data...")
                        progress_bar.progress(30)
                        
                        pipeline = GLPipeline()
                        
                        # Step 3: Normalization
                        status_text.info("🔄 Normalizing data structure...")
                        progress_bar.progress(50)
                        
                        normalized_df, processing_report, validation_result = (
                            pipeline.process_gl_file(
                                file_path=tmp_path,
                                entity=entity_name,
                                source_system=source_system,
                            )
                        )
                        
                        # Step 4: Validation
                        status_text.info("✅ Running validation checks...")
                        progress_bar.progress(80)
                        
                        # Store results
                        st.session_state.processed_data = normalized_df
                        st.session_state.validation_result = validation_result
                        st.session_state.processing_report = processing_report
                        st.session_state.source_files = [uploaded_file.name]
                        st.session_state.excel_file_path = None
                        st.session_state.processing_status = "completed"
                        
                        progress_bar.progress(100)
                        status_text.success("✅ Processing completed successfully!")
                        
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            
                else:
                    # Multiple files processing
                    file_entity_pairs = []
                    tmp_paths = []
                    
                    try:
                        for uploaded_file in uploaded_files:
                            entity_name = entity_configs[uploaded_file.name]
                            
                            # Save file temporarily
                            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file.close()
                            tmp_paths.append(tmp_file.name)
                            file_entity_pairs.append((tmp_file.name, entity_name))
                        
                        status_text.info("📥 Processing multiple files...")
                        progress_bar.progress(40)
                        
                        # Process multiple files
                        processor = MultiEntityProcessor()
                        normalized_df, processing_reports, validation_result = (
                            processor.process_multiple_files(
                                file_entity_pairs=file_entity_pairs,
                                source_system=source_system,
                            )
                        )
                        
                        status_text.info("✅ Running validation checks...")
                        progress_bar.progress(80)
                        
                        # Store results
                        st.session_state.processed_data = normalized_df
                        st.session_state.validation_result = validation_result
                        st.session_state.processing_report = processing_reports[0] if processing_reports else None
                        st.session_state.source_files = [f.name for f in uploaded_files]
                        st.session_state.excel_file_path = None
                        st.session_state.processing_status = "completed"
                        
                        progress_bar.progress(100)
                        status_text.success("✅ Processing completed successfully!")
                        
                    finally:
                        # Clean up temp files
                        for tmp_path in tmp_paths:
                            if os.path.exists(tmp_path):
                                os.unlink(tmp_path)
                
                # Small delay to show completion
                import time
                time.sleep(0.5)
                
                # Force rerun to show results
                st.rerun()
                
            except Exception as e:
                st.session_state.processing_status = "error"
                progress_bar.progress(100)
                status_text.error(f"❌ Error processing files: {str(e)}")
                st.error(f"**Error Details:**\n\n{str(e)}")
                with st.expander("🔍 Technical Details", expanded=False):
                    st.exception(e)

# ============================================================================
# SECTION 3: VALIDATION RESULTS DASHBOARD
# ============================================================================
if st.session_state.validation_result is not None:
    st.markdown("---")
    st.markdown("### ✅ Step 2: Validation Results")
    
    validation_result = st.session_state.validation_result
    processing_report = st.session_state.processing_report
    
    # Status Banner with enhanced styling
    status_col1, status_col2 = st.columns([3, 1])
    with status_col1:
        if validation_result.is_valid():
            st.markdown("""
            <div style='background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                        padding: 1.5rem; border-radius: 10px; color: white; 
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 1.5rem;'>
                <h2 style='color: white; margin: 0;'>✅ VALIDATION PASSED</h2>
                <p style='color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0;'>
                    Your GL data has been successfully validated and is ready for processing.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); 
                        padding: 1.5rem; border-radius: 10px; color: white; 
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 1.5rem;'>
                <h2 style='color: white; margin: 0;'>❌ VALIDATION FAILED</h2>
                <p style='color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0;'>
                    Please review the errors below and fix your GL file before proceeding.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with status_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if validation_result.is_valid():
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: #d4edda; 
                        border-radius: 8px; border: 2px solid #28a745;'>
                <h3 style='color: #155724; margin: 0;'>READY</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: #f8d7da; 
                        border-radius: 8px; border: 2px solid #dc3545;'>
                <h3 style='color: #721c24; margin: 0;'>BLOCKED</h3>
            </div>
            """, unsafe_allow_html=True)
    
    # Key Metrics Dashboard
    if validation_result.key_metrics:
        metrics = validation_result.key_metrics
        
        st.markdown("#### 📊 Key Metrics")
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric(
                "Total Transactions",
                f"{metrics.get('total_transactions', 0):,}",
                help="Number of valid transaction rows processed"
            )
        
        with metric_cols[1]:
            debit_value = metrics.get('total_debits', 0)
            st.metric(
                "Total Debits",
                f"${debit_value:,.2f}",
                help="Sum of all debit amounts"
            )
        
        with metric_cols[2]:
            credit_value = metrics.get('total_credits', 0)
            st.metric(
                "Total Credits",
                f"${credit_value:,.2f}",
                help="Sum of all credit amounts"
            )
        
        with metric_cols[3]:
            diff = metrics.get("debit_credit_difference", 0)
            diff_delta = f"{diff:,.2f}"
            if diff > 0.01:
                diff_delta = f"⚠️ {diff_delta}"
            st.metric(
                "Difference",
                f"${diff:,.2f}",
                delta=diff_delta if diff <= 0.01 else None,
                delta_color="normal" if diff <= 0.01 else "inverse",
                help="Absolute difference between debits and credits"
            )
    
    # Processing Statistics
    if processing_report:
        st.markdown("#### 📈 Processing Statistics")
        stats_cols = st.columns(5)
        
        with stats_cols[0]:
            st.metric(
                "Rows Read",
                f"{processing_report.total_rows_read:,}",
                help="Total rows read from source file"
            )
        
        with stats_cols[1]:
            st.metric(
                "Valid Transactions",
                f"{processing_report.final_transaction_rows:,}",
                help="Final number of transaction rows after filtering"
            )
        
        with stats_cols[2]:
            removed_total = (
                processing_report.rows_removed_totals +
                processing_report.rows_removed_subtotals +
                processing_report.rows_removed_opening_balance
            )
            st.metric(
                "Rows Removed",
                f"{removed_total:,}",
                help="Total rows removed (totals, subtotals, opening balances)"
            )
        
        with stats_cols[3]:
            invalid_dates = processing_report.rows_with_invalid_dates
            st.metric(
                "Invalid Dates",
                f"{invalid_dates:,}",
                delta=f"-{invalid_dates}" if invalid_dates == 0 else None,
                delta_color="normal",
                help="Number of rows with invalid or unparseable dates"
            )
        
        with stats_cols[4]:
            if processing_report.total_rows_read > 0:
                success_rate = (processing_report.final_transaction_rows / processing_report.total_rows_read) * 100
                st.metric(
                    "Success Rate",
                    f"{success_rate:.1f}%",
                    help="Percentage of rows successfully processed"
                )
    
    # Error Messages Section (if FAIL)
    if not validation_result.is_valid():
        st.markdown("---")
        st.markdown("#### ❌ Error Messages")
        
        if validation_result.errors:
            for idx, error in enumerate(validation_result.errors, 1):
                with st.expander(
                    f"🔴 Error {idx}: Click to view details and resolution steps",
                    expanded=True
                ):
                    st.markdown(error)
                    st.markdown("---")
                    st.caption(f"Error {idx} of {len(validation_result.errors)}")
        else:
            st.info("No specific error messages available.")
    
    # Warnings Section
    if validation_result.warnings:
        st.markdown("---")
        st.markdown("#### ⚠️ Warnings")
        
        for idx, warning in enumerate(validation_result.warnings, 1):
            with st.expander(
                f"⚠️ Warning {idx}: Click to view details",
                expanded=False
            ):
                st.markdown(warning)
                st.markdown("---")
                st.caption(f"Warning {idx} of {len(validation_result.warnings)}")
    
    # Processing Warnings (from ingestion)
    if processing_report and processing_report.warnings:
        st.markdown("---")
        st.markdown("#### ℹ️ Processing Warnings")
        for warning in processing_report.warnings:
            st.warning(warning)

# ============================================================================
# SECTION 4: DOWNLOAD EXCEL DATABOOK (only if validation PASS)
# ============================================================================
if st.session_state.validation_result is not None and st.session_state.validation_result.is_valid():
    st.markdown("---")
    st.markdown("### 📥 Step 3: Download Excel Databook")
    
    # Generate Excel file if not already generated
    if st.session_state.excel_file_path is None or not os.path.exists(st.session_state.excel_file_path):
        default_filename = f"GL_Databook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        try:
            # Get entity info
            entity_info = None
            if st.session_state.processed_data is not None:
                df = st.session_state.processed_data
                if "entity" in df.columns:
                    entities = df["entity"].unique()
                    if len(entities) == 1:
                        entity_info = entities[0]
            
            # Generate databook with progress
            with st.spinner("🔄 Generating professional Excel databook..."):
                # Automatically generate mapping
                from app.core.mapping import GLAccountMapper
                mapper = GLAccountMapper()
                auto_mapping_df = mapper.generate_auto_mapping_df(
                    st.session_state.processed_data,
                    entity=entity_info
                )
                
                generator = DatabookGenerator(break_formulas=False)
                
                output_path = generator.generate_databook(
                    output_path=default_filename,
                    normalized_df=st.session_state.processed_data,
                    validation_result=st.session_state.validation_result,
                    processing_report=st.session_state.processing_report,
                    source_files=st.session_state.source_files,
                    entity=entity_info,
                    mapping_df=auto_mapping_df,  # Pass auto-generated mapping
                )
                
                st.session_state.excel_file_path = output_path
                
                st.success("✅ Excel databook generated successfully!")
                
        except Exception as e:
            st.error(f"❌ Error generating Excel file: {str(e)}")
            with st.expander("🔍 Technical Details", expanded=False):
                st.exception(e)
    
    # Download section with enhanced UI
    if st.session_state.excel_file_path and os.path.exists(st.session_state.excel_file_path):
        file_path = Path(st.session_state.excel_file_path)
        file_size = file_path.stat().st_size / 1024  # KB
        
        # File info card
        info_col1, info_col2, info_col3 = st.columns([2, 1, 1])
        
        with info_col1:
            st.markdown(f"""
            <div style='background: #e7f3ff; padding: 1rem; border-radius: 8px; 
                        border-left: 4px solid #17a2b8; margin-bottom: 1rem;'>
                <strong>📄 File Ready:</strong> <code>{file_path.name}</code><br>
                <small>📦 Size: {file_size:.1f} KB | 📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with info_col2:
            st.metric("File Size", f"{file_size:.1f} KB")
        
        with info_col3:
            if st.session_state.processed_data is not None:
                st.metric("Transactions", f"{len(st.session_state.processed_data):,}")
        
        # Download button
        with open(st.session_state.excel_file_path, "rb") as f:
            file_data = f.read()
            filename = file_path.name
            
            download_col1, download_col2, download_col3 = st.columns([1, 2, 1])
            with download_col2:
                st.download_button(
                    label="📥 Download Excel Databook",
                    data=file_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                    key="download_button"
                )
        
        # File contents preview
        st.markdown("---")
        with st.expander("📋 Excel Databook Contents", expanded=False):
            st.markdown("""
            The generated Excel databook contains the following tabs:
            
            - **README**: Instructions, timestamp, and source file information
            - **Validation**: Validation results, totals, and processing statistics
            - **GL_Clean**: Clean, normalized transaction table with all columns
            - **Mapping**: Unique account list with mapping columns for categorization
            - **EBITDA**: Net Income, EBITDA, and Adjusted EBITDA calculations (formula-based)
            - **Pivots_Inputs**: Pivot-ready table for analysis
            
            All tabs include:
            - Professional blue/white styling
            - Frozen top row
            - Enabled filters
            - Consistent number and date formatting
            - Excel Table format for easy analysis
            """)
        
        # Data preview
        if st.session_state.processed_data is not None:
            st.markdown("---")
            with st.expander("👁️ Preview Processed Data", expanded=False):
                df_preview = st.session_state.processed_data.head(100)
                st.dataframe(
                    df_preview,
                    use_container_width=True,
                    height=400
                )
                st.caption(f"Showing first 100 rows of {len(st.session_state.processed_data):,} total transactions")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p><strong>QoE Tool</strong> - Quality of Earnings Analysis Platform</p>
    <p>Version 1.0.0 | Internal Use Only | © 2024</p>
    <p style="font-size: 0.8rem; color: #6c757d;">
        For support or questions, please contact the development team.
    </p>
</div>
""", unsafe_allow_html=True)