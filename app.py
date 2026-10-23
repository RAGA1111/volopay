"""
Revenue Intelligence Inbox - Main Application Entry Point

A lightweight revenue-intelligence workbench for sales managers and growth associates.
Converts sales call and meeting records into a prioritized work queue.
"""

import streamlit as st
from src.database import initialize_database

# Page configuration
st.set_page_config(
    page_title="Revenue Intelligence Inbox",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on app startup
initialize_database()

# Welcome page content
st.title("📊 Revenue Intelligence Inbox")
st.markdown("### Lightweight Revenue Intelligence Workbench")

st.markdown("""
Welcome to the Revenue Intelligence Inbox - a tool that transforms sales call and meeting records 
into a prioritized, actionable work queue.

#### What This Tool Does

- **📥 Smart Imports**: Upload CSV or JSON files with automatic duplicate detection and reconciliation
- **🎯 Intelligent Routing**: Categorize conversations with explainable priorities and evidence
- **📊 Clear Dashboard**: View activity metrics and follow-up priorities at a glance
- **✏️ Manual Corrections**: Override classifications with full audit trail
- **📤 Clean Exports**: Generate verified exports with manifest validation

#### Getting Started

1. **Import Data** - Use the Import Data page to upload your conversation records
2. **Review Dashboard** - Check the Overview for activity metrics and priorities
3. **Process Inbox** - Review and action conversations in priority order
4. **Export Results** - Generate reports with full traceability

#### Navigation

Use the sidebar to access:
- **Overview** - Dashboard with key metrics and activity visualization
- **Inbox** - Searchable conversation queue with detail view
- **Import Data** - Upload and reconcile data files
- **Exports** - Generate and download analysis results

---

**Note**: This is a lean MVP focused on reliable imports, explainable routing, and data integrity. 
All routing decisions show source evidence and reasoning.
""")

# System status
st.sidebar.title("System Info")
st.sidebar.info("""
**Version**: 1.0.0  
**Status**: Ready  
**Data Store**: SQLite
""")
