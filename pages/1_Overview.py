"""
Overview Dashboard Page

Displays key metrics and activity visualizations.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.database import get_dashboard_metrics
from src.metrics import calculate_overview_metrics, calculate_import_health, format_metric

st.set_page_config(page_title="Overview - Revenue Intelligence Inbox", page_icon="📊", layout="wide")

st.title("📊 Overview Dashboard")
st.markdown("### Activity metrics and conversation insights")

# Filters (optional)
with st.expander("🔍 Filters", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        owner_filter = st.text_input("Owner", placeholder="Filter by owner")
    with col2:
        date_from = st.date_input("Date From", value=None)
    with col3:
        date_to = st.date_input("Date To", value=None)

# Build filter dict
filters = {}
if owner_filter:
    filters['owner'] = owner_filter
if date_from:
    filters['date_from'] = date_from.strftime('%Y-%m-%d')
if date_to:
    filters['date_to'] = date_to.strftime('%Y-%m-%d')

# Calculate metrics
try:
    metrics = calculate_overview_metrics(filters if filters else None)
    
    # Top-level KPIs
    st.markdown("### Key Metrics")
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "Total Conversations",
            format_metric(metrics['unique_conversations']),
            help="Unique conversations after deduplication"
        )
    
    with cols[1]:
        high_priority = metrics['priority_distribution']
        high_count = high_priority[high_priority['priority'] == 'high']['count'].sum() if not high_priority.empty else 0
        st.metric(
            "High Priority",
            format_metric(high_count),
            help="Conversations requiring immediate attention"
        )
    
    with cols[2]:
        needs_review = metrics['priority_distribution']
        review_count = needs_review[needs_review['priority'] == 'needs_review']['count'].sum() if not needs_review.empty else 0
        st.metric(
            "Needs Review",
            format_metric(review_count),
            help="Conversations requiring manual classification"
        )
    
    with cols[3]:
        owner_count = len(metrics['activity_by_owner']) if not metrics['activity_by_owner'].empty else 0
        st.metric(
            "Active Owners",
            format_metric(owner_count),
            help="Unique sales owners with conversations"
        )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Priority Distribution")
        if not metrics['priority_distribution'].empty:
            priority_df = metrics['priority_distribution']
            
            # Create color map
            color_map = {
                'high': '#FF4B4B',
                'medium': '#FFA500',
                'low': '#4B8BFF',
                'needs_review': '#808080'
            }
            
            fig = px.pie(
                priority_df,
                values='count',
                names='priority',
                color='priority',
                color_discrete_map=color_map,
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available")
    
    with col2:
        st.markdown("#### Activity by Type")
        if not metrics['activity_by_type'].empty:
            type_df = metrics['activity_by_type']
            
            fig = px.bar(
                type_df,
                x='conversation_type',
                y='count',
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=350,
                xaxis_title="Type",
                yaxis_title="Count",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No conversation type data available")
    
    # Category distribution
    st.markdown("#### Category Distribution")
    if not metrics['category_distribution'].empty:
        cat_df = metrics['category_distribution']
        
        fig = px.bar(
            cat_df,
            x='category',
            y='count',
            color='count',
            color_continuous_scale='Viridis',
            text='count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(
            height=350,
            xaxis_title="Category",
            yaxis_title="Count",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No category data available")
    
    # Activity by owner and over time
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Top Owners by Activity")
        if not metrics['activity_by_owner'].empty:
            owner_df = metrics['activity_by_owner'].head(10)
            
            fig = px.bar(
                owner_df,
                y='owner',
                x='count',
                orientation='h',
                color='count',
                color_continuous_scale='Greens'
            )
            fig.update_layout(
                height=400,
                xaxis_title="Conversations",
                yaxis_title="Owner",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No owner data available")
    
    with col2:
        st.markdown("#### Activity Over Time (Last 30 Days)")
        if not metrics['activity_over_time'].empty:
            time_df = metrics['activity_over_time'].sort_values('date')
            
            fig = px.line(
                time_df,
                x='date',
                y='count',
                markers=True
            )
            fig.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title="Conversations",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No date data available")
    
    # Import health section
    st.markdown("---")
    st.markdown("### Import Health")
    
    import_health = calculate_import_health()
    
    if not import_health['recent_imports'].empty:
        recent_imports = import_health['recent_imports'].head(5)
        
        # Show summary stats
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Batches", format_metric(import_health['total_batches']))
        with cols[1]:
            st.metric("Rows Processed", format_metric(import_health['total_rows_processed']))
        with cols[2]:
            st.metric("Invalid Rows", format_metric(import_health['total_invalid_rows']))
        with cols[3]:
            if 'last_import' in import_health:
                st.metric("Last Import", import_health['last_import']['filename'][:20] + "...")
        
        # Recent imports table
        st.markdown("#### Recent Imports")
        display_df = recent_imports[['filename', 'timestamp', 'status', 'total_rows', 
                                     'new_count', 'updated_count', 'duplicate_count', 'invalid_count']]
        display_df.columns = ['File', 'Time', 'Status', 'Total', 'New', 'Updated', 'Duplicate', 'Invalid']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No import history available. Upload data using the Import Data page.")

except Exception as e:
    st.error(f"Error loading metrics: {str(e)}")
    st.info("Make sure you have imported data first using the Import Data page.")

# Refresh button
if st.button("🔄 Refresh Dashboard", type="primary"):
    st.rerun()
