"""
Import Data Page

Upload, validate, preview, and reconcile data files.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.readers import read_csv_file, read_json_file, normalize_dataframe, detect_schema, create_data_dictionary, validate_required_fields
from src.validation import validate_records, check_duplicates_in_batch, preview_data_quality
from src.reconciliation import reconcile_import, commit_reconciliation
from src.routing import batch_analyze_conversations
from src.database import get_connection, get_import_history

st.set_page_config(page_title="Import Data - Revenue Intelligence Inbox", page_icon="📥", layout="wide")

st.title("📥 Import Data")
st.markdown("### Upload and reconcile conversation records")

# Initialize session state
if 'import_step' not in st.session_state:
    st.session_state.import_step = 'upload'
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

# Import steps
st.markdown("#### Import Workflow")
steps = ["1️⃣ Upload", "2️⃣ Validate", "3️⃣ Preview", "4️⃣ Reconcile", "5️⃣ Commit"]
st.markdown(" → ".join(steps))
st.markdown("---")

# Step 1: Upload
if st.session_state.import_step == 'upload':
    st.markdown("### Step 1: Upload File")
    
    st.info("📁 Upload a CSV or JSON file containing conversation records. The system will automatically detect and normalize column names.")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'json'],
        help="Supported formats: CSV, JSON (array of objects)"
    )
    
    if uploaded_file:
        try:
            # Read file based on type
            if uploaded_file.name.endswith('.csv'):
                df, file_hash = read_csv_file(uploaded_file)
                source_type = 'csv'
            elif uploaded_file.name.endswith('.json'):
                df, file_hash = read_json_file(uploaded_file)
                source_type = 'json'
            else:
                st.error("Unsupported file type")
                st.stop()
            
            # Store in session
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.file_hash = file_hash
            st.session_state.source_type = source_type
            
            st.success(f"✅ File uploaded: {uploaded_file.name} ({len(df)} rows)")
            
            # Detect schema
            schema = detect_schema(df)
            st.session_state.schema = schema
            
            # Show basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", schema['total_rows'])
            with col2:
                st.metric("Total Columns", schema['total_columns'])
            with col3:
                has_id = "✅" if schema['has_source_id'] else "⚠️"
                st.metric("Has Source ID", has_id)
            
            # Normalize data
            with st.spinner("Normalizing column names..."):
                normalized_df = normalize_dataframe(df)
                st.session_state.uploaded_data = normalized_df
            
            st.success("✅ Data normalized successfully")
            
            # Show data dictionary
            with st.expander("📖 Detected Data Dictionary"):
                data_dict = create_data_dictionary(normalized_df, schema)
                st.text(data_dict)
            
            # Show sample
            st.markdown("#### Sample Data (first 5 rows)")
            st.dataframe(normalized_df.head(), use_container_width=True)
            
            # Validate required fields
            validation_errors = validate_required_fields(normalized_df)
            if validation_errors:
                st.error("❌ Validation errors found:")
                for error in validation_errors:
                    st.write(f"- {error}")
            else:
                if st.button("Continue to Validation →", type="primary"):
                    st.session_state.import_step = 'validate'
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.exception(e)
    
    # Show import history
    st.markdown("---")
    st.markdown("### Import History")
    try:
        history = get_import_history()
        if not history.empty:
            display_df = history[['filename', 'timestamp', 'status', 'total_rows', 
                                 'new_count', 'updated_count', 'duplicate_count', 'invalid_count']].head(10)
            display_df.columns = ['File', 'Time', 'Status', 'Total', 'New', 'Updated', 'Duplicate', 'Invalid']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No import history yet")
    except:
        st.info("No import history available")

# Step 2: Validate
elif st.session_state.import_step == 'validate':
    st.markdown("### Step 2: Validate Data")
    
    df = st.session_state.uploaded_data
    
    with st.spinner("Validating records..."):
        # Check for duplicates in batch
        deduped_df, dup_warnings = check_duplicates_in_batch(df)
        
        if dup_warnings:
            st.warning("⚠️ Duplicate Detection")
            for warning in dup_warnings:
                st.write(f"- {warning}")
        
        # Validate records
        valid_df, invalid_df, error_summary = validate_records(deduped_df)
        
        st.session_state.valid_data = valid_df
        st.session_state.invalid_data = invalid_df
        st.session_state.validation_results = {
            'valid_count': len(valid_df),
            'invalid_count': len(invalid_df),
            'error_summary': error_summary
        }
    
    # Show results
    col1, col2 = st.columns(2)
    with col1:
        st.metric("✅ Valid Records", len(valid_df), delta=None, delta_color="normal")
    with col2:
        st.metric("❌ Invalid Records", len(invalid_df), delta=None, delta_color="inverse")
    
    if error_summary:
        with st.expander("❌ Validation Errors"):
            for error in error_summary:
                st.write(error)
        
        # Show invalid records
        if not invalid_df.empty:
            st.markdown("#### Invalid Records")
            st.dataframe(invalid_df.head(10), use_container_width=True)
            
            # Option to download invalid records
            csv = invalid_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Invalid Records",
                data=csv,
                file_name=f"invalid_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    if len(valid_df) > 0:
        # Data quality preview
        st.markdown("#### Data Quality Preview")
        quality_report = preview_data_quality(valid_df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Completeness:**")
            for field, stats in quality_report['completeness'].items():
                st.write(f"- {field}: {stats['percentage']}%")
        
        with col2:
            if quality_report.get('date_range'):
                st.markdown("**Date Range:**")
                st.write(f"- From: {quality_report['date_range']['earliest']}")
                st.write(f"- To: {quality_report['date_range']['latest']}")
                st.write(f"- Span: {quality_report['date_range']['span_days']} days")
        
        if quality_report.get('warnings'):
            with st.expander("⚠️ Quality Warnings"):
                for warning in quality_report['warnings']:
                    st.warning(warning)
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Upload"):
                st.session_state.import_step = 'upload'
                st.rerun()
        with col2:
            if st.button("Continue to Preview →", type="primary"):
                st.session_state.import_step = 'preview'
                st.rerun()
    else:
        st.error("No valid records to import. Please fix validation errors and try again.")
        if st.button("← Back to Upload"):
            st.session_state.import_step = 'upload'
            st.rerun()

# Step 3: Preview
elif st.session_state.import_step == 'preview':
    st.markdown("### Step 3: Preview & Reconcile")
    
    valid_df = st.session_state.valid_data
    
    st.info(f"📊 Ready to reconcile {len(valid_df)} valid records against existing database")
    
    # Show sample of what will be imported
    st.markdown("#### Sample Records to Import")
    st.dataframe(valid_df.head(10), use_container_width=True)
    
    # Create batch record
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO import_batches (
            filename, file_hash, timestamp, status, total_rows
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.uploaded_file_name,
        st.session_state.file_hash,
        datetime.utcnow().isoformat(),
        'pending',
        len(valid_df)
    ))
    batch_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    st.session_state.batch_id = batch_id
    
    # Reconcile
    with st.spinner("Reconciling with existing data..."):
        reconciliation_result = reconcile_import(valid_df, batch_id)
        st.session_state.reconciliation_result = reconciliation_result
    
    # Show reconciliation results
    st.markdown("#### Reconciliation Results")
    
    counts = reconciliation_result.get_counts()
    
    cols = st.columns(5)
    with cols[0]:
        st.metric("🆕 New", counts['new'])
    with cols[1]:
        st.metric("✅ Unchanged", counts['unchanged'])
    with cols[2]:
        st.metric("🔄 Updated", counts['updated'])
    with cols[3]:
        st.metric("⚠️ Conflicts", counts['conflict'])
    with cols[4]:
        st.metric("📋 Duplicates", counts['duplicate'])
    
    # Detailed breakdown
    with st.expander("📊 Detailed Breakdown"):
        st.markdown("**New Records:** Will be inserted into database")
        st.markdown("**Unchanged:** Already in database with identical content")
        st.markdown("**Updated:** Existing records with changed content")
        st.markdown("**Conflicts:** Records with active manual overrides that might be affected")
        st.markdown("**Duplicates:** Multiple records with same source_id within this batch (already handled)")
    
    if counts['conflict'] > 0:
        st.warning(f"⚠️ {counts['conflict']} conflicts detected. These records have active manual overrides. Source data will be updated, but overrides will be preserved. Please review after import.")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Validation"):
            st.session_state.import_step = 'validate'
            st.rerun()
    with col2:
        if st.button("Commit Import →", type="primary"):
            st.session_state.import_step = 'commit'
            st.rerun()

# Step 4: Commit
elif st.session_state.import_step == 'commit':
    st.markdown("### Step 4: Commit Import")
    
    reconciliation_result = st.session_state.reconciliation_result
    batch_id = st.session_state.batch_id
    
    try:
        with st.spinner("Committing changes to database..."):
            # Commit reconciliation
            stats = commit_reconciliation(
                reconciliation_result,
                batch_id,
                st.session_state.source_type
            )
            
            # Update batch record
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE import_batches SET
                    status = 'success',
                    new_count = ?,
                    unchanged_count = ?,
                    updated_count = ?,
                    duplicate_count = 0,
                    invalid_count = ?,
                    conflict_count = ?
                WHERE id = ?
            """, (
                stats['inserted'],
                stats['unchanged'],
                stats['updated'],
                st.session_state.validation_results['invalid_count'],
                stats['conflicts_flagged'],
                batch_id
            ))
            conn.commit()
            
            # Get IDs of new and updated conversations for analysis
            cursor.execute("""
                SELECT id FROM conversations
                WHERE id >= (SELECT COALESCE(MAX(id), 0) - ? FROM conversations)
            """, (stats['inserted'] + stats['updated'],))
            conversation_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
        
        st.success("✅ Import committed successfully!")
        
        # Show final stats
        cols = st.columns(4)
        with cols[0]:
            st.metric("Inserted", stats['inserted'])
        with cols[1]:
            st.metric("Updated", stats['updated'])
        with cols[2]:
            st.metric("Unchanged", stats['unchanged'])
        with cols[3]:
            st.metric("Conflicts", stats['conflicts_flagged'])
        
        # Run analysis on imported conversations
        st.markdown("#### Running Routing Analysis")
        with st.spinner("Analyzing conversations and assigning priorities..."):
            analyzed_count = batch_analyze_conversations(conversation_ids)
        
        st.success(f"✅ Analyzed {analyzed_count} conversations")
        
        # Success message
        st.balloons()
        st.markdown("---")
        st.success("🎉 Import completed successfully! View results in the Overview and Inbox pages.")
        
        # Reset and start new import
        if st.button("Start New Import", type="primary"):
            # Clear session state
            for key in ['import_step', 'uploaded_data', 'validation_results', 'valid_data', 
                       'invalid_data', 'reconciliation_result', 'batch_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.import_step = 'upload'
            st.rerun()
            
    except Exception as e:
        st.error(f"Error committing import: {str(e)}")
        st.exception(e)
        
        # Update batch status to failed
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE import_batches SET
                    status = 'failed',
                    error_message = ?
                WHERE id = ?
            """, (str(e), batch_id))
            conn.commit()
            conn.close()
        except:
            pass
        
        if st.button("← Back to Preview"):
            st.session_state.import_step = 'preview'
            st.rerun()

# Reset button (always available)
st.markdown("---")
if st.button("🔄 Reset Import Process"):
    for key in ['import_step', 'uploaded_data', 'validation_results', 'valid_data', 
               'invalid_data', 'reconciliation_result', 'batch_id']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.import_step = 'upload'
    st.rerun()
