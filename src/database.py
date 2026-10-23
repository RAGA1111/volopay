"""
Database layer for Revenue Intelligence Inbox

Handles SQLite persistence for conversations, analysis, overrides, imports, and audit trail.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd

# Database file location
DB_PATH = Path(__file__).parent.parent / "revenue_intelligence.db"


def get_connection():
    """Get a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all required tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conversations table - canonical conversation records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT UNIQUE,
            source_type TEXT,
            source_hash TEXT,
            source_payload TEXT,
            
            -- Normalized fields from source
            conversation_date TEXT,
            conversation_type TEXT,
            owner TEXT,
            account_name TEXT,
            contact_name TEXT,
            duration_minutes INTEGER,
            topic TEXT,
            transcript TEXT,
            notes TEXT,
            status TEXT,
            
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            source_updated_at TEXT
        )
    """)
    
    # Analysis results table - routing and priority assignments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            category TEXT,
            priority TEXT,
            rationale TEXT,
            evidence TEXT,
            next_action TEXT,
            review_status TEXT DEFAULT 'pending',
            rule_version TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    
    # Manual overrides table - user corrections with audit trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            override_value TEXT,
            source_value_at_override TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    
    # Import batches table - track all import operations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            total_rows INTEGER,
            new_count INTEGER DEFAULT 0,
            unchanged_count INTEGER DEFAULT 0,
            updated_count INTEGER DEFAULT 0,
            duplicate_count INTEGER DEFAULT 0,
            invalid_count INTEGER DEFAULT 0,
            conflict_count INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)
    
    # Audit log table - comprehensive change tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            action TEXT NOT NULL,
            field_name TEXT,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            timestamp TEXT NOT NULL,
            batch_id INTEGER,
            FOREIGN KEY (batch_id) REFERENCES import_batches(id)
        )
    """)
    
    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_source_id ON conversations(source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_date ON conversations(conversation_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_owner ON conversations(owner)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_conversation ON analysis_results(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_priority ON analysis_results(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_category ON analysis_results(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_overrides_conversation ON manual_overrides(conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_overrides_active ON manual_overrides(active)")
    
    conn.commit()
    conn.close()


def log_audit_entry(entity_type: str, entity_id: Optional[int], action: str, 
                   field_name: Optional[str] = None, old_value: Optional[str] = None,
                   new_value: Optional[str] = None, reason: Optional[str] = None,
                   batch_id: Optional[int] = None):
    """Log an audit trail entry."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO audit_log 
        (entity_type, entity_id, action, field_name, old_value, new_value, reason, timestamp, batch_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (entity_type, entity_id, action, field_name, old_value, new_value, reason, 
          datetime.utcnow().isoformat(), batch_id))
    
    conn.commit()
    conn.close()


def get_all_conversations(filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Retrieve all conversations with their analysis results and active overrides.
    
    Args:
        filters: Optional dict with filter criteria (priority, category, owner, etc.)
    
    Returns:
        DataFrame with conversation and analysis data
    """
    conn = get_connection()
    
    query = """
        SELECT 
            c.*,
            a.category,
            a.priority,
            a.rationale,
            a.evidence,
            a.next_action,
            a.review_status
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        WHERE 1=1
    """
    
    params = []
    
    if filters:
        if filters.get('priority'):
            query += " AND a.priority = ?"
            params.append(filters['priority'])
        
        if filters.get('category'):
            query += " AND a.category = ?"
            params.append(filters['category'])
        
        if filters.get('owner'):
            query += " AND c.owner = ?"
            params.append(filters['owner'])
        
        if filters.get('status'):
            query += " AND c.status = ?"
            params.append(filters['status'])
        
        if filters.get('search'):
            query += """ AND (
                c.account_name LIKE ? OR 
                c.contact_name LIKE ? OR 
                c.topic LIKE ? OR
                c.notes LIKE ?
            )"""
            search_term = f"%{filters['search']}%"
            params.extend([search_term] * 4)
    
    query += " ORDER BY c.conversation_date DESC"
    
    df = pd.read_sql_query(query, conn, params=params if params else None)
    conn.close()
    
    return df


def get_conversation_by_id(conversation_id: int) -> Optional[Dict[str, Any]]:
    """Get a single conversation with all related data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get conversation and analysis
    cursor.execute("""
        SELECT 
            c.*,
            a.category,
            a.priority,
            a.rationale,
            a.evidence,
            a.next_action,
            a.review_status,
            a.rule_version
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        WHERE c.id = ?
    """, (conversation_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    result = dict(row)
    
    # Get active overrides
    cursor.execute("""
        SELECT field_name, override_value, reason, timestamp
        FROM manual_overrides
        WHERE conversation_id = ? AND active = 1
        ORDER BY timestamp DESC
    """, (conversation_id,))
    
    result['overrides'] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return result


def get_dashboard_metrics(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Calculate dashboard metrics from current data."""
    conn = get_connection()
    
    # Build WHERE clause for filters
    where_clause = "WHERE 1=1"
    params = []
    
    if filters:
        if filters.get('owner'):
            where_clause += " AND c.owner = ?"
            params.append(filters['owner'])
        if filters.get('date_from'):
            where_clause += " AND c.conversation_date >= ?"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            where_clause += " AND c.conversation_date <= ?"
            params.append(filters['date_to'])
    
    # Unique conversations
    query = f"SELECT COUNT(DISTINCT c.id) as count FROM conversations c {where_clause}"
    unique_conversations = pd.read_sql_query(query, conn, params=params if params else None).iloc[0]['count']
    
    # Activity by type
    query = f"""
        SELECT conversation_type, COUNT(*) as count 
        FROM conversations c 
        {where_clause} AND conversation_type IS NOT NULL
        GROUP BY conversation_type
    """
    activity_by_type = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Priority distribution
    query = f"""
        SELECT a.priority, COUNT(*) as count
        FROM conversations c
        LEFT JOIN analysis_results a ON c.id = a.conversation_id
        {where_clause}
        GROUP BY a.priority
    """
    priority_dist = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Activity by owner
    query = f"""
        SELECT owner, COUNT(*) as count
        FROM conversations c
        {where_clause} AND owner IS NOT NULL
        GROUP BY owner
    """
    activity_by_owner = pd.read_sql_query(query, conn, params=params if params else None)
    
    # Recent import stats
    query = """
        SELECT * FROM import_batches 
        ORDER BY timestamp DESC 
        LIMIT 5
    """
    recent_imports = pd.read_sql_query(query, conn)
    
    conn.close()
    
    return {
        'unique_conversations': unique_conversations,
        'activity_by_type': activity_by_type,
        'priority_distribution': priority_dist,
        'activity_by_owner': activity_by_owner,
        'recent_imports': recent_imports
    }


def get_import_history() -> pd.DataFrame:
    """Get all import batch records."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM import_batches 
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
    return df
