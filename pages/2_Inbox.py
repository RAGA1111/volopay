"""
Conversation Inbox Page

Searchable, filterable conversation queue with detail view and manual corrections.
"""

import streamlit as st
import pandas as pd
from src.database import get_all_conversations, get_conversation_by_id
from src.corrections import apply_manual_override, get_override_history, EDITABLE_FIELDS

st.set_page_config(page_title="Inbox - Revenue Intelligence Inbox", page_icon="📥", layout="wide")

st.title("📥 Conversation Inbox")
st.markdown("### Prioritized work queue with detail view")

# Filters
with st.expander("🔍 Search & Filters", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search", placeholder="Search account, contact, topic...")
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low", "needs_review"])
    with col3:
        category_filter = st.selectbox("Category", 
            ["All", "buying_signal", "objection_blocker", "customer_risk", "product_feedback", "routine", "needs_review"]
        )
    
    col4, col5 = st.columns(2)
    with col4:
        owner_filter = st.text_input("Owner", placeholder="Filter by owner")
    with col5:
        status_filter = st.selectbox("Status", ["All", "pending", "completed"])

# Build filters dict
filters = {}
if search_term:
    filters['search'] = search_term
if priority_filter != "All":
    filters['priority'] = priority_filter
if category_filter != "All":
    filters['category'] = category_filter
if owner_filter:
    filters['owner'] = owner_filter
if status_filter != "All":
    filters['status'] = status_filter

# Get conversations
try:
    df = get_all_conversations(filters if filters else None)
    
    if df.empty:
        st.info("No conversations found matching your filters.")
    else:
        # Summary
        st.markdown(f"**{len(df)}** conversations found")
        
        # Display table
        display_columns = ['source_id', 'conversation_date', 'owner', 'account_name', 
                          'category', 'priority', 'conversation_type']
        
        # Filter to only existing columns
        available_cols = [col for col in display_columns if col in df.columns]
        
        display_df = df[available_cols].copy()
        
        # Rename for better display
        column_rename = {
            'source_id': 'ID',
            'conversation_date': 'Date',
            'owner': 'Owner',
            'account_name': 'Account',
            'category': 'Category',
            'priority': 'Priority',
            'conversation_type': 'Type'
        }
        display_df = display_df.rename(columns=column_rename)
        
        # Color code priorities
        def highlight_priority(row):
            if 'Priority' in row:
                if row['Priority'] == 'high':
                    return ['background-color: #FFE6E6'] * len(row)
                elif row['Priority'] == 'medium':
                    return ['background-color: #FFF4E6'] * len(row)
                elif row['Priority'] == 'needs_review':
                    return ['background-color: #F0F0F0'] * len(row)
            return [''] * len(row)
        
        # Show styled table
        st.dataframe(
            display_df.style.apply(highlight_priority, axis=1),
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Conversation detail
        st.markdown("---")
        st.markdown("### Conversation Detail")
        
        # Select conversation
        conversation_ids = df['id'].tolist()
        source_ids = df['source_id'].tolist()
        
        selected_idx = st.selectbox(
            "Select conversation to view details",
            range(len(conversation_ids)),
            format_func=lambda i: f"{source_ids[i]} - {df.iloc[i]['account_name'] if 'account_name' in df.columns else 'N/A'}"
        )
        
        if selected_idx is not None:
            conversation_id = conversation_ids[selected_idx]
            conversation = get_conversation_by_id(conversation_id)
            
            if conversation:
                # Display conversation details
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### Conversation Info")
                    
                    info_col1, info_col2 = st.columns(2)
                    with info_col1:
                        st.write(f"**Source ID:** {conversation.get('source_id', 'N/A')}")
                        st.write(f"**Date:** {conversation.get('conversation_date', 'N/A')}")
                        st.write(f"**Type:** {conversation.get('conversation_type', 'N/A')}")
                    with info_col2:
                        st.write(f"**Owner:** {conversation.get('owner', 'N/A')}")
                        st.write(f"**Account:** {conversation.get('account_name', 'N/A')}")
                        st.write(f"**Contact:** {conversation.get('contact_name', 'N/A')}")
                    
                    if conversation.get('topic'):
                        st.markdown("**Topic:**")
                        st.info(conversation['topic'])
                    
                    if conversation.get('notes'):
                        st.markdown("**Notes:**")
                        st.text_area("", conversation['notes'], height=150, disabled=True, key="notes_display")
                    
                    if conversation.get('transcript'):
                        st.markdown("**Transcript:**")
                        with st.expander("View transcript"):
                            st.text_area("", conversation['transcript'], height=200, disabled=True, key="transcript_display")
                
                with col2:
                    st.markdown("#### Analysis Results")
                    
                    # Priority badge
                    priority = conversation.get('priority', 'unknown')
                    if priority == 'high':
                        st.error(f"🔴 Priority: **{priority.upper()}**")
                    elif priority == 'medium':
                        st.warning(f"🟡 Priority: **{priority.upper()}**")
                    elif priority == 'low':
                        st.info(f"🔵 Priority: **{priority.upper()}**")
                    else:
                        st.write(f"⚪ Priority: **{priority}**")
                    
                    st.write(f"**Category:** {conversation.get('category', 'N/A')}")
                    st.write(f"**Review Status:** {conversation.get('review_status', 'N/A')}")
                    
                    st.markdown("**Rationale:**")
                    st.caption(conversation.get('rationale', 'N/A'))
                    
                    st.markdown("**Evidence:**")
                    st.caption(conversation.get('evidence', 'N/A'))
                    
                    st.markdown("**Next Action:**")
                    st.success(conversation.get('next_action', 'N/A'))
                    
                    # Show overrides if any
                    if conversation.get('overrides'):
                        st.markdown("**Active Overrides:**")
                        for override in conversation['overrides']:
                            st.caption(f"• {override['field_name']}: {override['override_value']}")
                
                # Manual correction section
                st.markdown("---")
                st.markdown("### Manual Correction")
                
                with st.expander("✏️ Edit Classification"):
                    st.info("Override automated classification. Changes are preserved across re-imports.")
                    
                    edit_col1, edit_col2 = st.columns(2)
                    
                    with edit_col1:
                        field_to_edit = st.selectbox("Field to override", EDITABLE_FIELDS)
                    
                    with edit_col2:
                        current_value = conversation.get(field_to_edit, '')
                        
                        # Field-specific inputs
                        if field_to_edit == 'category':
                            new_value = st.selectbox("New value", 
                                ["buying_signal", "objection_blocker", "customer_risk", 
                                 "product_feedback", "routine", "needs_review"],
                                index=0 if not current_value else None
                            )
                        elif field_to_edit == 'priority':
                            new_value = st.selectbox("New value", ["high", "medium", "low", "needs_review"])
                        elif field_to_edit == 'review_status':
                            new_value = st.selectbox("New value", ["pending", "completed"])
                        else:
                            new_value = st.text_input("New value", value=current_value)
                    
                    reason = st.text_area("Reason for override", placeholder="Explain why this change is needed...")
                    
                    if st.button("Apply Override", type="primary"):
                        if not reason:
                            st.error("Please provide a reason for the override")
                        else:
                            try:
                                apply_manual_override(conversation_id, field_to_edit, new_value, reason)
                                st.success(f"Override applied successfully to {field_to_edit}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error applying override: {str(e)}")
                
                # Override history
                with st.expander("📜 Override History"):
                    history = get_override_history(conversation_id)
                    if history:
                        for item in history:
                            status = "✅ Active" if item['active'] else "⏳ Superseded"
                            st.caption(f"{status} | {item['timestamp']}")
                            st.write(f"**{item['field_name']}**: {item['source_value']} → {item['override_value']}")
                            st.write(f"*Reason: {item['reason']}*")
                            st.markdown("---")
                    else:
                        st.info("No override history for this conversation")

except Exception as e:
    st.error(f"Error loading inbox: {str(e)}")
    st.info("Make sure you have imported data first using the Import Data page.")

# Refresh button
if st.button("🔄 Refresh Inbox"):
    st.rerun()
