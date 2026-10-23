"""
Exports Page

Generate and verify data exports with manifest.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from src.exports import generate_export, verify_export, get_export_history, EXPORT_DIR
from src.database import get_all_conversations

st.set_page_config(page_title="Exports - Revenue Intelligence Inbox", page_icon="📤", layout="wide")

st.title("📤 Exports")
st.markdown("### Generate verified exports with manifest")

# Export generation section
st.markdown("### Generate New Export")

with st.expander("⚙️ Export Configuration", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox("Export Format", ["csv", "json"])
        include_overrides = st.checkbox("Include Override Information", value=True,
                                       help="Add columns indicating which fields have active manual overrides")
    
    with col2:
        # Filters
        st.markdown("**Apply Filters:**")
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low", "needs_review"], key="export_priority")
        category_filter = st.selectbox("Category", 
            ["All", "buying_signal", "objection_blocker", "customer_risk", "product_feedback", "routine", "needs_review"],
            key="export_category"
        )

# Build filter dict
filters = {}
if priority_filter != "All":
    filters['priority'] = priority_filter
if category_filter != "All":
    filters['category'] = category_filter

# Preview what will be exported
try:
    preview_df = get_all_conversations(filters if filters else None)
    
    st.markdown(f"**Preview:** {len(preview_df)} conversations will be exported")
    
    if not preview_df.empty:
        # Show sample
        with st.expander("📊 Preview Export Data (first 10 rows)"):
            st.dataframe(preview_df.head(10), use_container_width=True)
        
        # Generate export button
        if st.button("Generate Export", type="primary"):
            try:
                with st.spinner("Generating export files..."):
                    result = generate_export(
                        export_format=export_format,
                        filters=filters if filters else None,
                        include_overrides=include_overrides
                    )
                
                st.success("✅ Export generated successfully!")
                
                # Show export details
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Records Exported", result['row_count'])
                    st.metric("Main File", result['main_filename'])
                with col2:
                    st.metric("Manifest File", result['manifest_filename'])
                    st.metric("Generated At", result['timestamp'])
                
                # Download buttons
                st.markdown("#### Download Files")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Read main file
                    main_path = Path(result['main_file'])
                    with open(main_path, 'rb') as f:
                        main_content = f.read()
                    
                    st.download_button(
                        label=f"📥 Download {export_format.upper()} Export",
                        data=main_content,
                        file_name=result['main_filename'],
                        mime=f"text/{export_format}",
                        type="primary"
                    )
                
                with col2:
                    # Read manifest
                    manifest_path = Path(result['manifest_file'])
                    with open(manifest_path, 'rb') as f:
                        manifest_content = f.read()
                    
                    st.download_button(
                        label="📥 Download Manifest",
                        data=manifest_content,
                        file_name=result['manifest_filename'],
                        mime="application/json"
                    )
                
                st.balloons()
                
            except Exception as e:
                st.error(f"Error generating export: {str(e)}")
                st.exception(e)
    else:
        st.warning("No conversations match the specified filters. Adjust filters or import data first.")
        
except Exception as e:
    st.error(f"Error previewing export: {str(e)}")
    st.info("Make sure you have imported data first using the Import Data page.")

st.markdown("---")

# Export history section
st.markdown("### Export History")

try:
    export_history = get_export_history()
    
    if export_history:
        st.markdown(f"**{len(export_history)}** exports available")
        
        for i, export in enumerate(export_history):
            with st.expander(f"📦 {export['manifest_file']} - {export['generated_at']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Generated:** {export['generated_at']}")
                    st.write(f"**Records:** {export['row_count']}")
                    st.write(f"**Files:**")
                    for filename in export['files']:
                        st.write(f"  - {filename}")
                
                with col2:
                    # Verify export button
                    if st.button(f"🔍 Verify", key=f"verify_{i}"):
                        manifest_path = EXPORT_DIR / export['manifest_file']
                        
                        with st.spinner("Verifying export..."):
                            verification = verify_export(manifest_path)
                        
                        if verification['valid']:
                            st.success("✅ Export verified successfully")
                        else:
                            st.error("❌ Verification failed")
                            for error in verification['errors']:
                                st.write(f"- {error}")
                            for warning in verification['warnings']:
                                st.warning(f"- {warning}")
                
                # Download buttons for historical exports
                st.markdown("**Download:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Download main file
                    for filename in export['files']:
                        file_path = EXPORT_DIR / filename
                        if file_path.exists():
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                            
                            st.download_button(
                                label=f"📥 {filename}",
                                data=file_content,
                                file_name=filename,
                                mime="text/csv" if filename.endswith('.csv') else "application/json",
                                key=f"download_main_{i}"
                            )
                
                with col2:
                    # Download manifest
                    manifest_path = EXPORT_DIR / export['manifest_file']
                    if manifest_path.exists():
                        with open(manifest_path, 'rb') as f:
                            manifest_content = f.read()
                        
                        st.download_button(
                            label=f"📥 {export['manifest_file']}",
                            data=manifest_content,
                            file_name=export['manifest_file'],
                            mime="application/json",
                            key=f"download_manifest_{i}"
                        )
    else:
        st.info("No exports generated yet. Create your first export above.")
        
except Exception as e:
    st.error(f"Error loading export history: {str(e)}")
    st.exception(e)

# Manifest information section
st.markdown("---")
st.markdown("### About Manifests")

with st.expander("ℹ️ What is an Export Manifest?"):
    st.markdown("""
    An export manifest is a JSON file that provides complete traceability and verification for exported data.
    
    **Manifest Contents:**
    - **Metadata**: Timestamp, generator version, export type
    - **File Information**: Filename, format, row count, file size
    - **Checksums**: SHA256 hash for integrity verification
    - **Data Summary**: Database totals, filters applied, override status
    - **Schema**: Field definitions and data dictionary
    - **Verification**: Automated validation results
    
    **Use the manifest to:**
    1. Verify that exported files haven't been tampered with
    2. Understand exactly what data was exported and when
    3. Document filters and transformations applied
    4. Ensure row counts and checksums match expectations
    5. Provide audit trail for compliance requirements
    
    **Verification Process:**
    The verify function checks:
    - ✅ All listed files exist
    - ✅ Row counts match expected values
    - ✅ File checksums match recorded hashes
    - ✅ No data corruption occurred
    """)

# Cleanup section
st.markdown("---")
with st.expander("🗑️ Cleanup Old Exports"):
    st.warning("⚠️ This will permanently delete old export files. Only the 10 most recent exports will be kept.")
    
    if st.button("Clean Up Old Exports", type="secondary"):
        try:
            from src.exports import cleanup_old_exports
            cleanup_old_exports(keep_count=10)
            st.success("✅ Old exports cleaned up successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Error cleaning up exports: {str(e)}")
